from decimal import Decimal
from collections import defaultdict
from src.models import db, Lancamento, FluxoContaModel, ContaBanco, FluxoCaixaRealizado, FluxoCaixaPrevisto
from datetime import datetime

def consolidar_fluxo_caixa():
    # Limpa tabelas consolidadas
    FluxoCaixaRealizado.query.delete()
    FluxoCaixaPrevisto.query.delete()
    db.session.commit()

    contas_fluxo = FluxoContaModel.query.filter_by(ativo=True).all()
    contas_banco = ContaBanco.query.filter_by(ativo=True).all()

    # Realizado
    saldos_realizado = defaultdict(lambda: {
        'saldo_anterior': Decimal('0.00'),
        'valor_pago': Decimal('0.00'),
        'valor_recebido': Decimal('0.00'),
        'saldo_atual': Decimal('0.00'),
        'datas': []
    })
    # Previsto
    saldos_previsto = defaultdict(lambda: {
        'saldo_anterior': Decimal('0.00'),
        'valor_previsto_pago': Decimal('0.00'),
        'valor_previsto_recebido': Decimal('0.00'),
        'saldo_previsto': Decimal('0.00'),
        'datas': []
    })

    for lanc in Lancamento.query.all():
        key = (lanc.fluxo_conta_id, lanc.conta_banco_id)
        if lanc.status == 'pago':
            if lanc.fluxo_conta.tipo == 'P':
                saldos_realizado[key]['valor_pago'] += lanc.valor_pago or Decimal('0.00')
            else:
                saldos_realizado[key]['valor_recebido'] += lanc.valor_pago or Decimal('0.00')
            saldos_realizado[key]['datas'].append(lanc.data_pagamento or lanc.data_evento)
        else:
            if lanc.fluxo_conta.tipo == 'P':
                saldos_previsto[key]['valor_previsto_pago'] += lanc.valor_real or Decimal('0.00')
            else:
                saldos_previsto[key]['valor_previsto_recebido'] += lanc.valor_real or Decimal('0.00')
            saldos_previsto[key]['datas'].append(lanc.data_vencimento or lanc.data_evento)

    # Grava realizado
    for (fluxo_conta_id, conta_banco_id), valores in saldos_realizado.items():
        conta_banco = ContaBanco.query.get(conta_banco_id)
        saldo_anterior = conta_banco.saldo_inicial if conta_banco else Decimal('0.00')
        saldo_atual = saldo_anterior + valores['valor_recebido'] - valores['valor_pago']
        data_consolidado = valores['datas'][-1] if valores['datas'] else datetime.utcnow().date()
        consolidado = FluxoCaixaRealizado(
            data=data_consolidado,
            fluxo_conta_id=fluxo_conta_id,
            conta_banco_id=conta_banco_id,
            saldo_anterior=saldo_anterior,
            valor_pago=valores['valor_pago'],
            valor_recebido=valores['valor_recebido'],
            saldo_atual=saldo_atual
        )
        db.session.add(consolidado)
    # Grava previsto
    for (fluxo_conta_id, conta_banco_id), valores in saldos_previsto.items():
        conta_banco = ContaBanco.query.get(conta_banco_id)
        saldo_anterior = conta_banco.saldo_inicial if conta_banco else Decimal('0.00')
        saldo_previsto = saldo_anterior + valores['valor_previsto_recebido'] - valores['valor_previsto_pago']
        data_consolidado = valores['datas'][-1] if valores['datas'] else datetime.utcnow().date()
        previsto = FluxoCaixaPrevisto(
            data=data_consolidado,
            fluxo_conta_id=fluxo_conta_id,
            conta_banco_id=conta_banco_id,
            saldo_anterior=saldo_anterior,
            valor_previsto_pago=valores['valor_previsto_pago'],
            valor_previsto_recebido=valores['valor_previsto_recebido'],
            saldo_previsto=saldo_previsto
        )
        db.session.add(previsto)
    db.session.commit()

# Para uso: from src.services.fluxo_consolidado import consolidar_fluxo_caixa
# consolidar_fluxo_caixa()