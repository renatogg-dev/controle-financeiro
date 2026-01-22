import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import uuid
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from database import get_database, get_current_user

# =============================================================================
# Configuracao da Pagina
# =============================================================================
st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# Constantes
# =============================================================================
CATEGORIES = [
    "Alimentacao",
    "Transporte",
    "Moradia",
    "Saude",
    "Lazer",
    "Educacao",
    "Outros"
]

CATEGORY_COLORS = {
    "Alimentacao": "#2b6cb0",
    "Transporte": "#63b3ed",
    "Moradia": "#2f855a",
    "Saude": "#f6ad55",
    "Lazer": "#805ad5",
    "Educacao": "#e53e3e",
    "Outros": "#4a5568"
}

# =============================================================================
# Inicializacao
# =============================================================================
db = get_database()

if "editing_transaction" not in st.session_state:
    st.session_state.editing_transaction = None

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # "login" ou "signup"


# =============================================================================
# Funcoes Auxiliares
# =============================================================================
def format_currency(value):
    """Formata valor para moeda brasileira"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def get_month_key(dt):
    """Retorna chave do mes no formato YYYY-MM"""
    if isinstance(dt, str):
        return dt[:7]
    return dt.strftime("%Y-%m")


def get_monthly_totals(transactions, target_month):
    """Calcula totais do mes"""
    month_transactions = [
        t for t in transactions 
        if get_month_key(t["date"]) == target_month
    ]
    
    income = sum(t["amount"] for t in month_transactions if t["type"] == "income")
    expense = sum(t["amount"] for t in month_transactions if t["type"] == "expense")
    
    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "transactions": month_transactions
    }


def add_months(year_month, delta):
    """Adiciona meses a uma data YYYY-MM"""
    year, month = map(int, year_month.split("-"))
    dt = date(year, month, 1) + relativedelta(months=delta)
    return dt.strftime("%Y-%m")


# =============================================================================
# CSS Customizado
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #667085;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }
    .positive { color: #2f855a; }
    .negative { color: #c53030; }
    .transaction-item {
        background: #fafbfe;
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.75rem;
    }
    .reminder-due-soon {
        background: #fff5f5;
        border-color: #fed7d7;
    }
    .reminder-overdue {
        background: #fff1f1;
        border-color: #feb2b2;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 999px;
    }
    .db-status {
        padding: 0.5rem;
        border-radius: 8px;
        font-size: 0.85rem;
        text-align: center;
    }
    .db-cloud {
        background: #c6f6d5;
        color: #22543d;
    }
    .db-local {
        background: #feebc8;
        color: #744210;
    }
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
    }
    .user-info {
        padding: 0.75rem;
        background: #edf2f7;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Tela de Login/Cadastro
# =============================================================================
def show_auth_page():
    """Exibe pagina de autenticacao"""
    st.markdown('<h1 class="main-header" style="text-align: center;">💰 Controle Financeiro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header" style="text-align: center;">Organize seus gastos com facilidade.</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Toggle entre Login e Cadastro
        tab_login, tab_signup = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        
        with tab_login:
            with st.form("login_form"):
                st.subheader("Acesse sua conta")
                email = st.text_input("Email", placeholder="seu@email.com", key="login_email")
                password = st.text_input("Senha", type="password", placeholder="Sua senha", key="login_password")
                
                if st.form_submit_button("Entrar", use_container_width=True, type="primary"):
                    if email and password:
                        with st.spinner("Entrando..."):
                            result = db.sign_in(email, password)
                            if result["success"]:
                                st.session_state.user = result["user"]
                                st.success("Login realizado com sucesso!")
                                st.rerun()
                            else:
                                st.error(result["error"])
                    else:
                        st.warning("Preencha email e senha")
        
        with tab_signup:
            with st.form("signup_form"):
                st.subheader("Crie sua conta")
                new_email = st.text_input("Email", placeholder="seu@email.com", key="signup_email")
                new_password = st.text_input("Senha", type="password", placeholder="Minimo 6 caracteres", key="signup_password")
                confirm_password = st.text_input("Confirmar Senha", type="password", placeholder="Repita a senha", key="signup_confirm")
                
                if st.form_submit_button("Criar Conta", use_container_width=True, type="primary"):
                    if new_email and new_password and confirm_password:
                        if new_password != confirm_password:
                            st.error("As senhas nao conferem")
                        elif len(new_password) < 6:
                            st.error("A senha deve ter pelo menos 6 caracteres")
                        else:
                            with st.spinner("Criando conta..."):
                                result = db.sign_up(new_email, new_password)
                                if result["success"]:
                                    st.success("Conta criada! Agora faca login.")
                                else:
                                    st.error(result["error"])
                    else:
                        st.warning("Preencha todos os campos")
        
        st.divider()
        st.caption("Seus dados ficam seguros e privados. Cada usuario tem acesso apenas aos seus proprios dados.")


# =============================================================================
# Aplicacao Principal
# =============================================================================
def show_main_app():
    """Exibe aplicacao principal (usuario logado)"""
    user = get_current_user()
    
    # Header
    st.markdown('<h1 class="main-header">Controle Financeiro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Organize seus gastos com facilidade.</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Info do usuario
        st.markdown(f'<div class="user-info">👤 {user.email}</div>', unsafe_allow_html=True)
        
        if st.button("🚪 Sair", use_container_width=True):
            db.sign_out()
            st.rerun()
        
        st.divider()
        
        st.header("Mes de Referencia")
        current_date = date.today()
        
        # Gerar lista de meses
        months_options = []
        for i in range(-12, 13):
            dt = current_date.replace(day=1) + relativedelta(months=i)
            months_options.append(dt.strftime("%Y-%m"))
        
        current_month_str = current_date.strftime("%Y-%m")
        default_index = months_options.index(current_month_str) if current_month_str in months_options else 12
        
        selected_month = st.selectbox(
            "Selecione o mes",
            options=months_options,
            index=default_index,
            format_func=lambda x: datetime.strptime(x, "%Y-%m").strftime("%B %Y").capitalize()
        )
        
        st.divider()
        st.markdown('<div class="db-status db-cloud">☁️ Dados seguros na nuvem</div>', unsafe_allow_html=True)
    
    # Tabs
    tab_resumo, tab_transacoes, tab_metas, tab_lembretes = st.tabs([
        "📊 Resumo", "💳 Transacoes", "🎯 Metas", "🔔 Lembretes"
    ])
    
    # Tab Resumo
    with tab_resumo:
        transactions = db.load_transactions()
        totals = get_monthly_totals(transactions, selected_month)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            delta_color = "normal" if totals["balance"] >= 0 else "inverse"
            st.metric(
                label="Saldo do Mes",
                value=format_currency(totals["balance"]),
                delta="Positivo" if totals["balance"] > 0 else ("Negativo" if totals["balance"] < 0 else "Neutro"),
                delta_color=delta_color
            )
        
        with col2:
            st.metric(
                label="Receitas",
                value=format_currency(totals["income"]),
                delta="Total no mes",
                delta_color="off"
            )
        
        with col3:
            st.metric(
                label="Despesas", 
                value=format_currency(totals["expense"]),
                delta="Total no mes",
                delta_color="off"
            )
        
        st.divider()
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Gastos por Categoria")
            
            category_totals = {}
            for cat in CATEGORIES:
                total = sum(
                    t["amount"] for t in totals["transactions"]
                    if t["type"] == "expense" and t["category"] == cat
                )
                if total > 0:
                    category_totals[cat] = total
            
            if category_totals:
                fig_pie = px.pie(
                    values=list(category_totals.values()),
                    names=list(category_totals.keys()),
                    color=list(category_totals.keys()),
                    color_discrete_map=CATEGORY_COLORS,
                    hole=0.4
                )
                fig_pie.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                    margin=dict(t=20, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Nenhuma despesa registrada neste mes.")
        
        with col_chart2:
            st.subheader("Receitas x Despesas")
            
            months = [add_months(selected_month, i) for i in range(-5, 1)]
            income_data = []
            expense_data = []
            
            for month in months:
                month_totals = get_monthly_totals(transactions, month)
                income_data.append(month_totals["income"])
                expense_data.append(month_totals["expense"])
            
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Receitas",
                x=months,
                y=income_data,
                marker_color="#2f855a"
            ))
            fig_bar.add_trace(go.Bar(
                name="Despesas",
                x=months,
                y=expense_data,
                marker_color="#c53030"
            ))
            
            fig_bar.update_layout(
                barmode="group",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                margin=dict(t=20, b=20, l=20, r=20),
                yaxis=dict(tickformat=",.0f")
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # Tab Transacoes
    with tab_transacoes:
        transactions = db.load_transactions()
        
        col_form, col_list = st.columns([1, 1.5])
        
        with col_form:
            st.subheader("Nova Transacao")
            
            editing = st.session_state.editing_transaction
            
            with st.form("transaction_form", clear_on_submit=True):
                tipo = st.selectbox(
                    "Tipo",
                    options=["income", "expense"],
                    format_func=lambda x: "Receita" if x == "income" else "Despesa",
                    index=0 if not editing else (0 if editing["type"] == "income" else 1)
                )
                
                valor = st.number_input(
                    "Valor (R$)",
                    min_value=0.01,
                    step=0.01,
                    format="%.2f",
                    value=editing["amount"] if editing else 0.01
                )
                
                data_transacao = st.date_input(
                    "Data",
                    value=datetime.strptime(editing["date"], "%Y-%m-%d").date() if editing else date.today()
                )
                
                categoria = st.selectbox(
                    "Categoria",
                    options=CATEGORIES,
                    index=CATEGORIES.index(editing["category"]) if editing else 0
                )
                
                descricao = st.text_input(
                    "Descricao",
                    max_chars=60,
                    placeholder="Ex: Mercado",
                    value=editing["description"] if editing else ""
                )
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submitted = st.form_submit_button("Salvar", use_container_width=True, type="primary")
                with col_btn2:
                    cancelled = st.form_submit_button("Cancelar", use_container_width=True)
            
            if submitted and descricao:
                transaction = {
                    "id": editing["id"] if editing else str(uuid.uuid4()),
                    "type": tipo,
                    "amount": valor,
                    "date": data_transacao.strftime("%Y-%m-%d"),
                    "category": categoria,
                    "description": descricao.strip()
                }
                
                db.save_transaction(transaction)
                st.session_state.editing_transaction = None
                st.rerun()
            
            if cancelled:
                st.session_state.editing_transaction = None
                st.rerun()
        
        with col_list:
            st.subheader("Lista de Transacoes")
            
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                filter_category = st.selectbox(
                    "Categoria",
                    options=["Todas"] + CATEGORIES,
                    key="filter_cat"
                )
            with col_filter2:
                filter_type = st.selectbox(
                    "Tipo",
                    options=["Todos", "Receitas", "Despesas"],
                    key="filter_type"
                )
            
            filtered_transactions = [
                t for t in transactions
                if get_month_key(t["date"]) == selected_month
            ]
            
            if filter_category != "Todas":
                filtered_transactions = [t for t in filtered_transactions if t["category"] == filter_category]
            
            if filter_type == "Receitas":
                filtered_transactions = [t for t in filtered_transactions if t["type"] == "income"]
            elif filter_type == "Despesas":
                filtered_transactions = [t for t in filtered_transactions if t["type"] == "expense"]
            
            filtered_transactions.sort(key=lambda x: x["date"], reverse=True)
            
            if not filtered_transactions:
                st.info("Nenhuma transacao neste mes.")
            else:
                for t in filtered_transactions:
                    with st.container():
                        col_info, col_actions = st.columns([3, 1])
                        
                        with col_info:
                            tipo_emoji = "🟢" if t["type"] == "income" else "🔴"
                            st.markdown(f"""
                            **{tipo_emoji} {t['description']}**  
                            {format_currency(t['amount'])} - {t['date']}  
                            `{t['category']}`
                            """)
                        
                        with col_actions:
                            col_edit, col_delete = st.columns(2)
                            with col_edit:
                                if st.button("✏️", key=f"edit_{t['id']}", help="Editar"):
                                    st.session_state.editing_transaction = t
                                    st.rerun()
                            with col_delete:
                                if st.button("🗑️", key=f"del_{t['id']}", help="Excluir"):
                                    db.delete_transaction(t["id"])
                                    st.rerun()
                        
                        st.divider()
    
    # Tab Metas
    with tab_metas:
        transactions = db.load_transactions()
        goal = db.load_goal()
        
        col_goal_form, col_goal_progress = st.columns(2)
        
        with col_goal_form:
            st.subheader("Meta de Economia")
            
            with st.form("goal_form"):
                meta_valor = st.number_input(
                    "Meta mensal (R$)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    value=float(goal.get("amount", 0))
                )
                
                if st.form_submit_button("Salvar Meta", use_container_width=True, type="primary"):
                    db.save_goal({"amount": meta_valor})
                    st.rerun()
        
        with col_goal_progress:
            st.subheader("Progresso")
            
            target = float(goal.get("amount", 0))
            totals = get_monthly_totals(transactions, selected_month)
            current = max(totals["balance"], 0)
            
            if target > 0:
                percent = min((current / target), 1.0)
                
                if current >= target:
                    st.success("🎉 Parabens! Meta atingida.")
                else:
                    st.info("💪 Continue economizando!")
                
                st.progress(percent)
                
                col_val1, col_val2 = st.columns(2)
                with col_val1:
                    st.caption(f"Atual: {format_currency(current)}")
                with col_val2:
                    st.caption(f"Meta: {format_currency(target)}")
            else:
                st.warning("Defina uma meta para acompanhar.")
                st.progress(0.0)
    
    # Tab Lembretes
    with tab_lembretes:
        reminders = db.load_reminders()
        
        col_reminder_form, col_reminder_list = st.columns(2)
        
        with col_reminder_form:
            st.subheader("Adicionar Conta")
            
            with st.form("reminder_form", clear_on_submit=True):
                reminder_name = st.text_input(
                    "Conta",
                    max_chars=60,
                    placeholder="Ex: Luz"
                )
                
                reminder_amount = st.number_input(
                    "Valor (R$)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )
                
                reminder_due = st.date_input(
                    "Vencimento",
                    value=date.today()
                )
                
                reminder_notes = st.text_input(
                    "Observacoes",
                    max_chars=80,
                    placeholder="Ex: pagar via boleto"
                )
                
                if st.form_submit_button("Salvar Lembrete", use_container_width=True, type="primary"):
                    if reminder_name:
                        reminder = {
                            "id": str(uuid.uuid4()),
                            "name": reminder_name.strip(),
                            "amount": reminder_amount,
                            "dueDate": reminder_due.strftime("%Y-%m-%d"),
                            "notes": reminder_notes.strip()
                        }
                        db.save_reminder(reminder)
                        st.rerun()
        
        with col_reminder_list:
            st.subheader("Contas a Pagar")
            
            if not reminders:
                st.info("Nenhum lembrete cadastrado.")
            else:
                sorted_reminders = sorted(reminders, key=lambda x: x["dueDate"])
                today = date.today()
                
                for r in sorted_reminders:
                    due_date = datetime.strptime(r["dueDate"], "%Y-%m-%d").date()
                    diff_days = (due_date - today).days
                    
                    if diff_days < 0:
                        status = "🔴 Vencido"
                    elif diff_days <= 7:
                        status = "🟡 Vence em breve"
                    else:
                        status = "🟢 Em dia"
                    
                    with st.container():
                        col_info, col_del = st.columns([4, 1])
                        
                        with col_info:
                            amount_str = f" - {format_currency(r['amount'])}" if r['amount'] else ""
                            st.markdown(f"""
                            **{r['name']}** {status}  
                            📅 {r['dueDate']}{amount_str}  
                            _{r.get('notes', 'Sem observacoes') or 'Sem observacoes'}_
                            """)
                        
                        with col_del:
                            if st.button("🗑️", key=f"del_rem_{r['id']}", help="Excluir"):
                                db.delete_reminder(r["id"])
                                st.rerun()
                        
                        st.divider()


# =============================================================================
# Roteamento Principal
# =============================================================================
def main():
    """Funcao principal - roteia entre login e app"""
    
    # Se nao esta no modo cloud, mostra aviso
    if db.get_mode() != "cloud":
        st.warning("⚠️ Modo local ativo. Configure o Supabase para ter autenticacao e dados na nuvem.")
        show_main_app_local()
        return
    
    # Verifica se usuario esta logado
    user = get_current_user()
    
    if user:
        show_main_app()
    else:
        show_auth_page()


def show_main_app_local():
    """Versao simplificada para modo local (sem auth)"""
    st.markdown('<h1 class="main-header">Controle Financeiro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Organize seus gastos com facilidade.</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("Mes de Referencia")
        current_date = date.today()
        
        months_options = []
        for i in range(-12, 13):
            dt = current_date.replace(day=1) + relativedelta(months=i)
            months_options.append(dt.strftime("%Y-%m"))
        
        current_month_str = current_date.strftime("%Y-%m")
        default_index = months_options.index(current_month_str) if current_month_str in months_options else 12
        
        selected_month = st.selectbox(
            "Selecione o mes",
            options=months_options,
            index=default_index,
            format_func=lambda x: datetime.strptime(x, "%Y-%m").strftime("%B %Y").capitalize(),
            key="local_month"
        )
        
        st.divider()
        st.markdown('<div class="db-status db-local">💾 Modo Local (JSON)</div>', unsafe_allow_html=True)
    
    # Tabs simplificadas para modo local
    tab_resumo, tab_transacoes, tab_metas, tab_lembretes = st.tabs([
        "📊 Resumo", "💳 Transacoes", "🎯 Metas", "🔔 Lembretes"
    ])
    
    with tab_resumo:
        transactions = db.load_transactions()
        totals = get_monthly_totals(transactions, selected_month)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Saldo", format_currency(totals["balance"]))
        with col2:
            st.metric("Receitas", format_currency(totals["income"]))
        with col3:
            st.metric("Despesas", format_currency(totals["expense"]))
        
        st.info("Configure o Supabase para ter graficos, autenticacao e dados na nuvem.")
    
    with tab_transacoes:
        st.info("Configure o Supabase para gerenciar transacoes.")
    
    with tab_metas:
        st.info("Configure o Supabase para gerenciar metas.")
    
    with tab_lembretes:
        st.info("Configure o Supabase para gerenciar lembretes.")


if __name__ == "__main__":
    main()
