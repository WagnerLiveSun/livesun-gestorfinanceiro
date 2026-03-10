# Imports principais
import io
from collections import defaultdict
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from datetime import datetime
from flask_login import login_required, current_user
from src.models import db, Lancamento, Entidade, ContaBanco, FluxoContaModel
from sqlalchemy import func, or_
from datetime import datetime, date
from decimal import Decimal
from types import SimpleNamespace
import logging
try:
	from openpyxl import Workbook
except Exception:
	Workbook = None
	logging.getLogger(__name__).warning("openpyxl not available; Excel exports disabled", exc_info=True)


# Definição do blueprint deve vir logo após os imports principais
relatorios_bp = Blueprint('relatorios', __name__, url_prefix='/relatorios')

# --- EXPORTAÇÃO BALANCETE (NOVO ENDPOINT PADRÃO) ---
@relatorios_bp.route('/exportar/balancete', methods=['GET'])
@login_required
def export_balancete():
	from src.balancete_financeiro import montar_balancete_financeiro
	formato = request.args.get('formato', 'xlsx')
	empresa_nome = '-'
	empresa_cnpj = '-'
	from src.models import Empresa
	empresa_id = getattr(current_user, 'empresa_id', None)
	if empresa_id:
		empresa = Empresa.query.get(empresa_id)
		if empresa:
			empresa_nome = empresa.nome or '-'
			empresa_cnpj = empresa.cnpj or '-'
	data_ini = request.args.get('data_ini', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
	data_fim = request.args.get('data_fim', datetime.now().strftime('%Y-%m-%d'))
	conta = request.args.get('conta', '')
	entidade = request.args.get('entidade', '')
	status = request.args.get('status', '')

	# Unifica lógica de filtro igual à tela
	contas_query = FluxoContaModel.query.filter_by(empresa_id=current_user.empresa_id, ativo=True)
	contas = contas_query.order_by(FluxoContaModel.codigo.asc()).all()
	conta_ini = request.args.get('conta_ini', '')
	conta_fim = request.args.get('conta_fim', '')
	if conta_ini or conta_fim:
		def in_intervalo(codigo):
			if conta_ini and codigo < conta_ini:
				return False
			if conta_fim and codigo > conta_fim:
				return False
			return True
		contas_filtradas = [c for c in contas if in_intervalo(c.codigo)]
	else:
		contas_filtradas = contas
	lanc_query = Lancamento.query.filter_by(empresa_id=current_user.empresa_id)
	if data_ini:
		lanc_query = lanc_query.filter(Lancamento.data_evento >= data_ini)
	if data_fim:
		lanc_query = lanc_query.filter(Lancamento.data_evento <= data_fim)
	if conta_ini or conta_fim:
		contas_ids = [c.id for c in contas_filtradas]
		lanc_query = lanc_query.filter(Lancamento.fluxo_conta_id.in_(contas_ids))
	if entidade:
		lanc_query = lanc_query.filter(Lancamento.entidade_id == int(entidade))
	if status:
		lanc_query = lanc_query.filter(Lancamento.status == status)
	lancamentos_filtrados = lanc_query.order_by(Lancamento.data_evento.asc()).all()
	from src.balancete_financeiro import montar_balancete_estruturado
	linhas_estruturadas, total = montar_balancete_estruturado(
		contas_models=contas_filtradas,
		lancamentos_models=lancamentos_filtrados,
		usar_valor_pago=True,
		incluir_zeradas=False
	)
	gerado_em = datetime.now().strftime('%d/%m/%Y %H:%M')

	if formato == 'xlsx':
		try:
			from openpyxl import Workbook
		except ImportError:
			flash('Exportação para Excel indisponível.', 'warning')
			return redirect(url_for('relatorios.balancete_financeiro'))
		# Usa as variáveis já filtradas e montadas acima
		wb = Workbook()
		ws = wb.active
		ws.title = 'Balancete Financeiro'
		ws.append(['Empresa', empresa_nome])
		ws.append(['CNPJ', empresa_cnpj])
		ws.append(['Período', f'{data_ini} a {data_fim}'])
		ws.append(['Gerado em', gerado_em])
		ws.append([])
		ws.append(['Código', 'Conta', 'Valor'])
		for linha in linhas_estruturadas:
			indent = '  ' * linha['nivel']
			ws.append([linha['codigo'], f"{indent}{linha['descricao']}", f"R$ {linha['valor']:,.2f}"])
		ws.append([])
		ws.append(['TOTAL', '', f"R$ {total:,.2f}"])
		output = io.BytesIO()
		wb.save(output)
		output.seek(0)
		return send_file(output, download_name=f'balancete_{data_ini}_{data_fim}.xlsx', as_attachment=True)
	elif formato == 'pdf':
		try:
			from fpdf import FPDF
		except ImportError:
			flash('Exportação para PDF indisponível.', 'warning')
			return redirect(url_for('relatorios.balancete_financeiro'))
		pdf = FPDF()
		pdf.add_page()
		pdf.set_font('Arial', 'B', 12)
		pdf.set_text_color(0, 0, 0)
		pdf.cell(0, 10, f'Empresa: {empresa_nome}', ln=1)
		pdf.cell(0, 10, f'CNPJ: {empresa_cnpj}', ln=1)
		pdf.cell(0, 10, f'Período: {data_ini} a {data_fim}', ln=1)
		pdf.cell(0, 10, f'Gerado em: {gerado_em}', ln=1)
		pdf.ln(5)
		pdf.set_font('Arial', 'B', 11)
		pdf.cell(35, 8, 'Código', 1)
		pdf.cell(100, 8, 'Conta', 1)
		pdf.cell(40, 8, 'Valor', 1, ln=1)
		pdf.set_font('Arial', '', 10)
		for linha in linhas_estruturadas:
			indent = '  ' * linha['nivel']
			pdf.cell(35, 7, str(linha['codigo']), 1)
			pdf.cell(100, 7, f"{indent}{linha['descricao']}", 1)
			pdf.cell(40, 7, f"R$ {linha['valor']:,.2f}", 1, ln=1)
		pdf.set_font('Arial', 'B', 11)
		pdf.cell(135, 8, 'TOTAL', 1)
		pdf.cell(40, 8, f"R$ {total:,.2f}", 1, ln=1)
		output = io.BytesIO()
		pdf_bytes = pdf.output(dest='S').encode('latin1')
		output.write(pdf_bytes)
		output.seek(0)
		return send_file(output, download_name=f'balancete_{data_ini}_{data_fim}.pdf', as_attachment=True, mimetype='application/pdf')
	else:
		flash('Formato de exportação inválido.', 'danger')
		return redirect(url_for('relatorios.balancete_financeiro'))

import io
from collections import defaultdict
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from datetime import datetime
from flask_login import login_required, current_user
from src.models import db, Lancamento, Entidade, ContaBanco, FluxoContaModel
from sqlalchemy import func, or_
from datetime import datetime, date
from decimal import Decimal
from types import SimpleNamespace
import logging
try:
    from openpyxl import Workbook
except Exception:
    Workbook = None
    logging.getLogger(__name__).warning("openpyxl not available; Excel exports disabled", exc_info=True)



import io
from collections import defaultdict
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from datetime import datetime
from flask_login import login_required, current_user
from src.models import db, Lancamento, Entidade, ContaBanco, FluxoContaModel
from sqlalchemy import func, or_
from datetime import datetime, date
from decimal import Decimal
from types import SimpleNamespace
import logging
try:
	from openpyxl import Workbook
except Exception:
	Workbook = None
	logging.getLogger(__name__).warning("openpyxl not available; Excel exports disabled", exc_info=True)



# --- BALANCETE FINANCEIRO ---
@relatorios_bp.route('/balancete', methods=['GET'])
@login_required
def balancete_financeiro():
	empresa = current_user.empresa if hasattr(current_user, 'empresa') else None
	empresa_nome = empresa.nome if empresa else '-'
	empresa_cnpj = empresa.cnpj if empresa else '-'
	data_ini = request.args.get('data_ini', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
	data_fim = request.args.get('data_fim', datetime.now().strftime('%Y-%m-%d'))
	conta_ini = request.args.get('conta_ini', '')
	conta_fim = request.args.get('conta_fim', '')
	entidade = request.args.get('entidade', '')
	status = request.args.get('status', '')

	# Filtros
	contas = FluxoContaModel.query.filter_by(empresa_id=current_user.empresa_id, ativo=True).order_by(FluxoContaModel.codigo.asc()).all()  # Igual ao fluxo de caixa
	# Para o relatório, aplique o filtro de intervalo se houver
	if conta_ini or conta_fim:
		def in_intervalo(codigo):
			if conta_ini and codigo < conta_ini:
				return False
			if conta_fim and codigo > conta_fim:
				return False
			return True
		contas_filtradas = [c for c in contas if in_intervalo(c.codigo)]
	else:
		contas_filtradas = contas
	entidades_query = Entidade.query.filter_by(empresa_id=current_user.empresa_id, ativo=True)
	entidades = entidades_query.order_by(Entidade.nome.asc()).all()

	lanc_query = Lancamento.query.filter_by(empresa_id=current_user.empresa_id)
	if data_ini:
		lanc_query = lanc_query.filter(Lancamento.data_evento >= data_ini)
	if data_fim:
		lanc_query = lanc_query.filter(Lancamento.data_evento <= data_fim)
	if conta_ini or conta_fim:
		contas_ids = [c.id for c in contas_filtradas]
		lanc_query = lanc_query.filter(Lancamento.fluxo_conta_id.in_(contas_ids))
	if entidade:
		lanc_query = lanc_query.filter(Lancamento.entidade_id == int(entidade))
	if status:
		lanc_query = lanc_query.filter(Lancamento.status == status)
	lancamentos = lanc_query.order_by(Lancamento.data_evento.asc()).all()

	# Nome da entidade para cabeçalho
	entidade_nome = None
	if entidade:
		ent = Entidade.query.filter_by(id=int(entidade), empresa_id=current_user.empresa_id).first()
		entidade_nome = ent.nome if ent else None

	# Geração do relatório
	from src.balancete_financeiro import montar_balancete_estruturado
	linhas_estruturadas, total = montar_balancete_estruturado(
		contas_models=contas_filtradas,
		lancamentos_models=lancamentos,
		usar_valor_pago=True,
		incluir_zeradas=False
	)
	gerado_em = datetime.now().strftime('%d/%m/%Y %H:%M')

	return render_template(
		'relatorios/balancete_financeiro.html',
		linhas_estruturadas=linhas_estruturadas,
		total=total,
		empresa_nome=empresa_nome,
		empresa_cnpj=empresa_cnpj,
		data_ini=data_ini,
		data_fim=data_fim,
		conta_ini=conta_ini,
		conta_fim=conta_fim,
		contas=contas,  # Sempre todas as contas para o filtro
		entidade=entidade,
		entidades=entidades,
		entidade_nome=entidade_nome,
		status=status,
		gerado_em=gerado_em
	)

# Relatório de Fluxo de Caixa CSV
@relatorios_bp.route('/fluxo-caixa-csv')
@login_required
def fluxo_caixa_csv():
	data_inicio = request.args.get('data_inicio', '')
	data_fim = request.args.get('data_fim', '')
	# Filtros básicos
	query = Lancamento.query.filter_by(empresa_id=current_user.empresa_id)
	if data_inicio:
		data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
		query = query.filter(or_(Lancamento.data_pagamento >= data_inicio_dt, Lancamento.data_vencimento >= data_inicio_dt))
	if data_fim:
		data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
		query = query.filter(or_(Lancamento.data_pagamento <= data_fim_dt, Lancamento.data_vencimento <= data_fim_dt))
	# Apenas lançamentos da empresa do usuário
	if hasattr(current_user, 'empresa_id'):
		query = query.filter(Lancamento.empresa_id == current_user.empresa_id)
	lancamentos = query.order_by(Lancamento.data_pagamento.asc()).all()
	dados_csv = []
	for l in lancamentos:
		desc = getattr(l, 'descricao', None)
		if not desc:
			desc = l.observacoes or l.numero_documento or '-'
		# Categoria: mostrar código + descrição da conta (para sínteticas e analíticas)
		categoria = '-'
		if l.fluxo_conta:
			cod = getattr(l.fluxo_conta, 'codigo', None)
			dsc = getattr(l.fluxo_conta, 'descricao', None)
			if cod and dsc:
				categoria = f"{cod} - {dsc}"
			elif dsc:
				categoria = dsc
		# Data preferencial: data_pagamento se existir, senão data_vencimento
		data_display = l.data_pagamento or l.data_vencimento
		dados_csv.append({
			'data': data_display.strftime('%d/%m/%Y') if data_display else '-',
			'descricao': desc,
			'categoria': categoria,
			'conta_banco': l.conta_banco.nome if l.conta_banco else '-',
			'tipo': 'Receita' if l.fluxo_conta and l.fluxo_conta.tipo == 'R' else 'Despesa',
			'valor': l.valor_real or l.valor_pago or 0
		})
	return render_template('relatorios/fluxo_caixa_csv.html', dados_csv=dados_csv, data_inicio=data_inicio, data_fim=data_fim)

# Exportação para Excel do Fluxo de Caixa CSV
@relatorios_bp.route('/fluxo-caixa-csv/export')
@login_required
def export_fluxo_caixa_csv():
	data_inicio = request.args.get('data_inicio', '')
	data_fim = request.args.get('data_fim', '')
	# Se openpyxl não estiver disponível, retornar mensagem amigável
	if Workbook is None:
		flash('Exportação para Excel indisponível: biblioteca "openpyxl" não está instalada no ambiente.', 'warning')
		return redirect(url_for('relatorios.fluxo_caixa'))
	query = Lancamento.query.filter_by(empresa_id=current_user.empresa_id)
	if data_inicio:
		data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
		query = query.filter(or_(Lancamento.data_pagamento >= data_inicio_dt, Lancamento.data_vencimento >= data_inicio_dt))
	if data_fim:
		data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
		query = query.filter(or_(Lancamento.data_pagamento <= data_fim_dt, Lancamento.data_vencimento <= data_fim_dt))
	if hasattr(current_user, 'empresa_id'):
		query = query.filter(Lancamento.empresa_id == current_user.empresa_id)
	lancamentos = query.order_by(func.coalesce(Lancamento.data_pagamento, Lancamento.data_vencimento).asc()).all()
	wb = Workbook()
	ws = wb.active
	ws.title = 'Fluxo de Caixa'
	ws.append(['Data', 'Descrição', 'Categoria', 'Conta Banco', 'Tipo', 'Valor (R$)'])
	for l in lancamentos:
		valor = l.valor_real or l.valor_pago or 0
		valor_brl = f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
		ws.append([
			l.data_pagamento.strftime('%d/%m/%Y') if l.data_pagamento else '-',
			(getattr(l, 'descricao', None) or l.observacoes or l.numero_documento or '-'),
			l.fluxo_conta.descricao if l.fluxo_conta else '-',
			l.conta_banco.nome if l.conta_banco else '-',
			'Receita' if l.fluxo_conta and l.fluxo_conta.tipo == 'R' else 'Despesa',
			valor_brl
		])
	output = io.BytesIO()
	wb.save(output)
	output.seek(0)
	return send_file(output, as_attachment=True, download_name='fluxo_caixa.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

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
			contas = ContaBanco.query.filter(
				ContaBanco.empresa_id == current_user.empresa_id,
				ContaBanco.id == conta_banco_id
			).all()
		else:
			contas = ContaBanco.query.filter_by(empresa_id=current_user.empresa_id, ativo=True).all()
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
			if lancamento.fluxo_conta and lancamento.fluxo_conta.tipo == 'P':
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
			if lancamento.fluxo_conta and lancamento.fluxo_conta.tipo == 'P':
				totals[data_ref]['pagar'] += valor
			else:
				totals[data_ref]['receber'] += valor

		# Aqui você pode montar a lista de linhas diárias, exemplo:
		rows = []
		saldo_anterior = saldo_inicial
		for data in sorted(totals.keys()):
			pagamentos = totals[data]['pagar']
			recebimentos = totals[data]['receber']
			saldo_atual = saldo_anterior - pagamentos + recebimentos
			rows.append(SimpleNamespace(
				data=data,
				saldo_anterior=saldo_anterior,
				pagamentos=pagamentos,
				recebimentos=recebimentos,
				saldo_atual=saldo_atual
			))
			saldo_anterior = saldo_atual
		return rows

	saldo_inicial_por_conta = get_saldo_inicial_por_conta()
	saldo_inicial_total = get_saldo_inicial_total()

	# Build base queries
	query_realizado = Lancamento.query.filter(
		Lancamento.empresa_id == current_user.empresa_id,
		Lancamento.status == 'pago'
	)
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
	query_previsto = Lancamento.query.filter_by(empresa_id=current_user.empresa_id)
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
	contas_banco = ContaBanco.query.filter_by(empresa_id=current_user.empresa_id, ativo=True).all()
	contas_fluxo = FluxoContaModel.query.filter_by(empresa_id=current_user.empresa_id, ativo=True).all()

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
	# Se openpyxl não estiver disponível, retornar mensagem amigável
	if Workbook is None:
		flash('Exportação para Excel indisponível: biblioteca "openpyxl" não está instalada no ambiente.', 'warning')
		return redirect(url_for('relatorios.fluxo_caixa'))

	def get_saldo_inicial_por_conta():
		if conta_banco_id:
			contas = ContaBanco.query.filter(
				ContaBanco.empresa_id == current_user.empresa_id,
				ContaBanco.id == conta_banco_id
			).all()
		else:
			contas = ContaBanco.query.filter_by(empresa_id=current_user.empresa_id, ativo=True).all()
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
			if lancamento.fluxo_conta and lancamento.fluxo_conta.tipo == 'P':
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

	query_realizado = Lancamento.query.filter(
		Lancamento.empresa_id == current_user.empresa_id,
		Lancamento.status == 'pago'
	)
	query_previsto = Lancamento.query.filter_by(empresa_id=current_user.empresa_id)

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

	lancamentos_realizado = query_realizado.order_by(func.coalesce(Lancamento.data_pagamento, Lancamento.data_vencimento).asc()).all()
	lancamentos_previsto = query_previsto.order_by(func.coalesce(Lancamento.data_pagamento, Lancamento.data_vencimento).asc()).all()

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

