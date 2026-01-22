# Controle Financeiro

Aplicacao web em Python/Streamlit para controle de receitas, despesas, metas e lembretes de contas.

## Requisitos

- Python 3.8 ou superior

## Instalacao Local

1. Crie um ambiente virtual (recomendado):

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

## Como Executar Localmente

```bash
streamlit run app.py
```

O navegador abrira automaticamente em `http://localhost:8501`.

---

## Deploy no Streamlit Cloud (com Supabase)

Para ter seus dados salvos permanentemente na nuvem, siga estes passos:

### 1. Criar Banco de Dados no Supabase (Gratuito)

1. Acesse [supabase.com](https://supabase.com) e crie uma conta
2. Crie um novo projeto
3. Va em **SQL Editor** e execute o seguinte script para criar as tabelas:

```sql
-- Tabela de transacoes
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    category TEXT NOT NULL,
    description TEXT
);

-- Tabela de metas
CREATE TABLE goals (
    id TEXT PRIMARY KEY DEFAULT 'default',
    amount DECIMAL(10,2) NOT NULL DEFAULT 0
);

-- Tabela de lembretes
CREATE TABLE reminders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    amount DECIMAL(10,2),
    "dueDate" DATE NOT NULL,
    notes TEXT
);

-- Inserir meta padrao
INSERT INTO goals (id, amount) VALUES ('default', 0);
```

4. Copie suas credenciais:
   - Va em **Settings > API**
   - Copie a **URL** do projeto
   - Copie a **anon public key**

### 2. Subir Projeto para o GitHub

1. Crie um repositorio no GitHub
2. Faca upload dos arquivos:
   - `app.py`
   - `database.py`
   - `requirements.txt`

**Nao inclua** o arquivo `data.json` (dados locais).

### 3. Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Clique em **New app**
3. Selecione seu repositorio e o arquivo `app.py`
4. Em **Advanced settings > Secrets**, adicione:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-anon-key-aqui"
```

5. Clique em **Deploy**

Pronto! Seu app estara online com dados persistentes.

---

## Como Usar

1. Selecione o mes de referencia na barra lateral
2. Na aba **Transacoes**, adicione receitas e despesas
3. Veja o resumo e os graficos na aba **Resumo**
4. Defina uma meta mensal na aba **Metas**
5. Cadastre contas na aba **Lembretes** para nao esquecer vencimentos

## Recursos

- Saldo, receitas e despesas do mes
- Graficos interativos por categoria e comparativo mensal (Plotly)
- Cadastro de transacoes com edicao e exclusao
- Metas de economia com barra de progresso
- Lembretes de contas a pagar com destaque para vencidos
- Persistencia local (JSON) ou na nuvem (Supabase)

## Modos de Operacao

| Modo | Quando | Dados |
|------|--------|-------|
| **Local** | Sem configurar Supabase | Salvos em `data.json` |
| **Cloud** | Com Supabase configurado | Salvos no PostgreSQL |

A sidebar mostra qual modo esta ativo.

## Estrutura do Projeto

```
controle-financeiro-sheet/
├── app.py              # Aplicacao principal Streamlit
├── database.py         # Modulo de persistencia (Local/Supabase)
├── requirements.txt    # Dependencias Python
├── data.json           # Dados locais (gerado automaticamente)
└── README.md           # Documentacao
```
