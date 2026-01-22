"""
Modulo de conexao com Supabase para persistencia de dados.
Suporta autenticacao de usuarios e dados privados por usuario.
Fallback para arquivo JSON local quando Supabase nao esta configurado.
"""

import streamlit as st
import json
from pathlib import Path

# Tenta importar supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

DATA_FILE = Path(__file__).parent / "data.json"


def get_supabase_client() -> "Client | None":
    """Retorna cliente Supabase se configurado, senao None"""
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    
    return None


# =============================================================================
# Autenticacao
# =============================================================================

def sign_up(client: "Client", email: str, password: str) -> dict:
    """Registra novo usuario"""
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        if response.user:
            return {"success": True, "user": response.user}
        return {"success": False, "error": "Erro ao criar conta"}
    except Exception as e:
        error_msg = str(e)
        if "User already registered" in error_msg:
            return {"success": False, "error": "Este email ja esta cadastrado"}
        if "Password should be at least 6 characters" in error_msg:
            return {"success": False, "error": "A senha deve ter pelo menos 6 caracteres"}
        return {"success": False, "error": f"Erro: {error_msg}"}


def sign_in(client: "Client", email: str, password: str) -> dict:
    """Faz login do usuario"""
    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user:
            return {"success": True, "user": response.user, "session": response.session}
        return {"success": False, "error": "Email ou senha incorretos"}
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            return {"success": False, "error": "Email ou senha incorretos"}
        return {"success": False, "error": f"Erro: {error_msg}"}


def sign_out(client: "Client"):
    """Faz logout do usuario"""
    try:
        client.auth.sign_out()
    except Exception:
        pass


def get_current_user():
    """Retorna usuario atual do session_state"""
    return st.session_state.get("user", None)


def get_user_id() -> str | None:
    """Retorna ID do usuario atual"""
    user = get_current_user()
    if user:
        return user.id
    return None


# =============================================================================
# Funcoes Locais (JSON)
# =============================================================================

def init_local_data():
    """Inicializa dados locais se arquivo nao existe"""
    if not DATA_FILE.exists():
        save_local_data({
            "transactions": [],
            "goal": {"amount": 0},
            "reminders": []
        })


def load_local_data() -> dict:
    """Carrega dados do arquivo JSON local"""
    init_local_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"transactions": [], "goal": {"amount": 0}, "reminders": []}


