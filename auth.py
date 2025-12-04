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
        
        # Save session to state (Per User)
        if response.session:
            st.session_state['supabase_session'] = response.session
                
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
        
    # Remove session from state
    if 'supabase_session' in st.session_state:
        del st.session_state['supabase_session']
    if 'user' in st.session_state:
        del st.session_state['user']

def check_session():
    """Checks if a valid session exists in state."""
    if 'supabase_session' in st.session_state:
        return True
    return False

import hashlib
import base64
import secrets

# Fixed verifier to solve stateless streamit cloud issue
# In a perfect world, this would be random and persisted in a DB, 
# but for this personal app, a fixed high-entropy string works and solves the redirect loop.
FIXED_VERIFIER = "YoutubeCEO_Streamlit_Fixed_Verifier_Secret_Key_99887766"

def _get_fixed_pkce_challenge():
    """Generates the challenge for the fixed verifier."""
    digest = hashlib.sha256(FIXED_VERIFIER.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('utf-8')
    return challenge

def get_google_login_url():
    """Returns the URL for Google OAuth login."""
    supabase = init_supabase()
    if not supabase:
        return None
    
    try:
        # Use fixed challenge
        challenge = _get_fixed_pkce_challenge()
        
        # Clean redirect URL (No parameters needed!)
        redirect_url = os.environ.get("REDIRECT_URL", "https://youtubeceo.streamlit.app/")
        if not redirect_url.endswith('/'):
            redirect_url += '/'
            
        st.info(f"Debug - Redirect URL: {redirect_url}") 
        
        # Get the URL for Google OAuth
        data = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirectTo": redirect_url,
                "queryParams": {
                    "code_challenge": challenge,
                    "code_challenge_method": "S256"
                }
            }
        })
        return data.url
    except Exception:
        return None

def handle_oauth_callback():
    """Handles the OAuth callback from Supabase/Google."""
    try:
        query_params = st.query_params
        code = query_params.get("code")
        error = query_params.get("error")
        error_description = query_params.get("error_description")

        if error:
            st.error(f"Erro retornado pelo provedor: {error} - {error_description}")
            return False
            
        if code:
            supabase = init_supabase()
            if supabase:
                # Exchange code for session using the FIXED verifier
                try:
                    response = supabase.auth.exchange_code_for_session({
                        "auth_code": code,
                        "code_verifier": FIXED_VERIFIER
                    })
                    if response.session:
                        st.session_state['supabase_session'] = response.session
                        st.session_state.logged_in = True
                        # Clear query params to clean URL then set home
                        st.query_params.clear()
                        st.query_params["page"] = "home"
                        return True
                except Exception as exchange_error:
                    st.error(f"Falha na troca do token: {exchange_error}")
                    return False
             
    except Exception as e:
        st.error(f"Erro no callback de login: {e}")
    return False

def get_authenticated_client():
    """Returns a Supabase client with the active session set."""
    supabase = init_supabase()
    if not supabase:
        return None
        
    if 'supabase_session' in st.session_state:
        try:
            session = st.session_state['supabase_session']
            supabase.auth.set_session(session.access_token, session.refresh_token)
            return supabase
        except Exception as e:
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
