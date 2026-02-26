import os
import logging
from decimal import Decimal, InvalidOperation
from sqlalchemy import inspect, text
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime

# Load environment variables
load_dotenv()

# Import configuration
from config.config import config

# Import models
from src.models import db, User, Entidade, FluxoContaModel, ContaBanco, Lancamento

# Setup logging
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app_errors.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor acesse sua conta para continuar.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.dashboard import dashboard_bp
    from src.routes.entidades import entidades_bp
    from src.routes.fluxo import fluxo_bp
    from src.routes.contas_banco import contas_banco_bp
    from src.routes.lancamentos import lancamentos_bp
    from src.routes.relatorios import relatorios_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(entidades_bp)
    app.register_blueprint(fluxo_bp)
    app.register_blueprint(contas_banco_bp)
    app.register_blueprint(lancamentos_bp)
    app.register_blueprint(relatorios_bp)

    @app.route('/suporte')
    def suporte():
        return render_template('suporte.html')

    @app.template_filter('brl')
    def format_brl(value):
        """Format numeric values using pt-BR currency style."""
        if value is None:
            value = 0
        try:
            num = Decimal(str(value)).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError, TypeError):
            num = Decimal('0.00')
        formatted = f"{num:,.2f}"
        return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    # Register context processors
    @app.context_processor
    def inject_user():
        return {
            'current_user': current_user,
            'year': datetime.now().year,
            'powered_by': 'LiveSun Financeiro'
        }
    
    # Create database tables
    with app.app_context():
        db.create_all()
        _ensure_user_settings_columns()
        _create_default_user()
        logger.info('Database tables created successfully')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        import traceback
        logger.error('Erro interno no servidor: %s\n%s', error, traceback.format_exc())
        db.session.rollback()
        mensagem = "Ocorreu um erro inesperado. Nossa equipe já foi notificada. Tente novamente ou entre em contato com o suporte."
        return render_template('errors/500.html', mensagem=mensagem), 500
    
    # Shell context for flask shell
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'Entidade': Entidade,
            'FluxoContaModel': FluxoContaModel,
            'ContaBanco': ContaBanco,
            'Lancamento': Lancamento
        }
    
    logger.info(f'Application created with {config_name} configuration')
    
    return app


def _create_default_user():
    """Create default admin user if not exists"""
    from src.models import Empresa
    # Cria empresa padrão se não existir
    empresa = Empresa.query.filter_by(nome='Empresa Padrão').first()
    if not empresa:
        empresa = Empresa(nome='Empresa Padrão', cnpj=None)
        db.session.add(empresa)
        db.session.commit()

    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@livesun.local',
            full_name='Administrador',
            is_admin=True,
            is_active=True,
            empresa_id=empresa.id
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()


def _ensure_user_settings_columns():
    """Ensure new user settings columns exist for existing databases."""
    try:
        inspector = inspect(db.engine)
        columns = {col['name'] for col in inspector.get_columns('users')}
        if 'dashboard_chart_days' not in columns:
            with db.engine.begin() as conn:
                conn.execute(
                    text('ALTER TABLE users ADD COLUMN dashboard_chart_days INTEGER DEFAULT 30')
                )
            logger.info('Added dashboard_chart_days column to users table')
    except Exception as exc:
        import traceback
        logger.error('Erro ao verificar/atualizar schema da tabela users: %s\n%s', exc, traceback.format_exc())
        logger.info('Default admin user created: admin/admin123')



# Exporta o app para o Gunicorn
app = create_app()

if __name__ == '__main__':
    # Run application
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('SERVER_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    print(f'\n{"="*60} - app.py:190')
    print(f'LiveSun Financeiro  Sistema de Gestão Financeira - app.py:191')
    print(f'Servidor rodando em: http://localhost:{port} - app.py:192')
    print(f'Login padrão: admin / admin123 - app.py:193')
    print(f'{"="*60}\n - app.py:194')
    
    app.run(host=host, port=port, debug=debug)
