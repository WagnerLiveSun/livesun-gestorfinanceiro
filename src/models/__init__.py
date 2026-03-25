
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# Modelo de Entidade (restaurado)
class Entidade(db.Model):
    __tablename__ = 'entidades'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='entidades')
    nome = db.Column(db.String(150), nullable=False)
    cnpj_cpf = db.Column(db.String(18), nullable=False, index=True)

    tipo = db.Column(db.String(1))
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=True)
    fluxo_conta = db.relationship('FluxoContaModel', foreign_keys=[fluxo_conta_id])
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)

    def get_tipo_descricao(self):
        """Retorna a descrição do tipo da entidade (C=Cliente, F=Fornecedor, V=Funcionário, etc)."""
        if self.tipo == 'C':
            return 'Cliente'
        elif self.tipo == 'F':
            return 'Fornecedor'
        elif self.tipo == 'V':
            return 'Funcionário'
        elif self.tipo:
            return self.tipo
        return 'Não definido'

    def __repr__(self):
        return f'<Entidade {self.nome}>'

# Modelo de Usuário para autenticação
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.UniqueConstraint('empresa_id', 'username', name='uq_users_empresa_username'),
    )
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='users')
    username = db.Column(db.String(80), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    dashboard_chart_days = db.Column(db.Integer, default=30)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

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

class Comissao(db.Model):
    """Commission Records - Registro de Comissões"""
    __tablename__ = 'comissoes'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='comissoes')
    
    # Identificação de apuração
    id_apuracao = db.Column(db.Integer, nullable=False, index=True)  # Sequence da apuração
    # Relacionamentos
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id'), nullable=False, index=True)
    lancamento = db.relationship('Lancamento', foreign_keys=[lancamento_id])
    
    entidade_cliente_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    entidade_vendedor_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False, index=True)
    
    # Datas
    dt_lancamento = db.Column(db.Date, nullable=False, index=True)
    dt_vencimento = db.Column(db.Date, nullable=False, index=True)
    dt_pagamento_recebimento = db.Column(db.Date, nullable=False, index=True)  # data_pagamento do lancamento
    
    # Valores
    vl_nota = db.Column(db.Numeric(15, 2), nullable=False)  # valor_real
    vl_imposto = db.Column(db.Numeric(15, 2), default=0.00)
    vl_outros_custos = db.Column(db.Numeric(15, 2), default=0.00)
    vl_repasse = db.Column(db.Numeric(15, 2), default=0.00)  # Valor de repasse
    vl_liquido = db.Column(db.Numeric(15, 2), nullable=False)  # Base de cálculo
    aliquota_aplicada = db.Column(db.Numeric(5, 2), nullable=False)  # Percentual aplicado
    vl_comissao = db.Column(db.Numeric(15, 2), nullable=False)  # Valor da comissão
    
    # Situação
    situacao = db.Column(db.String(20), default='ativo')  # ativo, estornado, reapurado
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_comissao_empresa_apuracao', 'empresa_id', 'id_apuracao'),
        db.Index('idx_comissao_empresa_lancamento', 'empresa_id', 'lancamento_id', 'entidade_cliente_id', 'entidade_vendedor_id'),
    )
    
    def __repr__(self):
        return f'<Comissao {self.id} - Apuração {self.id_apuracao} - R$ {self.vl_comissao}>'

# -------------------
# Importação de NFSe
# -------------------
class ImportacaoNFSe(db.Model):
    __tablename__ = 'importacao_nfse'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='importacoes_nfse')
    chave_nota = db.Column(db.String(60), nullable=False, index=True)
    numero_nota = db.Column(db.String(30), nullable=False)
    data_emissao = db.Column(db.Date, nullable=False)
    cnpj_tomador = db.Column(db.String(20), nullable=False)
    entidade_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=True, index=True)
    entidade = db.relationship('Entidade', foreign_keys=[entidade_id], backref='importacoes_nfse')

    # Relacionamento reverso para facilitar exclusão em cascata
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos.id', ondelete='CASCADE'), nullable=True, index=True)
    lancamento = db.relationship('Lancamento', backref=db.backref('importacao_nfse', cascade='all, delete-orphan', passive_deletes=True), foreign_keys=[lancamento_id])
    valor_bruto = db.Column(db.Numeric(15, 2), nullable=False)
    valor_impostos = db.Column(db.Numeric(15, 2))
    descricao_servico = db.Column(db.String(255))
    status_importacao = db.Column(db.String(20), default='sucesso')
    mensagem_erro = db.Column(db.String(255))
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)
    # Armazena o XML original importado
    # xml_original removido (não armazenar XML no banco)
    
    def __repr__(self):
        return f'<ImportacaoNFSe {self.chave_nota} - {self.numero_nota}>'
    
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
    
    # Campos para comissão (aplicável apenas a CLIENTE)
    aliquota_comissao_especifica = db.Column(db.Numeric(5, 2), nullable=True)  # Percentual específico
    valor_repasse = db.Column(db.Numeric(10, 2), default=0.00)  # Valor fixo de repasse ao fornecedor

    entidade_vendedor_padrao_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=True)  # Vendedor padrão
    entidade_vendedor_padrao = db.relationship('Entidade', foreign_keys=[entidade_vendedor_padrao_id], backref='importacoes_nfse_vendedor_padrao')
    
    # Metadados
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    




class FluxoContaModel(db.Model):
    """Chart of Accounts for Cash Flow - Plano de Contas de Fluxo de Caixa"""
    __tablename__ = 'fluxo_contas_modelo'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='fluxo_contas')
    codigo = db.Column(db.String(20), nullable=False, index=True)  # 999 ou 9.99 format
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
    is_principal = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Indica se é a conta principal da entidade
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
    entidade_id = db.Column(db.Integer, db.ForeignKey('entidades.id'), nullable=False)
    entidade = db.relationship('Entidade', backref='lancamentos')
    fluxo_conta_id = db.Column(db.Integer, db.ForeignKey('fluxo_contas_modelo.id'), nullable=False)
    conta_banco_id = db.Column(db.Integer, db.ForeignKey('contas_banco.id'), nullable=False)
    
    # Valores
    valor_real = db.Column(db.Numeric(15, 2), nullable=False)  # Valor original
    valor_pago = db.Column(db.Numeric(15, 2), default=0.00)  # Valor efetivamente pago
    valor_imposto = db.Column(db.Numeric(15, 2), default=0.00)  # Imposto
    valor_outros_custos = db.Column(db.Numeric(15, 2), default=0.00)  # Outros custos
    
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


class ParametroSistema(db.Model):
    """System Parameters - Parâmetros de Sistema"""
    __tablename__ = 'parametros_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, index=True)
    empresa = db.relationship('Empresa', backref='parametros_sistema')
    
    chave = db.Column(db.String(100), nullable=False)  # Nome do parâmetro
    valor = db.Column(db.Text, nullable=False)  # Valor armazenado como string
    tipo = db.Column(db.String(20), default='string')  # Tipo: string, numeric, boolean
    descricao = db.Column(db.String(255))
    
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('empresa_id', 'chave', name='uq_parametro_chave'),)
    
    def __repr__(self):
        return f'<ParametroSistema {self.chave}={self.valor}>'


