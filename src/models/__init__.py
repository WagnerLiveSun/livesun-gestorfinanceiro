

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# Modelo Empresa para multi-tenant
class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)
    cnpj = db.Column(db.String(18), unique=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Empresa {self.nome}>'

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='users')
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    dashboard_chart_days = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Entidade(db.Model):
    """Entity model - Cliente, Fornecedor, Colaborador, Vendedor"""
    __tablename__ = 'entidades'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='entidades')
    tipo = db.Column(db.String(1), nullable=False)  # C-Cliente, F-Fornecedor, C-Colaborador, V-Vendedor
    cnpj_cpf = db.Column(db.String(14), unique=True, nullable=False, index=True)
    inscricao_estadual = db.Column(db.String(20))
    inscricao_municipal = db.Column(db.String(20))
    nome = db.Column(db.String(150), nullable=False, index=True)
    nome_fantasia = db.Column(db.String(150))
    
    # Endereço
    endereco_rua = db.Column(db.String(150))
    endereco_numero = db.Column(db.String(10))
    endereco_bairro = db.Column(db.String(100))
    endereco_cidade = db.Column(db.String(100))
    endereco_uf = db.Column(db.String(2))
    endereco_cep = db.Column(db.String(8))
    
    # Contato
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Contrato/Produto
    contrato_produto = db.Column(db.Text)
    
    # Metadados
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    lancamentos = db.relationship('Lancamento', backref='entidade', lazy='dynamic', foreign_keys='Lancamento.entidade_id')
    
    def __repr__(self):
        return f'<Entidade {self.nome} ({self.tipo})>'
    
    def get_tipo_descricao(self):
        """Get type description"""
        tipos = {
            'C': 'Cliente',
            'F': 'Fornecedor',
            'L': 'Colaborador',
            'V': 'Vendedor'
        }
        return tipos.get(self.tipo, self.tipo)


class FluxoContaModel(db.Model):
    """Chart of Accounts for Cash Flow - Plano de Contas de Fluxo de Caixa"""
    __tablename__ = 'fluxo_contas_modelo'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='fluxo_contas')
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)  # 999 ou 9.99 format
    descricao = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(1), nullable=False)  # P-Pagamento, R-Recebimento
    mascara = db.Column(db.String(50))  # 999 ou 9.99
    nivel_sintetico = db.Column(db.Integer)  # Nível sintético da máscara
    nivel_analitico = db.Column(db.Integer)  # Nível analítico da máscara
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    lancamentos = db.relationship('Lancamento', backref='fluxo_conta', lazy='dynamic')
    
    def __repr__(self):
        return f'<FluxoContaModel {self.codigo} - {self.descricao}>'


class ContaBanco(db.Model):
    """Bank Account - Conta de Banco"""
    __tablename__ = 'contas_banco'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='contas_banco')
    nome = db.Column(db.String(150), nullable=False, index=True)
    banco = db.Column(db.String(50), nullable=False)
    agencia = db.Column(db.String(10), nullable=False)
    numero_conta = db.Column(db.String(20), nullable=False)
    dv = db.Column(db.String(2))  # Dígito verificador
    tipo = db.Column(db.String(20))  # Corrente, Poupança, etc
    
    # Relacionamento com conta de fluxo analítica
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'))
    fluxo_conta = db.relationship('FluxoContaModel', foreign_keys=[fluxo_conta_id])
    
    saldo_inicial = db.Column(db.Numeric(15, 2), default=0.00)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    lancamentos = db.relationship('Lancamento', backref='conta_banco', lazy='dynamic')
    
    def __repr__(self):
        return f'<ContaBanco {self.nome} ({self.banco})>'


class Lancamento(db.Model):
    """Expense/Income Record - Lançamento de Despesa/Receita"""
    __tablename__ = 'lancamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='lancamentos')
    
    # Datas
    data_evento = db.Column(db.Date, nullable=False, index=True)
    data_vencimento = db.Column(db.Date, nullable=False, index=True)
    data_pagamento = db.Column(db.Date, index=True)  # Nulo se não pago
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='aberto')  # aberto, pago, vencido
    
    # Relacionamentos
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=False)
    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'), nullable=False)
    entidade_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False)
    
    # Valores
    valor_real = db.Column(db.Numeric(15, 2), nullable=False)  # Valor original
    valor_pago = db.Column(db.Numeric(15, 2), default=0.00)  # Valor efetivamente pago
    
    # Documentação
    numero_documento = db.Column(db.String(50), index=True)
    observacoes = db.Column(db.Text)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Lancamento {self.numero_documento} - R$ {self.valor_real}>'


class FluxoCaixaRealizado(db.Model):
    """Cash Flow Realized - Fluxo de Caixa Realizado"""
    __tablename__ = 'fluxo_caixa_realizado'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='fluxo_caixa_realizado')
    
    # Data
    data = db.Column(db.Date, nullable=False, index=True)
    
    # Relacionamento
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=False)
    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'), nullable=False)
    
    fluxo_conta = db.relationship('FluxoContaModel', foreign_keys=[fluxo_conta_id])
    conta_banco = db.relationship('ContaBanco', foreign_keys=[conta_banco_id])
    
    # Valores
    saldo_anterior = db.Column(db.Numeric(15, 2), default=0.00)
    valor_pago = db.Column(db.Numeric(15, 2), default=0.00)  # Saída (Pagamento)
    valor_recebido = db.Column(db.Numeric(15, 2), default=0.00)  # Entrada (Recebimento)
    saldo_atual = db.Column(db.Numeric(15, 2), default=0.00)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FluxoCaixaRealizado {self.data}>'


class FluxoCaixaPrevisto(db.Model):
    """Cash Flow Forecast - Fluxo de Caixa Previsto"""
    __tablename__ = 'fluxo_caixa_previsto'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='fluxo_caixa_previsto')
    
    # Data
    data = db.Column(db.Date, nullable=False, index=True)
    
    # Relacionamento
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=False)
    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'), nullable=False)
    
    fluxo_conta = db.relationship('FluxoContaModel', foreign_keys=[fluxo_conta_id])
    conta_banco = db.relationship('ContaBanco', foreign_keys=[conta_banco_id])
    
    # Valores
    saldo_anterior = db.Column(db.Numeric(15, 2), default=0.00)
    valor_previsto_pago = db.Column(db.Numeric(15, 2), default=0.00)  # Saída (Pagamento previsto)
    valor_previsto_recebido = db.Column(db.Numeric(15, 2), default=0.00)  # Entrada (Recebimento previsto)
    saldo_previsto = db.Column(db.Numeric(15, 2), default=0.00)
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FluxoCaixaPrevisto {self.data}>'
