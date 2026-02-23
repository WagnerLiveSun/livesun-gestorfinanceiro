# LiveSun Financeiro
# Sistema de Gestão de Fluxo de Caixa

---

## 📋 Descrição

**LiveSun Financeiro** é um sistema completo de gestão financeira desenvolvido em Python com Flask, projetado para automação de fluxo de caixa, controle de contas a pagar/receber e relatórios financeiros em tempo real.

### ✨ Características Principais

- ✅ **Autenticação Segura**: Login com usuário e senha (Admin/admin123 como padrão)
- ✅ **Cadastros Completos**: Entidades, Fluxo de Caixa, Contas Bancárias
- ✅ **Lançamentos**: Registre receitas e despesas com controle de status
- ✅ **Relatórios**: Contas a Pagar, Contas a Receber e Fluxo de Caixa Previsto/Realizado
- ✅ **Design Responsivo**: Interface moderna para PC, Tablet e Mobile
- ✅ **Dark Mode**: Tema escuro com gradientes sofisticados
- ✅ **Banco de Dados**: Suporte para MySQL com SQLAlchemy ORM

---

## 🚀 Instalação

### Requisitos
- Python 3.8+
- MySQL 5.7+ (ou MariaDB)
- pip

### 1. Clonar o Repositório

```bash
cd d:\App_LiveSun\Livesun_Financeiro
```

### 2. Criar Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:
```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=sua-chave-secreta-aqui
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=livesun_financeiro
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
```

### 5. Criar Banco de Dados

```sql
CREATE DATABASE livesun_financeiro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Executar a Aplicação

```bash
python run.py
```

A aplicação estará disponível em: **http://localhost:5000**

---

## 🔐 Acesso Padrão

- **Usuário**: `admin`
- **Senha**: `admin123`

> ⚠️ Mude a senha após o primeiro acesso em produção!

---

## 📁 Estrutura do Projeto

```
Livesun_Financeiro/
├── config/
│   └── config.py              # Configurações da aplicação
├── src/
│   ├── app.py                 # Factory Flask
│   ├── models/
│   │   └── __init__.py        # Modelos do banco de dados
│   ├── routes/
│   │   ├── auth.py            # Autenticação
│   │   ├── dashboard.py       # Dashboard
│   │   ├── entidades.py       # CRUD Entidades
│   │   ├── fluxo.py           # CRUD Plano de Contas
│   │   ├── contas_banco.py    # CRUD Contas Bancárias
│   │   ├── lancamentos.py     # CRUD Lançamentos
│   │   └── relatorios.py      # Relatórios financeiros
│   ├── templates/
│   │   ├── layout.html        # Template base
│   │   ├── login.html         # Tela de login
│   │   ├── dashboard.html     # Dashboard
│   │   ├── auth/              # Templates de autenticação
│   │   ├── entidades/         # Templates de entidades
│   │   ├── fluxo/             # Templates de fluxo
│   │   ├── contas_banco/      # Templates de contas
│   │   ├── lancamentos/       # Templates de lançamentos
│   │   ├── relatorios/        # Templates de relatórios
│   │   └── errors/            # Templates de erro
│   ├── static/
│   │   ├── css/               # Estilos CSS
│   │   ├── js/                # Scripts JavaScript
│   │   └── images/            # Imagens
│   └── utils/                 # Utilitários
├── data/                      # Armazenamento de dados locais
├── .env.example               # Exemplo de variáveis de ambiente
├── requirements.txt           # Dependências Python
├── run.py                     # Script de execução
└── README.md                  # Este arquivo
```

---

## 📊 Principais Funcionalidades

### 1. **Dashboard**
- Resumo de contas a pagar/receber
- Total de entidades e contas bancárias
- Saldo total atualizado
- Últimos lançamentos

### 2. **Cadastros**

#### Entidades
- Clientes, Fornecedores, Colaboradores, Vendedores
- CNPJ/CPF, Inscrição Estadual/Municipal
- Endereço, Contato, Contrato/Produto
- Status ativo/inativo

#### Plano de Fluxo de Caixa
- Código e Descrição
- Tipo: Pagamento (P) ou Recebimento (R)
- Máscara de código (999 ou 9.99)
- Nível Sintético e Analítico

#### Contas Bancárias
- Banco, Agência, Número da Conta
- Relacionamento com Plano de Fluxo
- Saldo inicial por conta
- Histórico de movimentações

### 3. **Lançamentos**
- Data do evento, vencimento e pagamento
- Status: Aberto, Pago, Vencido
- Relacionamento com Fluxo, Conta e Entidade
- Valor real e valor pago
- Documento e observações

### 4. **Relatórios**

#### Contas a Pagar
- Filtros por data, fluxo, banco, fornecedor
- Total previsto vs. pago
- Status de cada lançamento

#### Contas a Receber
- Filtros por data, fluxo, banco, cliente
- Total previsto vs. recebido
- Status de cada lançamento

#### Fluxo de Caixa
- Previsto: baseado em data de vencimento
- Realizado: baseado em data de pagamento
- Saldo anterior, entradas, saídas, saldo atual

---

## 🎨 Design System

### Cores
- **Fundo**: `#020617` (Quase preto)
- **Primária**: `#2563eb` (Azul)
- **Sucesso**: `#22c55e` (Verde)
- **Alerta**: `#fbbf24` (Amarelo)
- **Erro**: `#ef4444` (Vermelho)
- **Texto**: `#e5e7eb` (Cinza claro)

### Componentes
- Bootstrap 5 para responsividade
- Font Awesome 6 para ícones
- Dark mode com gradientes
- Cards com backdrop blur
- Navegação sidebar
- Topbar responsivo

---

## 🔧 Configuração do Banco de Dados

### Usar um banco de dados existente

Edite `.env`:
```env
DB_HOST=seu_host
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=seu_banco
```

### Criar novo banco

```sql
CREATE DATABASE livesun_financeiro;
USE livesun_financeiro;
```

A aplicação criará automaticamente as tabelas na primeira execução.

---

## 📱 Responsividade

O sistema é totalmente responsivo:
- **Desktop**: Sidebar + Conteúdo
- **Tablet**: Layout otimizado
- **Mobile**: Menu colapsável, tabelas scroll

---

## 🔒 Segurança

- ✅ Senhas com hash PBKDF2
- ✅ CSRF Protection (Flask-WTF)
- ✅ Session management
- ✅ SQL Injection prevention (SQLAlchemy ORM)
- ✅ XSS protection (Jinja2 escaping)

---

## 📝 Criar Novos Usuários

Via código Python:
```python
from src.app import create_app
from src.models import db, User

app = create_app()
with app.app_context():
    user = User(
        username='novo_usuario',
        email='user@example.com',
        full_name='Nome do Usuário',
        is_admin=False
    )
    user.set_password('senha')
    db.session.add(user)
    db.session.commit()
    print('Usuário criado!')
```

---

## 🐛 Troubleshooting

### Erro de conexão com banco de dados
```
Certifique-se que MySQL está rodando:
- localhost:3306 está acessível
- Credenciais estão corretas no .env
- Banco livesun_financeiro existe
```

### Porta 5000 já em uso
```bash
# Mude em .env
SERVER_PORT=5001
```

### Erro de import
```bash
# Instale novamente as dependências
pip install -r requirements.txt --force-reinstall
```

---

## 📞 Suporte

Para problemas ou sugestões, abra uma issue ou entre em contato.

---

## 📄 Licença

© 2026 LiveSun. Todos os direitos reservados.

---

**Desenvolvido com ❤️ em Python**
