import os
import json
import streamlit as st
from supabase import create_client, Client

# Config File
API_CONFIG_FILE = 'api_config.json'
SESSION_FILE = '.session'

def init_supabase():
    """Initialize Supabase client from config or env."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    # Try loading from config if not in env
    if not url or not key:
        # Check Streamlit Secrets (Cloud)
        if hasattr(st, "secrets"):
            try:
                url = st.secrets.get("SUPABASE_URL") or st.secrets.get("general", {}).get("SUPABASE_URL")
                key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("general", {}).get("SUPABASE_KEY")
            except:
                pass

    if not url or not key:
        if os.path.exists(API_CONFIG_FILE):
            try:
                with open(API_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    url = url or config.get("SUPABASE_URL")
                    key = key or config.get("SUPABASE_KEY")
            except:
                pass
    
    if url and key:
        try:
            return create_client(url, key)
        except Exception as e:
            st.error(f"Erro ao conectar com Supabase: {e}")
            return None
    return None

def is_configured():
    """Checks if Supabase credentials are available."""
    # Check env vars
    if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"):
        return True

    # Check Streamlit Secrets
    if hasattr(st, "secrets"):
        try:
             if (st.secrets.get("SUPABASE_URL") or st.secrets.get("general", {}).get("SUPABASE_URL")) and \
                (st.secrets.get("SUPABASE_KEY") or st.secrets.get("general", {}).get("SUPABASE_KEY")):
                 return True
        except:
            pass
        
    # Check file
    if os.path.exists(API_CONFIG_FILE):
        try:
            with open(API_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                if config.get("SUPABASE_URL") and config.get("SUPABASE_KEY"):
                    return True
        except:
            return False
    return False

def save_config(url, key):
    """Saves Supabase credentials to config file."""
    config = {}
    if os.path.exists(API_CONFIG_FILE):
        try:
            with open(API_CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except:
            pass
            
    config["SUPABASE_URL"] = url
    config["SUPABASE_KEY"] = key
    
    with open(API_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
        
    # Update env vars immediately
    os.environ["SUPABASE_URL"] = url
    os.environ["SUPABASE_KEY"] = key

def login_user(email, password):
    """Logs in a user with email and password."""
    supabase = init_supabase()
    if not supabase:
        return False, "Supabase não configurado."
    
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        # Save session to file
        if response.session:
            with open(SESSION_FILE, 'w') as f:
                f.write(response.session.model_dump_json())
                
        return True, response
    except Exception as e:
        return False, str(e)

def register_user(email, password):
    """Registers a new user."""
    supabase = init_supabase()
    if not supabase:
        return False, "Supabase não configurado."
    
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return True, response
    except Exception as e:
        return False, str(e)

def logout_user():
    """Logs out the current user."""
    supabase = init_supabase()
    if supabase:
        supabase.auth.sign_out()
        
    # Remove session file
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def check_session():
    """Checks if a valid session exists and restores it."""
    if not os.path.exists(SESSION_FILE):
        return False
        
    supabase = init_supabase()
    if not supabase:
        return False
        
    try:
        with open(SESSION_FILE, 'r') as f:
            session_data = json.load(f)
            
        # Restore session
        # Supabase python client doesn't have a direct 'set_session' that takes the full object easily 
        # without using the internal gotrue client, but we can try setting the access token if needed
        # or just verify if the token is still valid.
        # However, the standard way is usually to just rely on the client handling it if we could inject it,
        # but here we might just want to return True if we have a file, 
        # assuming the token is valid for now (or validate it).
        
        # Better approach: Use set_session with refresh_token if available
        if 'refresh_token' in session_data:
             res = supabase.auth.refresh_session(session_data['refresh_token'])
             if res.session:
                 # Update session file with new token
                 with open(SESSION_FILE, 'w') as f:
                    f.write(res.session.model_dump_json())
                 return True
        
        return False
    except Exception:
        return False

def get_google_login_url():
    """Returns the URL for Google OAuth login."""
    supabase = init_supabase()
    if not supabase:
        return None
    
    try:
        # Get the URL for Google OAuth
        data = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirectTo": os.environ.get("REDIRECT_URL", "http://localhost:8501")
            }
        })
        return data.url
    except Exception:
        return None

def get_authenticated_client():
    """Returns a Supabase client with the active session set."""
    supabase = init_supabase()
    if not supabase:
        return None
        
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                session_data = json.load(f)
            
            if 'access_token' in session_data and 'refresh_token' in session_data:
                supabase.auth.set_session(session_data['access_token'], session_data['refresh_token'])
                return supabase
        except Exception as e:
            # print(f"Error restoring session: {e}")
            pass
    return None

def get_current_user():
    """Returns the current authenticated user or None."""
    # Use authenticated client to ensure we have the session
    supabase = get_authenticated_client()
    if not supabase:
        return None
    
    try:
        user = supabase.auth.get_user()
        return user.user
    except:
        return None
