# Controle Financeiro

Aplicacao web em Python/Streamlit para controle de receitas, despesas, metas e lembretes de contas.

**Recursos:**
- Sistema de login - cada usuario tem seus dados privados
- Dashboard com graficos interativos
- Cadastro de transacoes (receitas/despesas)
- Metas de economia com acompanhamento
- Lembretes de contas a pagar

## Requisitos

- Python 3.8 ou superior

## Instalacao Local

1. Crie um ambiente virtual:

```bash
python -m venv venv
```

2. Ative o ambiente virtual:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

3. Instale as dependencias:

```bash
pip install -r requirements.txt
```

## Executar Localmente

```bash
streamlit run app.py
```

---

## Deploy no Streamlit Cloud (com Supabase)

### 1. Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com) e crie uma conta
2. Crie um novo projeto
3. Va em **SQL Editor** e execute o script abaixo

### 2. Script SQL (NOVO - com user_id)

```sql
-- Tabela de transacoes (com user_id)
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL,
    type TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    category TEXT NOT NULL,
    description TEXT
);

-- Tabela de metas (com user_id)
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0
);

-- Tabela de lembretes (com user_id)
CREATE TABLE reminders (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    amount DECIMAL(10,2),
    "dueDate" DATE NOT NULL,
    notes TEXT
);

-- Indices para melhor performance
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_goals_user ON goals(user_id);
CREATE INDEX idx_reminders_user ON reminders(user_id);

-- Habilitar Row Level Security (RLS)
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;

-- Politicas de seguranca: usuarios so veem seus proprios dados
CREATE POLICY "Users can view own transactions" ON transactions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own transactions" ON transactions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own transactions" ON transactions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own transactions" ON transactions
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own goals" ON goals
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own goals" ON goals
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own goals" ON goals
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own goals" ON goals
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view own reminders" ON reminders
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own reminders" ON reminders
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own reminders" ON reminders
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own reminders" ON reminders
    FOR DELETE USING (auth.uid() = user_id);
```

### 3. Configurar Autenticacao no Supabase

1. Va em **Authentication > Providers**
2. Certifique-se que **Email** esta habilitado
3. Em **Authentication > URL Configuration**, verifique o Site URL

### 4. Copiar Credenciais

Va em **Settings > API** e copie:
- **Project URL** → `SUPABASE_URL`
- **anon public key** → `SUPABASE_KEY`

### 5. Deploy no Streamlit Cloud

1. Suba o codigo para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Clique em **New app** e selecione seu repositorio
4. Em **Advanced settings > Secrets**, adicione:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-anon-key"
```

5. Clique em **Deploy**

---

## Como Funciona

### Sistema de Login

- Cada usuario cria sua conta com email e senha
- Os dados sao completamente separados entre usuarios
- Ninguem consegue ver os dados de outra pessoa

### Seguranca

- Senhas sao criptografadas pelo Supabase Auth
- Row Level Security (RLS) garante que cada usuario so acessa seus dados
- A chave usada (anon key) e segura para frontend

---

## Estrutura do Projeto

```
controle-financeiro/
├── app.py              # Aplicacao principal com login
├── database.py         # Modulo de persistencia com auth
├── requirements.txt    # Dependencias Python
├── GUIA_DE_USO.md      # Manual do usuario
└── README.md           # Este arquivo
```

## Suporte

Problemas ou sugestoes? Abra uma issue:
https://github.com/renatogg-dev/controle-financeiro/issues
