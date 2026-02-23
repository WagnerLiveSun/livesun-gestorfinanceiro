#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de inicialização do banco de dados LiveSun Financeiro

Cria o banco de dados e as tabelas automaticamente
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from src.app import create_app
from src.models import db, User, Entidade, FluxoContaModel, ContaBanco, Lancamento

def create_database():
    """Create database if it doesn't exist"""
    import pymysql
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'livesun_financeiro')
    
    try:
        # Connect without specifying database
        conn = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password if db_password else None,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
        
        print(f"✅ Banco de dados '{db_name}' pronto")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco de dados: {str(e)}")
        return False

def init_db():
    """Initialize database with tables"""
    
    # First, create the database
    print("\n" + "="*70)
    print("  LiveSun Financeiro - Inicialização do Banco de Dados")
    print("="*70 + "\n")
    
    print("📦 Criando banco de dados...")
    if not create_database():
        sys.exit(1)
    
    app = create_app()
    
    with app.app_context():
        try:
            print("📦 Criando tabelas do banco de dados...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            print("\n📝 Verificando dados padrão...")
            
            # Check if default admin user exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("   Criando usuário admin padrão...")
                admin = User(
                    username='admin',
                    email='admin@livesun.local',
                    full_name='Administrador',
                    is_admin=True,
                    is_active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("   ✅ Usuário admin criado: admin / admin123")
            else:
                print("   ℹ️ Usuário admin já existe")
            
            print("\n" + "="*70)
            print("  ✅ Banco de dados inicializado com sucesso!")
            print("="*70)
            print("\n🚀 Para iniciar a aplicação, execute:")
            print("   python run.py")
            print("\n🔐 Login padrão: admin / admin123")
            print("\n" + "="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ Erro ao inicializar banco de dados: {str(e)}")
            print("\nVerifique:")
            print("  1. MySQL está rodando?")
            print("  2. Arquivo .env está configurado corretamente?")
            print("  3. Banco de dados 'livesun_financeiro' foi criado?\n")
            sys.exit(1)

if __name__ == '__main__':
    init_db()
