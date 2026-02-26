from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from src.models import db, Lancamento, Entidade, FluxoContaModel, ContaBanco
from datetime import datetime, date
from src.services.fluxo_consolidado import consolidar_fluxo_caixa

lancamentos_bp = Blueprint('lancamentos', __name__, url_prefix='/lancamentos')


@lancamentos_bp.route('/')
@login_required
def index():
    """List all lancamentos"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    tipo = request.args.get('tipo', '')  # P para Pagamento, R para Recebimento
    
    query = Lancamento.query
    
    if status:
        query = query.filter_by(status=status)
    
    if tipo:
        query = query.join(FluxoContaModel).filter(FluxoContaModel.tipo == tipo)
    
    pagination = query.order_by(Lancamento.data_vencimento.desc()).paginate(page=page, per_page=20)
    lancamentos = pagination.items
    
    return render_template(
        'lancamentos/index.html',
        lancamentos=lancamentos,
        pagination=pagination,
        status=status,
        tipo=tipo
    )


@lancamentos_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def criar():
    """Create new lancamento"""
    entidades = Entidade.query.filter_by(ativo=True).all()
    contas_fluxo = FluxoContaModel.query.filter_by(ativo=True).all()
    contas_banco = ContaBanco.query.filter_by(ativo=True).all()
    
    if request.method == 'POST':
        try:
            lancamento = Lancamento(
                data_evento=datetime.strptime(request.form.get('data_evento'), '%Y-%m-%d').date(),
                data_vencimento=datetime.strptime(request.form.get('data_vencimento'), '%Y-%m-%d').date(),
                data_pagamento=None,
                status='aberto' if not request.form.get('data_pagamento') else 'pago',
                fluxo_conta_id=request.form.get('fluxo_conta_id', type=int),
                conta_banco_id=request.form.get('conta_banco_id', type=int),
                entidade_id=request.form.get('entidade_id', type=int),
                valor_real=float(request.form.get('valor_real')),
                valor_pago=0.00 if not request.form.get('data_pagamento') else float(request.form.get('valor_real')),
                numero_documento=request.form.get('numero_documento'),
                observacoes=request.form.get('observacoes')
            )
            
            # Se houver data de pagamento, converter
            if request.form.get('data_pagamento'):
                lancamento.data_pagamento = datetime.strptime(request.form.get('data_pagamento'), '%Y-%m-%d').date()
                lancamento.status = 'pago'
                lancamento.valor_pago = float(request.form.get('valor_real'))
            
            db.session.add(lancamento)
            db.session.commit()
            consolidar_fluxo_caixa()
            
            flash(f'Lançamento {lancamento.numero_documento} criado com sucesso', 'success')
            return redirect(url_for('lancamentos.index'))
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao criar lançamento: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao criar lançamento: {str(e)}', 'danger')
    
    return render_template(
        'lancamentos/form.html',
        action='criar',
        entidades=entidades,
        contas_fluxo=contas_fluxo,
        contas_banco=contas_banco
    )


@lancamentos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edit lancamento"""
    lancamento = Lancamento.query.get_or_404(id)
    entidades = Entidade.query.filter_by(ativo=True).all()
    contas_fluxo = FluxoContaModel.query.filter_by(ativo=True).all()
    contas_banco = ContaBanco.query.filter_by(ativo=True).all()
    
    if request.method == 'POST':
        try:
            lancamento.data_evento = datetime.strptime(request.form.get('data_evento'), '%Y-%m-%d').date()
            lancamento.data_vencimento = datetime.strptime(request.form.get('data_vencimento'), '%Y-%m-%d').date()
            lancamento.fluxo_conta_id = request.form.get('fluxo_conta_id', type=int)
            lancamento.conta_banco_id = request.form.get('conta_banco_id', type=int)
            lancamento.entidade_id = request.form.get('entidade_id', type=int)
            lancamento.valor_real = float(request.form.get('valor_real'))
            lancamento.numero_documento = request.form.get('numero_documento')
            lancamento.observacoes = request.form.get('observacoes')
            
            # Handle payment
            if request.form.get('data_pagamento'):
                lancamento.data_pagamento = datetime.strptime(request.form.get('data_pagamento'), '%Y-%m-%d').date()
                lancamento.status = 'pago'
                lancamento.valor_pago = float(request.form.get('valor_pago', lancamento.valor_real))
            else:
                lancamento.data_pagamento = None
                lancamento.valor_pago = 0.00
                lancamento.status = 'aberto'
            
            db.session.commit()
            consolidar_fluxo_caixa()
            
            flash(f'Lançamento {lancamento.numero_documento} atualizado com sucesso', 'success')
            return redirect(url_for('lancamentos.index'))
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao atualizar lançamento: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao atualizar lançamento: {str(e)}', 'danger')
    
    return render_template(
        'lancamentos/form.html',
        action='editar',
        lancamento=lancamento,
        entidades=entidades,
        contas_fluxo=contas_fluxo,
        contas_banco=contas_banco
    )


@lancamentos_bp.route('/<int:id>/pagar', methods=['POST'])
@login_required
def pagar(id):
    """Mark lancamento as paid"""
    lancamento = Lancamento.query.get_or_404(id)
    
    try:
        lancamento.data_pagamento = date.today()
        lancamento.valor_pago = float(lancamento.valor_real)
        lancamento.status = 'pago'
        
        db.session.commit()
        consolidar_fluxo_caixa()
        
        flash(f'Lançamento {lancamento.numero_documento} marcado como pago', 'success')
    except Exception as e:
        import logging, traceback
        db.session.rollback()
        logging.error('Erro ao pagar lançamento: %s\n%s', e, traceback.format_exc())
        flash(f'Erro ao pagar lançamento: {str(e)}', 'danger')
    
    return redirect(url_for('lancamentos.index'))


@lancamentos_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):
    """Delete lancamento"""
    lancamento = Lancamento.query.get_or_404(id)
    
    try:
        db.session.delete(lancamento)
        db.session.commit()
        # Recalcula o consolidado para remover reflexos do lançamento excluído
        from src.services.fluxo_consolidado import consolidar_fluxo_caixa
        consolidar_fluxo_caixa()
        flash(f'Lançamento deletado com sucesso', 'success')
    except Exception as e:
        import logging, traceback
        db.session.rollback()
        logging.error('Erro ao deletar lançamento: %s\n%s', e, traceback.format_exc())
        flash(f'Erro ao deletar lançamento: {str(e)}', 'danger')
    
    return redirect(url_for('lancamentos.index'))
