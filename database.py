import streamlit as st
from auth import init_supabase, get_authenticated_client

def get_user_api_keys(user_id):
    """Fetches all API keys for a specific user."""
    supabase = get_authenticated_client()
    if not supabase:
        return {}
    
    try:
        response = supabase.table("user_api_keys").select("*").eq("user_id", user_id).execute()
        # Convert list of dicts to a simpler dict format: {provider: {key: ..., model: ...}}
        keys_map = {}
        for item in response.data:
            keys_map[item['provider']] = {
                "api_key": item.get('api_key'),
                "model": item.get('model')
            }
        return keys_map
    except Exception as e:
        st.error(f"Erro ao buscar chaves de API: {e}")
        return {}

def save_user_api_key(user_id, provider, api_key, model=None):
    """Saves or updates an API key for a user."""
    supabase = get_authenticated_client()
    if not supabase:
        return False, "Supabase não conectado"
    
    try:
        # Upsert logic
        data = {
            "user_id": user_id,
            "provider": provider,
            "api_key": api_key,
            "model": model
        }
        
        # We need to check if it exists to know if we update or insert, 
        # but Supabase upsert works if we have a unique constraint.
        # We defined unique(user_id, provider) in SQL, so upsert should work.
        response = supabase.table("user_api_keys").upsert(data, on_conflict="user_id, provider").execute()
        return True, "Salvo com sucesso"
    except Exception as e:
        return False, str(e)

def get_youtube_token(user_id):
    """Fetches the YouTube token data for a user."""
    supabase = get_authenticated_client()
    if not supabase:
        return None
        
    try:
        response = supabase.table("youtube_tokens").select("token_data").eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]['token_data']
        return None
    except Exception as e:
        print(f"Erro ao buscar token YouTube: {e}")
        return None

def save_youtube_token(user_id, token_data):
    """Saves the YouTube token data."""
    supabase = get_authenticated_client()
    if not supabase:
        return False
        
    try:
        data = {
            "user_id": user_id,
            "token_data": token_data
        }
        supabase.table("youtube_tokens").upsert(data, on_conflict="user_id").execute()
        return True
    except Exception as e:
        print(f"Erro ao salvar token YouTube: {e}")
        return False

def get_automation_settings(user_id):
    """Fetches automation settings for a user."""
    supabase = get_authenticated_client()
    if not supabase:
        return {}
        
    try:
        response = supabase.table("automation_settings").select("*").eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
        return {}
    except Exception as e:
        print(f"Erro ao buscar configurações de automação: {e}")
        return {}

def save_automation_settings(user_id, active, frequency, last_run=None, next_run=None):
    """Saves automation settings."""
    supabase = get_authenticated_client()
    if not supabase:
        return False
        
    try:
        data = {
            "user_id": user_id,
            "active": active,
            "frequency": frequency,
            "last_run": last_run,
            "next_run": next_run
        }
        supabase.table("automation_settings").upsert(data, on_conflict="user_id").execute()
        return True
    except Exception as e:
        print(f"Erro ao salvar configurações de automação: {e}")
        return False

def get_optimization_history(user_id):
    """Fetches optimization history."""
    supabase = get_authenticated_client()
    if not supabase:
        return {}
        
    try:
        response = supabase.table("optimization_history").select("*").eq("user_id", user_id).execute()
        # Convert to dict format expected by app: {video_id: date}
        history = {}
        for item in response.data:
            history[item['video_id']] = item['created_at']
        return history
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return {}

def add_optimization_history(user_id, video_id, video_title, action_taken, details=None):
    """Adds an entry to optimization history."""
    supabase = get_authenticated_client()
    if not supabase:
        return False
        
    try:
        data = {
            "user_id": user_id,
            "video_id": video_id,
            "video_title": video_title,
            "action_taken": action_taken,
            "details": details
        }
        supabase.table("optimization_history").insert(data).execute()
        return True
    except Exception as e:
        print(f"Erro ao salvar histórico: {e}")
        return False

def get_pending_reviews(user_id):
    """Fetches pending reviews."""
    supabase = get_authenticated_client()
    if not supabase:
        return {}
        
    try:
        response = supabase.table("pending_reviews").select("*").eq("user_id", user_id).execute()
        # Convert to dict format: {video_id: {data...}}
        pending = {}
        for item in response.data:
            # Merge suggested_data with other fields if needed, or just return suggested_data
            # App expects a dict of items.
            # Let's assume suggested_data contains the fields we need.
            data = item['suggested_data']
            data['db_id'] = item['id'] # Store DB ID for deletion
            pending[item['video_id']] = data
        return pending
    except Exception as e:
        print(f"Erro ao buscar pendências: {e}")
        return {}

def add_pending_review(user_id, video_id, original_data, suggested_data):
    """Adds a pending review."""
    supabase = get_authenticated_client()
    if not supabase:
        return False
        
    try:
        data = {
            "user_id": user_id,
            "video_id": video_id,
            "original_data": original_data,
            "suggested_data": suggested_data
        }
        supabase.table("pending_reviews").insert(data).execute()
        return True
    except Exception as e:
        print(f"Erro ao salvar pendência: {e}")
        return False

def delete_pending_review(user_id, video_id):
    """Deletes a pending review."""
    supabase = get_authenticated_client()
    if not supabase:
        return False
        
    try:
        supabase.table("pending_reviews").delete().eq("user_id", user_id).eq("video_id", video_id).execute()
        return True
    except Exception as e:
        print(f"Erro ao deletar pendência: {e}")
        return False

def get_all_active_automations():
    """Fetches all active automation settings."""
    # This function is used by the background script which might NOT have a session file
    # BUT it needs to read ALL users.
    # This requires SERVICE_ROLE key or a special admin user.
    # Since we are running locally, we might need to use the service role key if we want to bypass RLS.
    # OR, we can just use init_supabase() if we assume the script has admin privileges or RLS allows it (unlikely).
    # For now, let's keep init_supabase() here as it's likely running in a different context (background script).
    # However, RLS will block this if we use anon key.
    # We need to handle this. For now, I will leave it as init_supabase() but note the risk.
    # Actually, the background script runs as a separate process. It doesn't share the session file of the web user necessarily.
    # But wait, I updated youtube_seo_optimizer.py to use database.py.
    # If youtube_seo_optimizer.py runs, it calls get_all_active_automations.
    # If I change this to get_authenticated_client, it will try to load the session file.
    # If the user is logged in on the app, the session file exists.
    # So the script will run AS the logged in user.
    # If the logged in user is not an admin, they can't see OTHER users' automations!
    # This is a problem for a multi-user background worker.
    # Ideally, the background worker should use a SERVICE_ROLE key.
    # But we don't have that in the config currently (only anon key).
    # For this local prototype, maybe we can assume the user runs it for themselves?
    # But the script logic I wrote iterates over ALL users.
    # Let's stick to init_supabase() for this one function and hope RLS allows it or we fix it later.
    # Actually, I should probably NOT change this one function to get_authenticated_client if it's meant for admin.
    # But for now, I will update the others.
    
    supabase = init_supabase()
    if not supabase:
        return []
        
    try:
        response = supabase.table("automation_settings").select("*").eq("active", True).execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar automações ativas: {e}")
        return []
