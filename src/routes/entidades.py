from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from src.models import db, Entidade
from datetime import datetime
from src.tenant import scoped_query, scoped_get_or_404, tenant_id

entidades_bp = Blueprint('entidades', __name__, url_prefix='/entidades')


@entidades_bp.route('/')
@login_required
def index():
    """List all entities"""
    page = request.args.get('page', 1, type=int)
    tipo = request.args.get('tipo', '')
    busca = request.args.get('busca', '')
    
    query = scoped_query(Entidade)
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    if busca:
        query = query.filter(
            (Entidade.nome.ilike(f'%{busca}%')) |
            (Entidade.cnpj_cpf.ilike(f'%{busca}%')) |
            (Entidade.email.ilike(f'%{busca}%'))
        )
    
    pagination = query.paginate(page=page, per_page=20)
    entidades = pagination.items
    
    return render_template(
        'entidades/index.html',
        entidades=entidades,
        pagination=pagination,
        tipo=tipo,
        busca=busca
    )


@entidades_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def criar():
    """Create new entity"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Sempre inicializar vendedores como lista vazia
    vendedores = []
    
    # Tentar buscar vendedores
    try:
        if current_user and hasattr(current_user, 'empresa_id') and current_user.empresa_id:
            vendedores = scoped_query(Entidade).filter_by(
                tipo='V',
                ativo=True
            ).order_by(Entidade.nome).all()
            logger.info(f'Vendedores encontrados: {len(vendedores)}')
    except Exception as e:
        logger.warning(f'Erro ao buscar vendedores: {e}')
    
    if request.method == 'POST':
        try:
            # Ensure the new entity is associated with the current user's company
            if not hasattr(current_user, 'empresa_id') or not current_user.empresa_id:
                flash('Usuário não está associado a uma empresa.', 'danger')
                return render_template('entidades/form.html', action='criar', vendedores=vendedores)

            entidade = Entidade(
                empresa_id=tenant_id(),
                tipo=request.form.get('tipo'),
                cnpj_cpf=request.form.get('cnpj_cpf'),
                inscricao_estadual=request.form.get('inscricao_estadual'),
                inscricao_municipal=request.form.get('inscricao_municipal'),
                nome=request.form.get('nome'),
                nome_fantasia=request.form.get('nome_fantasia'),
                endereco_rua=request.form.get('endereco_rua'),
                endereco_numero=request.form.get('endereco_numero'),
                endereco_bairro=request.form.get('endereco_bairro'),
                endereco_cidade=request.form.get('endereco_cidade'),
                endereco_uf=request.form.get('endereco_uf'),
                endereco_cep=request.form.get('endereco_cep'),
                telefone=request.form.get('telefone'),
                email=request.form.get('email'),
                contrato_produto=request.form.get('contrato_produto'),
                ativo=request.form.get('ativo') == 'on',
                # Campos de comissão (CLIENTE)
                aliquota_comissao_especifica=request.form.get('aliquota_comissao_especifica') or None,
                percentual_repasse=request.form.get('percentual_repasse') or 0,
                entidade_vendedor_padrao_id=request.form.get('entidade_vendedor_padrao_id') or None
            )
            
            db.session.add(entidade)
            db.session.commit()
            
            flash(f'Entidade {entidade.nome} criada com sucesso', 'success')
            return redirect(url_for('entidades.index'))
        
        except Exception as e:
            import traceback
            logger.error(f'Erro ao criar entidade: {e}')
            logger.error(traceback.format_exc())
            db.session.rollback()
            flash('Erro ao criar entidade. Verifique os dados e tente novamente.', 'danger')
            return render_template('entidades/form.html', action='criar', vendedores=vendedores, entidade=None)
    
    # GET request - just show the form
    logger.info('Renderizando formulário de criação')
    return render_template('entidades/form.html', action='criar', vendedores=vendedores, entidade=None)


@entidades_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edit entity"""
    import logging
    logger = logging.getLogger(__name__)
    
    entidade = scoped_get_or_404(Entidade, id)
    
    # ALWAYS initialize vendedores as empty list
    vendedores = []
    
    # Protected vendedores query
    try:
        if current_user and hasattr(current_user, 'empresa_id') and current_user.empresa_id:
            vendedores = scoped_query(Entidade).filter_by(
                tipo='V',
                ativo=True
            ).order_by(Entidade.nome).all()
            logger.info(f'[EDITAR] Vendedores encontrados: {len(vendedores)}')
    except Exception as e:
        logger.warning(f'[EDITAR] Erro ao buscar vendedores: {e}')
    
    if request.method == 'POST':
        try:
            entidade.tipo = request.form.get('tipo')
            entidade.cnpj_cpf = request.form.get('cnpj_cpf')
            entidade.inscricao_estadual = request.form.get('inscricao_estadual')
            entidade.inscricao_municipal = request.form.get('inscricao_municipal')
            entidade.nome = request.form.get('nome')
            entidade.nome_fantasia = request.form.get('nome_fantasia')
            entidade.endereco_rua = request.form.get('endereco_rua')
            entidade.endereco_numero = request.form.get('endereco_numero')
            entidade.endereco_bairro = request.form.get('endereco_bairro')
            entidade.endereco_cidade = request.form.get('endereco_cidade')
            entidade.endereco_uf = request.form.get('endereco_uf')
            entidade.endereco_cep = request.form.get('endereco_cep')
            entidade.telefone = request.form.get('telefone')
            entidade.email = request.form.get('email')
            entidade.contrato_produto = request.form.get('contrato_produto')
            entidade.ativo = request.form.get('ativo') == 'on'
            
            # Campos de comissão (CLIENTE)
            aliquota = request.form.get('aliquota_comissao_especifica')
            entidade.aliquota_comissao_especifica = aliquota if aliquota else None
            entidade.percentual_repasse = request.form.get('percentual_repasse') or 0
            vendedor_id = request.form.get('entidade_vendedor_padrao_id')
            entidade.entidade_vendedor_padrao_id = vendedor_id if vendedor_id else None
            
            db.session.commit()
            
            flash(f'Entidade {entidade.nome} atualizada com sucesso', 'success')
            return redirect(url_for('entidades.index'))
        
        except Exception as e:
            import traceback
            logger.error(f'[EDITAR] Erro ao atualizar entidade: {e}')
            logger.error(traceback.format_exc())
            db.session.rollback()
            flash(f'Erro ao atualizar entidade: {str(e)}', 'danger')
            return render_template('entidades/form.html', action='editar', entidade=entidade, vendedores=vendedores)
    
    # GET request - show form for editing
    logger.info(f'[EDITAR] Renderizando formulário para entidade ID={id}')
    return render_template('entidades/form.html', action='editar', entidade=entidade, vendedores=vendedores)


