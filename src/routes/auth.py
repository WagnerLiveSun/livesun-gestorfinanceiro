from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from src.models import db, User, Empresa

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

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

    # GET -> render form
    return render_template('auth/add_user.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
            try:
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
            except Exception as e:
                import logging, traceback
                logging.error('Erro ao processar login: %s\n%s', e, traceback.format_exc())
                flash('Erro interno ao processar login. Tente novamente ou contate o suporte.', 'danger')
                return redirect(url_for('auth.login'))
    
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
        try:
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
            try:
                empresa_existente = Empresa.query.filter_by(cnpj=empresa_cnpj).first()
                if empresa_existente:
                    usuario_existente = User.query.filter_by(empresa_id=empresa_existente.id, is_admin=True).first()
                    import logging
                    logging.warning(f"empresa_existente: {empresa_existente}, usuario_existente: {usuario_existente}")
                    if usuario_existente:
                        flash(f'Já existe uma empresa cadastrada com este CPF/CNPJ. Usuário administrador responsável: {usuario_existente.username} (e-mail: {usuario_existente.email}). Caso não lembre o acesso, contate o suporte.', 'danger')
                    else:
                        flash('Já existe uma empresa cadastrada com este CPF/CNPJ. Caso não lembre o acesso, contate o suporte.', 'danger')
                    return redirect(url_for('auth.register'))
            except Exception as e:
                import logging, traceback
                logging.error(f"Erro ao verificar empresa existente: {e}\n{traceback.format_exc()}")
                flash('Erro interno ao verificar empresa existente. Tente novamente ou contate o suporte.', 'danger')
                return redirect(url_for('auth.register'))

            # Cria empresa
            empresa = Empresa(nome=empresa_nome, cnpj=empresa_cnpj)
            db.session.add(empresa)
            db.session.flush()  # Para obter o id

            # Inserir plano de fluxo de caixa padrão para a nova empresa
            from src.models import FluxoContaModel
            PLANO_PADRAO = [
            ("1", "Entradas de Caixa", "R", None, 1, None),
            ("1.1", "Receitas Operacionais", "R", None, 2, None),
            ("1.1.1", "Vendas à vista", "R", None, 3, 1),
            ("1.1.2", "Vendas cartão crédito", "R", None, 3, 1),
            ("1.1.3", "Vendas cartão débito", "R", None, 3, 1),
            ("1.1.4", "Recebimento mensalidades/serviços", "R", None, 3, 1),
            ("1.2", "Receitas Financeiras", "R", None, 2, None),
            ("1.2.1", "Juros recebidos", "R", None, 3, 1),
            ("1.2.2", "Descontos obtidos", "R", None, 3, 1),
            ("1.3", "Outras Entradas", "R", None, 2, None),
            ("1.3.1", "Empréstimos recebidos", "R", None, 3, 1),
            ("1.3.2", "Aporte de sócios", "R", None, 3, 1),
            ("1.3.3", "Reembolsos diversos", "R", None, 3, 1),
            ("2", "Saídas de Caixa", "P", None, 1, None),
            ("2.1", "Custos Operacionais", "P", None, 2, None),
            ("2.1.1", "Compra de mercadorias", "P", None, 3, 1),
            ("2.1.2", "Matéria-prima/insumos", "P", None, 3, 1),
            ("2.1.3", "Fretes sobre compras", "P", None, 3, 1),
            ("2.2", "Despesas Fixas", "P", None, 2, None),
            ("2.2.1", "Aluguel", "P", None, 3, 1),
            ("2.2.2", "Energia elétrica", "P", None, 3, 1),
            ("2.2.3", "Água", "P", None, 3, 1),
            ("2.2.4", "Internet e telefone", "P", None, 3, 1),
            ("2.3", "Despesas com Pessoal", "P", None, 2, None),
            ("2.3.1", "Salários", "P", None, 3, 1),
            ("2.3.2", "Encargos (INSS, FGTS)", "P", None, 3, 1),
            ("2.3.3", "Pró-labore", "P", None, 3, 1),
            ("2.4", "Despesas Variáveis", "P", None, 2, None),
            ("2.4.1", "Comissões sobre vendas", "P", None, 3, 1),
            ("2.4.2", "Taxas de cartão/maquininha", "P", None, 3, 1),
            ("2.4.3", "Impostos sobre vendas", "P", None, 3, 1),
            ("2.5", "Despesas Financeiras", "P", None, 2, None),
            ("2.5.1", "Juros e multas pagas", "P", None, 3, 1),
            ("2.5.2", "Tarifas bancárias", "P", None, 3, 1),
            ("2.6", "Outras Saídas", "P", None, 2, None),
            ("2.6.1", "Distribuição de lucros", "P", None, 3, 1),
            ("2.6.2", "Adiantamentos a sócios", "P", None, 3, 1),
        ]

            for codigo, descricao, tipo, mascara, nivel_sintetico, nivel_analitico in PLANO_PADRAO:
                conta = FluxoContaModel(
                    empresa_id=empresa.id,
                    codigo=codigo,
                    descricao=descricao,
                    tipo=tipo,
                    mascara=mascara,
                    nivel_sintetico=nivel_sintetico,
                    nivel_analitico=nivel_analitico,
                    ativo=True
                )
                db.session.add(conta)

            # Verifica se já existe usuário com mesmo username/email
            if User.query.filter_by(username=username).first():
                flash('Usuário já existe', 'danger')
                db.session.rollback()
                return redirect(url_for('auth.register'))
            if User.query.filter_by(email=email).first():
                flash('Email já registrado', 'danger')
                db.session.rollback()
                return redirect(url_for('auth.register'))

            # Sempre criar usuário admin neste cadastro
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
        except Exception as e:
            import logging, traceback
            db.session.rollback()
            logging.error('Erro no cadastro de empresa/usuário: %s\n%s', e, traceback.format_exc())
            flash('Erro interno ao cadastrar empresa/usuário. Tente novamente ou contate o suporte.', 'danger')
            return redirect(url_for('auth.register'))

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