def save_local_data(data: dict):
    """Salva dados no arquivo JSON local"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =============================================================================
# Funcoes Supabase (com user_id)
# =============================================================================

def load_transactions_supabase(client: "Client", user_id: str) -> list:
    """Carrega transacoes do usuario"""
    try:
        response = client.table("transactions").select("*").eq("user_id", user_id).execute()
        return response.data or []
    except Exception as e:
        st.error(f"Erro ao carregar transacoes: {e}")
        return []


def save_transaction_supabase(client: "Client", transaction: dict, user_id: str):
    """Salva transacao do usuario"""
    try:
        transaction["user_id"] = user_id
        client.table("transactions").upsert(transaction).execute()
    except Exception as e:
        st.error(f"Erro ao salvar transacao: {e}")


def delete_transaction_supabase(client: "Client", transaction_id: str, user_id: str):
    """Remove transacao do usuario"""
    try:
        client.table("transactions").delete().eq("id", transaction_id).eq("user_id", user_id).execute()
    except Exception as e:
        st.error(f"Erro ao excluir transacao: {e}")


def load_goal_supabase(client: "Client", user_id: str) -> dict:
    """Carrega meta do usuario"""
    try:
        response = client.table("goals").select("*").eq("user_id", user_id).limit(1).execute()
        if response.data:
            return response.data[0]
        return {"id": user_id, "user_id": user_id, "amount": 0}
    except Exception as e:
        st.error(f"Erro ao carregar meta: {e}")
        return {"id": user_id, "user_id": user_id, "amount": 0}


def save_goal_supabase(client: "Client", goal: dict, user_id: str):
    """Salva meta do usuario"""
    try:
        goal["id"] = user_id  # Usa user_id como ID para ter uma meta por usuario
        goal["user_id"] = user_id
        client.table("goals").upsert(goal).execute()
    except Exception as e:
        st.error(f"Erro ao salvar meta: {e}")


def load_reminders_supabase(client: "Client", user_id: str) -> list:
    """Carrega lembretes do usuario"""
    try:
        response = client.table("reminders").select("*").eq("user_id", user_id).execute()
        return response.data or []
    except Exception as e:
        st.error(f"Erro ao carregar lembretes: {e}")
        return []


def save_reminder_supabase(client: "Client", reminder: dict, user_id: str):
    """Salva lembrete do usuario"""
    try:
        reminder["user_id"] = user_id
        client.table("reminders").upsert(reminder).execute()
    except Exception as e:
        st.error(f"Erro ao salvar lembrete: {e}")


def delete_reminder_supabase(client: "Client", reminder_id: str, user_id: str):
    """Remove lembrete do usuario"""
    try:
        client.table("reminders").delete().eq("id", reminder_id).eq("user_id", user_id).execute()
    except Exception as e:
        st.error(f"Erro ao excluir lembrete: {e}")


# =============================================================================
# Interface Unificada
# =============================================================================

class Database:
    """Classe unificada para acesso ao banco de dados"""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.is_cloud = self.client is not None
        
        if not self.is_cloud:
            init_local_data()
    
    def get_mode(self) -> str:
        """Retorna modo atual: 'cloud' ou 'local'"""
        return "cloud" if self.is_cloud else "local"
    
    def get_client(self):
        """Retorna cliente Supabase"""
        return self.client
    
    # Autenticacao
    def sign_up(self, email: str, password: str) -> dict:
        if not self.is_cloud:
            return {"success": False, "error": "Modo local nao suporta autenticacao"}
        return sign_up(self.client, email, password)
    
    def sign_in(self, email: str, password: str) -> dict:
        if not self.is_cloud:
            return {"success": False, "error": "Modo local nao suporta autenticacao"}
        return sign_in(self.client, email, password)
    
    def sign_out(self):
        if self.is_cloud:
            sign_out(self.client)
        st.session_state.pop("user", None)
    
    # Transacoes
    def load_transactions(self) -> list:
        if self.is_cloud:
            user_id = get_user_id()
            if user_id:
                return load_transactions_supabase(self.client, user_id)
            return []
        return load_local_data().get("transactions", [])
    
    def save_transaction(self, transaction: dict):
        if self.is_cloud:
            user_id = get_user_id()
            if user_id:
                save_transaction_supabase(self.client, transaction, user_id)
        else:
            data = load_local_data()
            existing = next((i for i, t in enumerate(data["transactions"]) if t["id"] == transaction["id"]), None)
            if existing is not None:
                data["transactions"][existing] = transaction
            else:
                data["transactions"].append(transaction)
            save_local_data(data)
    
    def delete_transaction(self, transaction_id: str):
        if self.is_cloud:
            user_id = get_user_id()
            if user_id:
                delete_transaction_supabase(self.client, transaction_id, user_id)
        else:
            data = load_local_data()
            data["transactions"] = [t for t in data["transactions"] if t["id"] != transaction_id]
            save_local_data(data)
    
    # Meta
    def load_goal(self) -> dict:
        if self.is_cloud:
            user_id = get_user_id()
            if user_id:
                return load_goal_supabase(self.client, user_id)
            return {"amount": 0}
        return load_local_data().get("goal", {"amount": 0})
    
    def save_goal(self, goal: dict):
        if self.is_cloud:
            user_id = get_user_id()
            if user_id:
                save_goal_supabase(self.client, goal, user_id)
        else:
            data = load_local_data()
            data["goal"] = goal
            save_local_data(data)
    
    # Lembretes
    def load_reminders(self) -> list:
        if self.is_cloud:
            user_id = get_user_id()
            if user_id:
                return load_reminders_supabase(self.client, user_id)
            return []
        return load_local_data().get("reminders", [])
    
    def save_reminder(self, reminder: dict):
        if self.is_cloud:
            user_id = get_user_id()
            if user_id:
                save_reminder_supabase(self.client, reminder, user_id)
        else:
            data = load_local_data()
            existing = next((i for i, r in enumerate(data["reminders"]) if r["id"] == reminder["id"]), None)
            if existing is not None:
                data["reminders"][existing] = reminder
            else:
                data["reminders"].append(reminder)
            save_local_data(data)
    
    def delete_reminder(self, reminder_id: str):
        if self.is_cloud:
            user_id = get_user_id()
            if user_id:
                delete_reminder_supabase(self.client, reminder_id, user_id)
        else:
            data = load_local_data()
            data["reminders"] = [r for r in data["reminders"] if r["id"] != reminder_id]
            save_local_data(data)


@st.cache_resource
def get_database() -> Database:
    """Retorna instancia do banco de dados (cached)"""
    return Database()
