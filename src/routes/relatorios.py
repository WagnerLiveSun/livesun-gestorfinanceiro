import io
from collections import defaultdict
from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required
from src.models import db, Lancamento, Entidade, ContaBanco, FluxoContaModel
from sqlalchemy import func
from datetime import datetime, date
from decimal import Decimal
from types import SimpleNamespace
from openpyxl import Workbook

relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

@relatorios_bp.route('/fluxo-caixa-previsto')
@login_required
def fluxo_caixa_previsto():
	return render_template('relatorios/fluxo_caixa_previsto.html')

@relatorios_bp.route('/fluxo-caixa-realizado')
@login_required
def fluxo_caixa_realizado():
	return render_template('relatorios/fluxo_caixa_realizado.html')

@relatorios_bp.route('/fluxo-caixa')
@login_required
def fluxo_caixa():
	# Get filters
	data_inicio = request.args.get('data_inicio', '')
	data_fim = request.args.get('data_fim', '')
	conta_banco_id = request.args.get('conta_banco_id', '', type=int)
	conta_fluxo_id = request.args.get('conta_fluxo_id', '', type=int)

	def get_saldo_inicial_por_conta():
		if conta_banco_id:
			contas = ContaBanco.query.filter(ContaBanco.id == conta_banco_id).all()
		else:
			contas = ContaBanco.query.filter_by(ativo=True).all()
		return {c.id: Decimal(str(c.saldo_inicial or 0)) for c in contas}

	def get_saldo_inicial_total():
		return sum(get_saldo_inicial_por_conta().values(), Decimal('0.00'))

	def build_fluxo_rows(lancamentos, saldo_inicial_por_conta, use_valor_real):
		saldo_atual_por_conta = saldo_inicial_por_conta.copy()
		rows = []
		for lancamento in lancamentos:
			conta_id = lancamento.conta_banco_id
			saldo_anterior = saldo_atual_por_conta.get(conta_id, Decimal('0.00'))
			valor_base = lancamento.valor_real if use_valor_real else lancamento.valor_pago
			valor = Decimal(str(valor_base or 0))
			if lancamento.fluxo_conta.tipo == 'P':
				saldo_atual = saldo_anterior - valor
			else:
				saldo_atual = saldo_anterior + valor
			saldo_atual_por_conta[conta_id] = saldo_atual
			rows.append(SimpleNamespace(
				lancamento=lancamento,
				saldo_anterior=saldo_anterior,
				saldo_atual=saldo_atual
			))
		return rows

	def build_daily_rows(lancamentos, saldo_inicial, use_valor_real, date_attr):
		totals = defaultdict(lambda: {'pagar': Decimal('0.00'), 'receber': Decimal('0.00')})
		for lancamento in lancamentos:
			data_ref = getattr(lancamento, date_attr)
			if not data_ref:
				continue
			valor_base = lancamento.valor_real if use_valor_real else lancamento.valor_pago
			valor = Decimal(str(valor_base or 0))
			if lancamento.fluxo_conta.tipo == 'P':
				totals[data_ref]['pagar'] += valor
			else:
				totals[data_ref]['receber'] += valor

		saldo_atual = saldo_inicial
		rows = []
		for data_ref in sorted(totals.keys()):
			pagar = totals[data_ref]['pagar']
			receber = totals[data_ref]['receber']
			saldo_anterior = saldo_atual
			saldo_atual = saldo_anterior + receber - pagar
			rows.append(SimpleNamespace(
				data=data_ref,
				saldo_anterior=saldo_anterior,
				pagamentos=pagar,
				recebimentos=receber,
				saldo_atual=saldo_atual
			))
		return rows

	saldo_inicial_por_conta = get_saldo_inicial_por_conta()
	saldo_inicial_total = get_saldo_inicial_total()

	# Build base queries
	query_realizado = Lancamento.query.filter(Lancamento.status == 'pago')
	if data_inicio:
		data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
		query_realizado = query_realizado.filter(Lancamento.data_pagamento >= data_inicio)
	if data_fim:
		data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
		query_realizado = query_realizado.filter(Lancamento.data_pagamento <= data_fim)
	if conta_banco_id:
		query_realizado = query_realizado.filter(Lancamento.conta_banco_id == conta_banco_id)
	if conta_fluxo_id:
		query_realizado = query_realizado.filter(Lancamento.fluxo_conta_id == conta_fluxo_id)
	lancamentos_realizado = query_realizado.order_by(Lancamento.data_pagamento.asc()).all()

	# Build previsto query
	query_previsto = Lancamento.query
	if data_inicio:
		query_previsto = query_previsto.filter(Lancamento.data_vencimento >= data_inicio)
	if data_fim:
		query_previsto = query_previsto.filter(Lancamento.data_vencimento <= data_fim)
	if conta_banco_id:
		query_previsto = query_previsto.filter(Lancamento.conta_banco_id == conta_banco_id)
	if conta_fluxo_id:
		query_previsto = query_previsto.filter(Lancamento.fluxo_conta_id == conta_fluxo_id)
	lancamentos_previsto = query_previsto.order_by(Lancamento.data_vencimento.asc()).all()

	resumo_diario_realizado = build_daily_rows(
		lancamentos_realizado,
		saldo_inicial_total,
		use_valor_real=False,
		date_attr='data_pagamento'
	)

	resumo_diario_previsto = build_daily_rows(
		lancamentos_previsto,
		saldo_inicial_total,
		use_valor_real=True,
		date_attr='data_vencimento'
	)

	# Get filter options
	contas_banco = ContaBanco.query.filter_by(ativo=True).all()
	contas_fluxo = FluxoContaModel.query.filter_by(ativo=True).all()

	return render_template(
		'relatorios/fluxo_caixa.html',
		lancamentos_realizado=build_fluxo_rows(lancamentos_realizado, saldo_inicial_por_conta, use_valor_real=False),
		lancamentos_previsto=build_fluxo_rows(lancamentos_previsto, saldo_inicial_por_conta, use_valor_real=True),
		resumo_diario_realizado=resumo_diario_realizado,
		resumo_diario_previsto=resumo_diario_previsto,
		contas_banco=contas_banco,
		contas_fluxo=contas_fluxo,
		data_inicio=data_inicio,
		data_fim=data_fim,
		conta_banco_id=conta_banco_id,
		conta_fluxo_id=conta_fluxo_id
	)

