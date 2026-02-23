@auth_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    # Apenas admin pode acessar
    if not current_user.is_admin:
        flash('Acesso permitido apenas para administradores.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Limite de 2 usuários por empresa
    from src.models import User
    user_count = User.query.filter_by(empresa_id=current_user.empresa_id).count()
    if user_count >= 2:
        flash('Limite de 2 usuários por empresa atingido.', 'warning')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')

        if not username or not email or not password or not full_name:
            flash('Preencha todos os campos', 'danger')
            return redirect(url_for('auth.add_user'))

        if User.query.filter_by(username=username).first():
            flash('Usuário já existe', 'danger')
            return redirect(url_for('auth.add_user'))
        if User.query.filter_by(email=email).first():
            flash('Email já registrado', 'danger')
            return redirect(url_for('auth.add_user'))

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_active=True,
            is_admin=False,
            empresa_id=current_user.empresa_id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Usuário criado com sucesso.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/add_user.html')
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from src.models import db, User, Empresa

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Preencha usuário e senha', 'danger')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Usuário ou senha inválidos', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Usuário inativo', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=request.form.get('remember'))
        flash(f'Bem-vindo, {user.full_name or user.username}!', 'success')
        
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de novos usuários - apenas para ambiente de desenvolvimento"""
    if request.method == 'POST':
        empresa_nome = request.form.get('empresa_nome')
        empresa_cnpj = request.form.get('empresa_cnpj')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')

        if not empresa_nome or not empresa_cnpj or not username or not email or not password or not full_name:
            flash('Preencha todos os campos', 'danger')
            return redirect(url_for('auth.register'))

        # Verifica se já existe empresa com mesmo CNPJ
        if Empresa.query.filter_by(cnpj=empresa_cnpj).first():
            flash('Já existe uma empresa cadastrada com este CPF/CNPJ.', 'danger')
            return redirect(url_for('auth.register'))

        # Cria empresa
        empresa = Empresa(nome=empresa_nome, cnpj=empresa_cnpj)
        db.session.add(empresa)
        db.session.flush()  # Para obter o id

        # Verifica se já existe usuário com mesmo username/email
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe', 'danger')
            db.session.rollback()
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('Email já registrado', 'danger')
            db.session.rollback()
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_active=True,
            is_admin=True,
            empresa_id=empresa.id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Empresa e usuário administrador criados com sucesso. Faça login para continuar.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if not current_user.is_admin:
        flash('Acesso permitido apenas para administradores.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            dias_grafico = int(request.form.get('dashboard_chart_days', '30'))
        except ValueError:
            dias_grafico = 30

        if dias_grafico < 7 or dias_grafico > 365:
            flash('Informe um periodo entre 7 e 365 dias.', 'warning')
        else:
            current_user.dashboard_chart_days = dias_grafico
            db.session.commit()
            flash('Preferencias atualizadas com sucesso.', 'success')

    return render_template('auth/perfil.html')
