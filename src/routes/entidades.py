from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from src.models import db, Entidade
from datetime import datetime

entidades_bp = Blueprint('entidades', __name__, url_prefix='/entidades')


@entidades_bp.route('/')
@login_required
def index():
    """List all entities"""
    page = request.args.get('page', 1, type=int)
    tipo = request.args.get('tipo', '')
    busca = request.args.get('busca', '')
    
    query = Entidade.query
    
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
    if request.method == 'POST':
        try:
            entidade = Entidade(
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
                ativo=request.form.get('ativo') == 'on'
            )
            
            db.session.add(entidade)
            db.session.commit()
            
            flash(f'Entidade {entidade.nome} criada com sucesso', 'success')
            return redirect(url_for('entidades.index'))
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao criar entidade: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao criar entidade: {str(e)}', 'danger')
    
    return render_template('entidades/form.html', action='criar')


@entidades_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edit entity"""
    entidade = Entidade.query.get_or_404(id)
    
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
            
            db.session.commit()
            
            flash(f'Entidade {entidade.nome} atualizada com sucesso', 'success')
            return redirect(url_for('entidades.index'))
        
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro ao atualizar entidade: %s\n%s', e, traceback.format_exc())
            flash(f'Erro ao atualizar entidade: {str(e)}', 'danger')
    
    return render_template('entidades/form.html', action='editar', entidade=entidade)


@entidades_bp.route('/<int:id>/ver')
@login_required
def ver(id):
    """View entity details"""
    entidade = Entidade.query.get_or_404(id)
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
    entidade = Entidade.query.get_or_404(id)
    
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
    
    query = Entidade.query.filter(Entidade.ativo == True)
    
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