@relatorios_bp.route('/fluxo-caixa/export')
@login_required
def export_fluxo_caixa():
	data_inicio = request.args.get('data_inicio', '')
	data_fim = request.args.get('data_fim', '')
	conta_banco_id = request.args.get('conta_banco_id', '', type=int)
	conta_fluxo_id = request.args.get('conta_fluxo_id', '', type=int)

	def get_saldo_inicial_por_conta():
		if conta_banco_id:
			contas = ContaBanco.query.filter(ContaBanco.id == conta_banco_id).all()
		else:
			contas = ContaBanco.query.filter_by(ativo=True).all()
		return {c.id: Decimal(str(c.saldo_inicial or 0)) for c in contas}

	def get_saldo_inicial_total():
		return sum(get_saldo_inicial_por_conta().values(), Decimal('0.00'))

	def build_daily_rows(lancamentos, saldo_inicial, use_valor_real, date_attr):
		totals = defaultdict(lambda: {'pagar': Decimal('0.00'), 'receber': Decimal('0.00')})
		for lancamento in lancamentos:
			data_ref = getattr(lancamento, date_attr)
			if not data_ref:
				continue
			valor_base = lancamento.valor_real if use_valor_real else lancamento.valor_pago
			valor = Decimal(str(valor_base or 0))
			if lancamento.fluxo_conta.tipo == 'P':
				totals[data_ref]['pagar'] += valor
			else:
				totals[data_ref]['receber'] += valor

		saldo_atual = saldo_inicial
		rows = []
		for data_ref in sorted(totals.keys()):
			pagar = totals[data_ref]['pagar']
			receber = totals[data_ref]['receber']
			saldo_anterior = saldo_atual
			saldo_atual = saldo_anterior + receber - pagar
			rows.append((data_ref, saldo_anterior, pagar, receber, saldo_atual))
		return rows

	query_realizado = Lancamento.query.filter(Lancamento.status == 'pago')
	query_previsto = Lancamento.query

	if data_inicio:
		data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
		query_realizado = query_realizado.filter(Lancamento.data_pagamento >= data_inicio)
		query_previsto = query_previsto.filter(Lancamento.data_vencimento >= data_inicio)

	if data_fim:
		data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
		query_realizado = query_realizado.filter(Lancamento.data_pagamento <= data_fim)
		query_previsto = query_previsto.filter(Lancamento.data_vencimento <= data_fim)

	if conta_banco_id:
		query_realizado = query_realizado.filter(Lancamento.conta_banco_id == conta_banco_id)
		query_previsto = query_previsto.filter(Lancamento.conta_banco_id == conta_banco_id)

	if conta_fluxo_id:
		query_realizado = query_realizado.filter(Lancamento.fluxo_conta_id == conta_fluxo_id)
		query_previsto = query_previsto.filter(Lancamento.fluxo_conta_id == conta_fluxo_id)

	lancamentos_realizado = query_realizado.order_by(Lancamento.data_pagamento.asc()).all()
	lancamentos_previsto = query_previsto.order_by(Lancamento.data_vencimento.asc()).all()

	saldo_inicial_total = get_saldo_inicial_total()
	resumo_realizado = build_daily_rows(lancamentos_realizado, saldo_inicial_total, False, 'data_pagamento')
	resumo_previsto = build_daily_rows(lancamentos_previsto, saldo_inicial_total, True, 'data_vencimento')

	wb = Workbook()
	ws_previsto = wb.active
	ws_previsto.title = 'Previsto'
	ws_realizado = wb.create_sheet('Realizado')

	headers = ['Data', 'Saldo Anterior', 'Pagamentos', 'Recebimentos', 'Saldo do Dia']
	ws_previsto.append(headers)
	ws_realizado.append(headers)

	for data_ref, saldo_anterior, pagar, receber, saldo_atual in resumo_previsto:
		ws_previsto.append([data_ref.strftime('%d/%m/%Y'), float(saldo_anterior), float(pagar), float(receber), float(saldo_atual)])

	for data_ref, saldo_anterior, pagar, receber, saldo_atual in resumo_realizado:
		ws_realizado.append([data_ref.strftime('%d/%m/%Y'), float(saldo_anterior), float(pagar), float(receber), float(saldo_atual)])

	for sheet in (ws_previsto, ws_realizado):
		for col in ['B', 'C', 'D', 'E']:
			for cell in sheet[col]:
				cell.number_format = '#,##0.00'
		sheet.column_dimensions['A'].width = 14
		sheet.column_dimensions['B'].width = 18
		sheet.column_dimensions['C'].width = 16
		sheet.column_dimensions['D'].width = 16
		sheet.column_dimensions['E'].width = 18

	output = io.BytesIO()
	wb.save(output)
	output.seek(0)

	return send_file(
		output,
		as_attachment=True,
		download_name='fluxo_caixa_diario.xlsx',
		mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
	)

