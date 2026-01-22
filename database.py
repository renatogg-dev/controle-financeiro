"""
Modulo de conexao com Supabase para persistencia de dados.
Suporta fallback para arquivo JSON local quando Supabase nao esta configurado.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime

# Tenta importar supabase, se falhar usa modo local
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
# Funcoes para Supabase
# =============================================================================

def load_transactions_supabase(client: "Client") -> list:
    """Carrega transacoes do Supabase"""
    try:
        response = client.table("transactions").select("*").execute()
        return response.data or []
    except Exception as e:
        st.error(f"Erro ao carregar transacoes: {e}")
        return []


def save_transaction_supabase(client: "Client", transaction: dict):
    """Salva ou atualiza transacao no Supabase"""
    try:
        # Upsert - insere ou atualiza se existir
        client.table("transactions").upsert(transaction).execute()
    except Exception as e:
        st.error(f"Erro ao salvar transacao: {e}")


def delete_transaction_supabase(client: "Client", transaction_id: str):
    """Remove transacao do Supabase"""
    try:
        client.table("transactions").delete().eq("id", transaction_id).execute()
    except Exception as e:
        st.error(f"Erro ao excluir transacao: {e}")


def load_goal_supabase(client: "Client") -> dict:
    """Carrega meta do Supabase"""
    try:
        response = client.table("goals").select("*").limit(1).execute()
        if response.data:
            return response.data[0]
        return {"id": "default", "amount": 0}
    except Exception as e:
        st.error(f"Erro ao carregar meta: {e}")
        return {"id": "default", "amount": 0}


def save_goal_supabase(client: "Client", goal: dict):
    """Salva meta no Supabase"""
    try:
        goal["id"] = "default"  # Sempre usa mesmo ID para ter apenas uma meta
        client.table("goals").upsert(goal).execute()
    except Exception as e:
        st.error(f"Erro ao salvar meta: {e}")


def load_reminders_supabase(client: "Client") -> list:
    """Carrega lembretes do Supabase"""
    try:
        response = client.table("reminders").select("*").execute()
        return response.data or []
    except Exception as e:
        st.error(f"Erro ao carregar lembretes: {e}")
        return []


def save_reminder_supabase(client: "Client", reminder: dict):
    """Salva lembrete no Supabase"""
    try:
        client.table("reminders").upsert(reminder).execute()
    except Exception as e:
        st.error(f"Erro ao salvar lembrete: {e}")


def delete_reminder_supabase(client: "Client", reminder_id: str):
    """Remove lembrete do Supabase"""
    try:
        client.table("reminders").delete().eq("id", reminder_id).execute()
    except Exception as e:
        st.error(f"Erro ao excluir lembrete: {e}")


# =============================================================================
# Interface Unificada (detecta automaticamente Supabase ou Local)
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
    
    # Transacoes
    def load_transactions(self) -> list:
        if self.is_cloud:
            return load_transactions_supabase(self.client)
        return load_local_data().get("transactions", [])
    
    def save_transaction(self, transaction: dict):
        if self.is_cloud:
            save_transaction_supabase(self.client, transaction)
        else:
            data = load_local_data()
            # Verifica se e update ou insert
            existing = next((i for i, t in enumerate(data["transactions"]) if t["id"] == transaction["id"]), None)
            if existing is not None:
                data["transactions"][existing] = transaction
            else:
                data["transactions"].append(transaction)
            save_local_data(data)
    
    def delete_transaction(self, transaction_id: str):
        if self.is_cloud:
            delete_transaction_supabase(self.client, transaction_id)
        else:
            data = load_local_data()
            data["transactions"] = [t for t in data["transactions"] if t["id"] != transaction_id]
            save_local_data(data)
    
    # Meta
    def load_goal(self) -> dict:
        if self.is_cloud:
            return load_goal_supabase(self.client)
        return load_local_data().get("goal", {"amount": 0})
    
    def save_goal(self, goal: dict):
        if self.is_cloud:
            save_goal_supabase(self.client, goal)
        else:
            data = load_local_data()
            data["goal"] = goal
            save_local_data(data)
    
    # Lembretes
    def load_reminders(self) -> list:
        if self.is_cloud:
            return load_reminders_supabase(self.client)
        return load_local_data().get("reminders", [])
    
    def save_reminder(self, reminder: dict):
        if self.is_cloud:
            save_reminder_supabase(self.client, reminder)
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
            delete_reminder_supabase(self.client, reminder_id)
        else:
            data = load_local_data()
            data["reminders"] = [r for r in data["reminders"] if r["id"] != reminder_id]
            save_local_data(data)


@st.cache_resource
def get_database() -> Database:
    """Retorna instancia do banco de dados (cached)"""
    return Database()