@entidades_bp.route('/<int:id>/ver')
@login_required
def ver(id):
    """View entity details"""
    entidade = scoped_get_or_404(Entidade, id)
    lancamentos = entidade.lancamentos.limit(10).all()
    
    return render_template(
        'entidades/details.html',
        entidade=entidade,
        lancamentos=lancamentos
    )


@entidades_bp.route('/<int:id>/deletar', methods=['POST'])
@login_required
def deletar(id):
    """Delete entity"""
    entidade = scoped_get_or_404(Entidade, id)
    
    try:
        # Soft delete - just deactivate
        entidade.ativo = False
        db.session.commit()
        flash(f'Entidade {entidade.nome} desativada com sucesso', 'success')
    except Exception as e:
        import logging, traceback
        db.session.rollback()
        logging.error('Erro ao deletar entidade: %s\n%s', e, traceback.format_exc())
        flash(f'Erro ao deletar entidade: {str(e)}', 'danger')
    
    return redirect(url_for('entidades.index'))


@entidades_bp.route('/api/search')
@login_required
def api_search():
    """API for entity search - used in select fields"""
    termo = request.args.get('q', '')
    tipo = request.args.get('tipo', '')
    
    query = scoped_query(Entidade).filter(Entidade.ativo == True)
    
    if tipo:
        query = query.filter_by(tipo=tipo)
    
    if termo:
        query = query.filter(
            (Entidade.nome.ilike(f'%{termo}%')) |
            (Entidade.cnpj_cpf.ilike(f'%{termo}%'))
        )
    
    entidades = query.limit(10).all()
    
    return jsonify([{
        'id': e.id,
        'text': f'{e.nome} ({e.cnpj_cpf})',
        'cnpj_cpf': e.cnpj_cpf,
        'tipo': e.tipo
    } for e in entidades])
