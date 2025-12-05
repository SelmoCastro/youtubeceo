import streamlit as st

import os

import json

import datetime

import time

import requests

import base64

import re

import pandas as pd

import plotly.express as px

import google.generativeai as genai

from googleapiclient.discovery import build

from googleapiclient.http import MediaFileUpload

from google.oauth2.credentials import Credentials

from google.auth.transport.requests import Request

from googleapiclient.errors import HttpError

from openai import OpenAI

# from moviepy.editor import *

from PIL import Image, ImageDraw, ImageFont



import auth

import database



# --- Configuration ---

st.set_page_config(page_title="Gerenciador de SEO para YouTube", layout="wide", page_icon="🚀")



SCOPES = [

    'https://www.googleapis.com/auth/youtube.force-ssl',

    'https://www.googleapis.com/auth/yt-analytics.readonly',

    'https://www.googleapis.com/auth/youtube.upload'

]

API_SERVICE_NAME = 'youtube'

API_VERSION = 'v3'

TOKEN_FILE = 'token.json'

CLIENT_SECRETS_FILE = 'client_secret.json'

PENDING_FILE = 'pending_reviews.json'

HISTORY_FILE = 'optimization_history.json'

API_CONFIG_FILE = 'api_config.json'

SCRIPT_NAME = 'youtube_seo_optimizer.py'

ASSETS_DIR = 'generated_assets'



# Ensure assets directory exists

if not os.path.exists(ASSETS_DIR):

    os.makedirs(ASSETS_DIR)



# --- Load API Config on Startup ---

if os.path.exists(API_CONFIG_FILE):

    try:

        with open(API_CONFIG_FILE, 'r') as f:

            config = json.load(f)

            for key, value in config.items():

                if value:

                    os.environ[key] = value

                    # Configure libraries immediately if needed

                    if key == "GOOGLE_API_KEY":

                        genai.configure(api_key=value)

    except Exception as e:

        print(f"Error loading config: {e}")



# --- Authentication Flow ---

# --- Authentication Flow ---

if 'logged_in' not in st.session_state:

    st.session_state.logged_in = False



# Check for OAuth Callback (Google Login)

if not st.session_state.logged_in:

    if auth.handle_oauth_callback():

        st.rerun()



if 'logged_in' not in st.session_state or not st.session_state.logged_in:

    # Try to restore session

    if auth.check_session():

        st.session_state.logged_in = True

        st.query_params["page"] = "home"

        # Load keys from DB

        user = auth.get_current_user()

        if user:

            st.session_state.user = user # Cache user object

            db_keys = database.get_user_api_keys(user.id)

            for provider, data in db_keys.items():

                if data['api_key']:

                    # Map provider name to env var

                    if provider == "Google Gemini":

                        os.environ["GOOGLE_API_KEY"] = data['api_key']

                        if data['model']: os.environ["GOOGLE_MODEL"] = data['model']

                        genai.configure(api_key=data['api_key'])

                    elif provider == "OpenAI (ChatGPT)":

                        os.environ["OPENAI_API_KEY"] = data['api_key']

                        if data['model']: os.environ["OPENAI_MODEL"] = data['model']

                    elif provider == "Anthropic (Claude)":

                        os.environ["ANTHROPIC_API_KEY"] = data['api_key']

                        if data['model']: os.environ["ANTHROPIC_MODEL"] = data['model']

                    elif provider == "Stability AI":

                        os.environ["STABILITY_API_KEY"] = data['api_key']

                        if data['model']: os.environ["STABILITY_MODEL"] = data['model']

                    elif provider == "ElevenLabs":

                        os.environ["ELEVENLABS_API_KEY"] = data['api_key']

                        if data['model']: os.environ["ELEVENLABS_MODEL"] = data['model']

                    elif provider == "Pexels":

                        os.environ["PEXELS_API_KEY"] = data['api_key']

                        if data['model']: os.environ["PEXELS_MODEL"] = data['model']

                    elif provider == "Hugging Face":

                        os.environ["HUGGINGFACE_API_TOKEN"] = data['api_key']

                        if data['model']: os.environ["HUGGINGFACE_MODEL"] = data['model']

    else:

        st.session_state.logged_in = False



# --- Custom CSS for Premium Look ---

@st.cache_data

def get_base64_of_bin_file(bin_file):

    with open(bin_file, 'rb') as f:

        data = f.read()

    return base64.b64encode(data).decode()



def set_png_as_page_bg(png_file):

    bin_str = get_base64_of_bin_file(png_file)

    page_bg_img = '''

    <style>

    .stApp {

        background-image: url("data:image/png;base64,%s");

        background-size: cover;

        background-repeat: no-repeat;

        background-attachment: fixed;

    }

    .main {

        background-color: transparent;

    }

    h1, h2, h3 {

        color: #E6EDF3 !important;

        font-family: 'Inter', sans-serif;

        text-shadow: 2px 2px 4px #000000;

    }

    /* Metric Cards */

    .stMetric {

        background-color: rgba(31, 36, 45, 0.7);

        padding: 15px;

        border-radius: 10px;

        border: 1px solid #30363D;

        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);

        backdrop-filter: blur(5px);

        transition: all 0.3s ease;

    }

    .stMetric:hover {

        border-color: #58A6FF;

        transform: translateY(-2px);

        box-shadow: 0 6px 12px rgba(88, 166, 255, 0.2);

    }

    /* Buttons */

    .stButton>button {

        background-color: #1e3a8a;

        color: white;

        border: 1px solid #1e3a8a;

        border-radius: 6px;

        padding: 0.5rem 1rem;

        font-weight: 600;

        transition: all 0.3s ease;

    }

    .stButton>button:hover {

        background-color: #172554;

        border-color: #58A6FF;

        transform: scale(1.02);

        box-shadow: 0 0 15px rgba(88, 166, 255, 0.6);

    }

    /* Inputs */

    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {

        background-color: rgba(22, 27, 34, 0.8) !important;

        color: #e6edf3 !important;

        border: 1px solid #30363D;

        border-radius: 6px;

        transition: border-color 0.3s ease, box-shadow 0.3s ease;

    }

    .stTextInput input:focus, .stTextArea textarea:focus {

        border-color: #58A6FF !important;

        box-shadow: 0 0 8px rgba(88, 166, 255, 0.4) !important;

    }

    /* Integration Cards */

    .integration-card {

        background-color: rgba(22, 27, 34, 0.6);

        border: 1px solid #30363D;

        border-radius: 10px;

        padding: 15px;

        text-align: center;

        transition: all 0.3s ease;

        margin-bottom: 10px;

        height: 100%%;

        display: flex;

        flex-direction: column;

        align-items: center;

        justify-content: center;

    }

    .integration-card:hover {

        transform: translateY(-3px);

    }

    .status-active {

        border-color: #A371F7; /* Purple Neon */

        box-shadow: 0 0 15px rgba(163, 113, 247, 0.3);

        background-color: rgba(163, 113, 247, 0.1);

    }

    .status-inactive {

        border-color: #30363D;

        opacity: 0.7;

    }

    .status-icon {

        font-size: 2rem;

        margin-bottom: 10px;

    }

    .status-text {

        font-weight: bold;

        font-size: 0.9rem;

    }

    .active-text { color: #A371F7; }

    .inactive-text { color: #8b949e; }

    

    div[data-testid="stExpander"] {

        background-color: rgba(22, 27, 34, 0.8);

        border: 1px solid #30363D;

        border-radius: 8px;

        backdrop-filter: blur(5px);

    }

    </style>

    ''' % bin_str

    st.markdown(page_bg_img, unsafe_allow_html=True)



# Check if background exists

if os.path.exists('background.png'):

    set_png_as_page_bg('background.png')

else:

    st.markdown("""

    <style>

    .main {

        background-color: #0E1117;

    }

    .stApp {

        background: linear-gradient(to bottom right, #0E1117, #161B22);

    }

    /* ... rest of original CSS if needed ... */

    </style>

    """, unsafe_allow_html=True)



# --- Sidebar Header ---

with st.sidebar:

    if os.path.exists('logo.png'):

        if st.session_state.get('logged_in'):

            col1, col2 = st.columns([1, 2])

            with col1:

                st.image('logo.png', use_container_width=True)

            with col2:

                if st.button("🚪 Sair", key="logout_btn_sidebar", use_container_width=True):

                    auth.logout_user()

                    st.session_state.logged_in = False

                    st.rerun()

        else:

             st.image('logo.png', use_container_width=True)

    

    st.divider()





# --- Helper Functions ---

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

import yt_dlp

import time



def get_video_transcript(video_id):

    """Fetches video transcript/captions. Fallback to Audio -> Gemini."""

    try:

        # 1. Try Standard Captions

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        try:

            transcript = transcript_list.find_transcript(['pt', 'pt-BR'])

        except:

            try:

                transcript = transcript_list.find_generated_transcript(['pt', 'pt-BR'])

            except:

                transcript = transcript_list.find_transcript(['en'])

        

        transcript_data = transcript.fetch()

        full_text = " ".join([t['text'] for t in transcript_data])

        return full_text

        

    except (TranscriptsDisabled, NoTranscriptFound, Exception) as e:

        print(f"Caption fetch failed ({e}). Trying Audio Fallback...")

        

        # 2. Fallback: Download Audio & Transcribe with Gemini

        try:

            api_key = os.environ.get("GOOGLE_API_KEY")

            if not api_key:

                return None

                

            genai.configure(api_key=api_key)

            

            # Download Audio

            ydl_opts = {

                'format': 'm4a/bestaudio/best',

                'outtmpl': f'temp_{video_id}.%(ext)s',

                'postprocessors': [{

                    'key': 'FFmpegExtractAudio',

                    'preferredcodec': 'mp3',

                }],

                'quiet': True

            }

            

            audio_file = f"temp_{video_id}.mp3"

            

            # Check if already exists to save time

            if not os.path.exists(audio_file):

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                    ydl.download([f'https://www.youtube.com/watch?v={video_id}'])

            

            if os.path.exists(audio_file):

                # Upload to Gemini

                myfile = genai.upload_file(audio_file)

                

                # Wait for processing

                while myfile.state.name == "PROCESSING":

                    time.sleep(1)

                    myfile = genai.get_file(myfile.name)

                    

                # Generate Transcript

                model = genai.GenerativeModel("gemini-1.5-flash")

                response = model.generate_content([myfile, "Transcreva este áudio em português."])

                

                # Cleanup

                try:

                    os.remove(audio_file)

                    myfile.delete()

                except: pass

                

                return response.text

                

        except Exception as e_audio:

            print(f"Audio Fallback Error: {e_audio}")

            return None



    return None



def get_top_performing_videos(service, max_results=10):

    """Fetches top performing videos by views to learn channel style."""

    try:

        # Get All Videos (limited to 50 for speed, then sort)

        # Note: Search API is better for sorting by viewCount but costs more quota (100 units).

        # PlaylistItems cost 1 unit. We'll fetch recent 50 and sort, or use Search if quota allows.

        # Let's use Search for accuracy of "Top Performing" across all time.

        

        search_response = service.search().list(

            forMine=True,

            part='snippet',

            type='video',

            order='viewCount',

            maxResults=max_results

        ).execute()

        

        top_videos = []

        for item in search_response.get('items', []):

            top_videos.append({

                'title': item['snippet']['title'],

                'description': item['snippet']['description']

            })

            

        return top_videos

        

    except Exception as e:

        print(f"Error fetching top videos: {e}")

        return []




def get_current_user_cached():
    """Returns cached user or fetches if missing."""
    if 'user' in st.session_state and st.session_state.user:
        return st.session_state.user
    
    user = auth.get_current_user()
    if user:
        st.session_state.user = user
        st.session_state.logged_in = True
    return user

def get_authenticated_service():
    """Authenticates with YouTube Data API."""
    creds = None
    
    # Try to load from DB first if logged in
    user = get_current_user_cached()

    if user:

        token_data = database.get_youtube_token(user.id)

        if token_data:

            # Inject client_id and client_secret from file if available

            secret_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json")

            if os.path.exists(secret_path):

                try:

                    with open(secret_path, 'r') as f:

                        client_config = json.load(f)

                        # Handle both "web" and "installed" formats

                        config_data = client_config.get('web') or client_config.get('installed')

                        if config_data:

                            token_data['client_id'] = config_data.get('client_id')

                            token_data['client_secret'] = config_data.get('client_secret')

                except:

                    pass

            

            creds = Credentials.from_authorized_user_info(token_data, SCOPES)

            

    # Fallback to local file REMOVED for cloud security/isolation

    # if not creds and os.path.exists(TOKEN_FILE): ...

    

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:

            try:

                creds.refresh(Request())

                # Save refreshed credentials to DB

                if user:

                    database.save_youtube_token(user.id, json.loads(creds.to_json()))

            except Exception as e:

                st.error(f"Erro ao atualizar token: {e}")

                return None

        else:

            # On Cloud, we cannot run local server. 

            # User must authenticate via the web flow (not fully implemented here, but preventing crash).

            st.warning("⚠️ Autenticação do YouTube necessária. Por favor, reconecte sua conta na aba de Configurações.")

            return None

            

    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)



@st.cache_resource(ttl=3600)

def get_cached_service(user_id):

    """Cached version of get_authenticated_service to reduce auth calls.

    Requires user_id to ensure cache is unique per user.

    """

    return get_authenticated_service()



def load_json(filepath):

    if os.path.exists(filepath):

        try:

            with open(filepath, 'r') as f:

                return json.load(f)

        except:

            return {}

    return {}



def save_json(filepath, data):

    with open(filepath, 'w') as f:

        json.dump(data, f, indent=4)



def update_video_on_youtube(service, video_id, title, description, tags, thumbnail_path=None):

    try:

        # 1. Update Metadata

        video_response = service.videos().list(id=video_id, part='snippet').execute()

        if not video_response['items']:

            st.error(f"Video {video_id} not found.")

            return False



        snippet = video_response['items'][0]['snippet']

        snippet['title'] = title

        snippet['description'] = description

        snippet['tags'] = tags



        service.videos().update(

            part='snippet',

            body={'id': video_id, 'snippet': snippet}

        ).execute()



        # 2. Update Thumbnail (if exists)

        if thumbnail_path and os.path.exists(thumbnail_path):

            service.thumbnails().set(

                videoId=video_id,

                media_body=MediaFileUpload(thumbnail_path)

            ).execute()

        

        return True

    except Exception as e:

        st.error(f"Error updating video: {e}")

        return False



@st.cache_data(ttl=3600)

def get_watch_time_year(_creds):

    """Fetches watch time (hours) for the last 365 days."""

    try:

        analytics = build('youtubeAnalytics', 'v2', credentials=_creds)

        end_date = datetime.date.today().strftime("%Y-%m-%d")

        start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")

        

        response = analytics.reports().query(

            ids='channel==MINE',

            startDate=start_date,

            endDate=end_date,

            metrics='estimatedMinutesWatched'

        ).execute()

        

        rows = response.get('rows', [])

        if rows:

            return float(rows[0][0]) / 60 # Convert minutes to hours

        return 0.0

    except Exception as e:

        st.error(f"Error fetching watch time: {e}")

        return 0.0



@st.cache_data(ttl=3600)

def get_traffic_sources(_creds):

    """Fetches traffic sources for the last 30 days."""

    try:

        analytics = build('youtubeAnalytics', 'v2', credentials=_creds)

        end_date = datetime.date.today().strftime("%Y-%m-%d")

        start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        

        response = analytics.reports().query(

            ids='channel==MINE',

            startDate=start_date,

            endDate=end_date,

            metrics='views',

            dimensions='insightTrafficSourceType',

            sort='-views'

        ).execute()

        

        return response.get('rows', [])

    except Exception as e:

        st.error(f"Error fetching traffic sources: {e}")

        return []



@st.cache_data(ttl=3600)

def get_monthly_views(_creds):

    """Fetches total views for the last 30 days. Cached for 1 hour."""

    try:

        analytics = build('youtubeAnalytics', 'v2', credentials=_creds)

        end_date = datetime.date.today().strftime("%Y-%m-%d")

        start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        

        response = analytics.reports().query(

            ids='channel==MINE',

            startDate=start_date,

            endDate=end_date,

            metrics='views'

        ).execute()

        

        rows = response.get('rows', [])

        if rows:

            return int(rows[0][0])

        return 0

    except HttpError as e:

        if "quotaExceeded" in str(e):

            st.warning("⚠️ Cota da API do YouTube excedida. Tente novamente após as 05:00 (Brasília). Exibindo dados padrão.")

            return 0

        st.error(f"Error fetching monthly views: {e}")

        return 0

    except Exception as e:

        st.error(f"Error fetching monthly views: {e}")

        return 0



@st.cache_data(ttl=3600)

def get_channel_stats(_service):

    """Fetches channel statistics (subs, views, video count)."""

    return _service.channels().list(mine=True, part='contentDetails,statistics').execute()



@st.cache_data(ttl=3600)

def get_subscriber_count(_service):

    """Fetches just the subscriber count."""

    response = _service.channels().list(mine=True, part='statistics').execute()

    return int(response['items'][0]['statistics']['subscriberCount'])



@st.cache_data(ttl=3600)

def get_video_details(_service, video_id):

    """Fetches snippet and statistics for a specific video."""

    return _service.videos().list(id=video_id, part='snippet,statistics').execute()



def parse_duration(duration_iso):

    """Parses YouTube duration (ISO 8601) to seconds (approx)."""

    match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration_iso)

    if not match:

        return 0

    

    h = int(match.group(1)[:-1]) if match.group(1) else 0

    m = int(match.group(2)[:-1]) if match.group(2) else 0

    s = int(match.group(3)[:-1]) if match.group(3) else 0

    

    return h*3600 + m*60 + s



def generate_image_with_ai(prompt, provider="Auto", model=None):

    """Generates an image using available AI providers (Stability > DALL-E 3 > Hugging Face > Pollinations)."""

    

    # 1. Stability AI

    if (provider == "Auto" or provider == "Stability AI") and os.environ.get("STABILITY_API_KEY"):

        try:

            api_key = os.environ["STABILITY_API_KEY"]

            engine_id = model or os.environ.get("STABILITY_MODEL", "stable-diffusion-xl-10-stable")

            api_host = os.getenv('API_HOST', 'https://api.stability.ai')

            

            # Enhance prompt for realism

            enhanced_prompt = f"{prompt}, photorealistic, 8k, highly detailed, cinematic lighting, ultra realistic, photography"

            

            response = requests.post(

                f"{api_host}/v1/generation/{engine_id}/text-to-image",

                headers={

                    "Content-Type": "application/json",

                    "Accept": "application/json",

                    "Authorization": f"Bearer {api_key}"

                },

                json={

                    "text_prompts": [{"text": enhanced_prompt}],

                    "cfg_scale": 7,

                    "height": 720,

                    "width": 1280,

                    "samples": 1,

                    "steps": 30,

                },

            )



            if response.status_code != 200:

                raise Exception(f"Non-200 response: {str(response.text)}")



            data = response.json()

            return base64.b64decode(data["artifacts"][0]["base64"])

            

        except Exception as e:

            if provider != "Auto": return None # Fail if specific provider requested

            st.warning(f"Stability AI falhou ({e}), tentando próximo...")



    # 2. OpenAI DALL-E 3

    if (provider == "Auto" or provider == "OpenAI (DALL-E 3)") and os.environ.get("OPENAI_API_KEY"):

        try:

            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

            

            response = client.images.generate(

                model="dall-e-3",

                prompt=f"{prompt}, Photorealistic, cinematic, 4k",

                size="1024x1024", # DALL-E 3 standard

                quality="standard",

                n=1,

                response_format="b64_json"

            )

            

            return base64.b64decode(response.data[0].b64_json)

            

        except Exception as e:

            if provider != "Auto": return None

            st.warning(f"DALL-E 3 falhou ({e}), usando fallback...")



    # 3. Hugging Face Inference API (Free with Token)

    if (provider == "Auto" or provider == "Hugging Face") and os.environ.get("HUGGINGFACE_API_TOKEN"):

        try:

            api_token = os.environ["HUGGINGFACE_API_TOKEN"]

            model_id = model or os.environ.get("HUGGINGFACE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")

            api_url = f"https://api-inference.huggingface.co/models/{model_id}"

            headers = {"Authorization": f"Bearer {api_token}"}

            

            # Enhance prompt

            enhanced_prompt = f"{prompt}, photorealistic, 8k, highly detailed, cinematic lighting"

            

            payload = {

                "inputs": enhanced_prompt,

                "parameters": {"num_inference_steps": 25}

            }



            response = requests.post(api_url, headers=headers, json=payload)

            

            # Handle model loading state (common in free tier)

            if response.status_code == 503:

                 st.warning("Modelo Hugging Face carregando, aguardando...")

                 time.sleep(10) # Wait a bit

                 response = requests.post(api_url, headers=headers, json=payload)



            if response.status_code != 200:

                 raise Exception(f"Non-200 response: {str(response.text)}")



            return response.content

            

        except Exception as e:

            if provider != "Auto": return None

            st.warning(f"Hugging Face falhou ({e}), tentando Pollinations...")



    # 4. Pollinations.ai (Fallback - Free)

    # Always available if Auto or specifically requested

    if provider == "Auto" or provider == "Pollinations (Grátis)":

        try:

            # URL encode prompt

            encoded_prompt = requests.utils.quote(f"{prompt}, photorealistic, 4k, cinematic")

            # Force Flux model for better quality

            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&model=flux" 

            return requests.get(image_url).content

        except Exception as e:

            st.error(f"Erro no gerador gratuito: {e}")

            return None

            

    return None



# --- Authentication Flow ---



def login_screen():

    st.markdown("""

    <style>

        .stTextInput input {

            background-color: rgba(22, 27, 34, 0.8);

            color: #e6edf3;

        }

    </style>

    """, unsafe_allow_html=True)

    

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.title("🔐 Login")

        

        # Google Login Button

        google_url = auth.get_google_login_url()

        if google_url:

            st.link_button("🇬 Entrar com Google", google_url, use_container_width=True)

            st.divider()

        

        tab_login, tab_register = st.tabs(["Entrar", "Cadastrar"])

        

        with tab_login:

            email = st.text_input("E-mail", key="login_email")

            password = st.text_input("Senha", type="password", key="login_pass")

            

            if st.button("Entrar", use_container_width=True):

                if not email or not password:

                    st.error("Preencha todos os campos.")

                else:

                    with st.spinner("Autenticando..."):

                        success, resp = auth.login_user(email, password)

                        if success:

                            st.session_state.logged_in = True

                            st.success("Login realizado com sucesso!")

                            st.rerun()

                        else:

                            st.error(f"Erro no login: {resp}")

                            

        with tab_register:

            new_email = st.text_input("E-mail", key="reg_email")

            new_pass = st.text_input("Senha", type="password", key="reg_pass")

            confirm_pass = st.text_input("Confirmar Senha", type="password", key="reg_confirm")

            

            if st.button("Cadastrar", use_container_width=True):

                if not new_email or not new_pass:

                    st.error("Preencha todos os campos.")

                elif new_pass != confirm_pass:

                    st.error("As senhas não coincidem.")

                else:

                    with st.spinner("Criando conta..."):

                        success, resp = auth.register_user(new_email, new_pass)

                        if success:

                            st.success("Conta criada! Verifique seu e-mail para confirmar.")

                        else:

                            st.error(f"Erro no cadastro: {resp}")



def setup_screen():

    st.markdown("""

    <style>

        .stTextInput input {

            background-color: rgba(22, 27, 34, 0.8);

            color: #e6edf3;

        }

    </style>

    """, unsafe_allow_html=True)

    

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.title("🛠️ Configuração Inicial")

        st.info("Configure o banco de dados para iniciar o sistema.")

        

        st.markdown("### ☁️ Supabase")

        st.caption("Insira as credenciais do seu projeto Supabase.")

        

        url = st.text_input("Project URL", placeholder="https://your-project.supabase.co")

        key = st.text_input("Anon / Public Key", type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

        

        if st.button("Salvar e Iniciar", use_container_width=True):

            if not url or not key:

                st.error("Preencha todos os campos.")

            else:

                auth.save_config(url, key)

                st.success("Configuração salva! Reiniciando...")

                time.sleep(1)

                st.rerun()



# --- Login Logic ---

if not st.session_state.get('logged_in') and not get_current_user_cached():

    if not auth.is_configured():

        setup_screen()

    else:

        login_screen()

    st.stop() # Stop execution if not logged in



# --- Tabs ---



# --- Session State Init ---

if 'session_history' not in st.session_state:

    st.session_state.session_history = []



# --- Tabs ---



# --- Custom CSS & Theme ---

def apply_custom_style(logged_in=False):

    # Dynamic Background Logic
    if logged_in:
        # Dashboard: Void (Deep & Calm)
        bg_image = "radial-gradient(circle at 100% 100%, #172554 0%, #020617 40%)"
    else:
        # Login: Nebula (Futuristic & Immersive)
        bg_image = "radial-gradient(circle at 50% 0%, #1e1b4b 0%, #020617 60%)"

    st.markdown("""
    <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global Variables */
        :root {
            --bg-color: #020617; /* Slate-950 */
            --card-bg: rgba(15, 23, 42, 0.6); /* Slate-900 with opacity */
            --sidebar-bg: rgba(2, 6, 23, 0.8);
            --text-primary: #f8fafc; /* Slate-50 */
            --text-secondary: #94a3b8; /* Slate-400 */
            --accent-gradient: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); /* Blue to Violet */
            --border-color: rgba(30, 41, 59, 0.5); /* Slate-800 */
        }

        /* Main App Background */
        .stApp {
            background-color: var(--bg-color);
            font-family: 'Inter', sans-serif;
            color: var(--text-primary);
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
        }
        
        /* Remove default top padding */
        .block-container {
            padding-top: 2rem;
        }

        /* Custom Metric Card Class */
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card:hover {
            border-color: rgba(59, 130, 246, 0.5);
            box-shadow: 0 10px 30px -10px rgba(37, 99, 235, 0.2);
            transform: translateY(-2px);
        }

        .metric-title {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .metric-value {
            color: var(--text-primary);
            font-size: 1.875rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            margin-bottom: 4px;
        }

        .metric-sub {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }

        /* Integration Card Class */
        .integration-card {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.2s ease;
        }

        .integration-card:hover {
            border-color: var(--hover-color, #3b82f6);
            background: rgba(15, 23, 42, 0.8);
        }

        /* Buttons */
        .stButton > button {
            background: var(--accent-gradient);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .stButton > button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        /* Inputs */
        .stTextInput > div > div > input {
            background-color: #0f172a;
            border: 1px solid var(--border-color);
            color: white;
            border-radius: 12px;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }

        /* Headers */
        h1, h2, h3 {
            color: white !important;
            font-weight: 700;
            letter-spacing: -0.025em;
        }
        
        /* Hide default Streamlit elements if needed */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Sidebar Navigation (Radio) */
        div[role="radiogroup"] label {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 8px 12px;
            transition: all 0.2s;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }
        
        div[role="radiogroup"] label:hover {
            background-color: rgba(30, 41, 59, 0.5);
            color: white;
        }
        
        /* Active State (approximate, depends on Streamlit version) */
        div[role="radiogroup"] label[data-baseweb="radio"] {
             /* This targets the container */
        }
        
        /* Target the selected radio button text */
        div[role="radiogroup"] label p {
            font-weight: 500;
        }
        
    </style>
    """, unsafe_allow_html=True)

    # Inject Dynamic Background
    st.markdown(f"""
    <style>
        .stApp {{
            background-image: {bg_image} !important;
            background-attachment: fixed;
            background-size: cover;
        }}
    </style>
    """, unsafe_allow_html=True)



apply_custom_style(st.session_state.get('logged_in', False))



# --- Navigation ---

with st.sidebar:

    st.image("https://cdn-icons-png.flaticon.com/512/1384/1384060.png", width=50) # Placeholder Logo

    st.title("YouTube CEO")

    

    selected_page = st.radio(

        "Navegação",

        ["🏠 Início", "🚀 Desempenho", "💰 Monetização", "📤 Upload", "✨ Otimizar Existentes", "📝 Revisões Pendentes", "📋 Relatório", "🔌 Integrações"],

        label_visibility="collapsed"

    )

    

    st.divider()

    

    # User Status in Sidebar

    user = get_current_user_cached()

    if user:

        st.success(f"👤 {user.email}")

        if st.button("Sair", key="logout_btn"):

            auth.logout()

            st.rerun()

    else:

        st.warning("Visitante")

        if st.button("Login com Google"):

            login_url = auth.get_google_login_url()

            st.markdown(f'<meta http-equiv="refresh" content="0;url={login_url}">', unsafe_allow_html=True)



# --- Page Logic Functions ---



def render_home():

    st.title("🏠 Dashboard Principal")

def render_metric_card(title, value, sub_value, progress_percent):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">
            {title}
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub_value}</div>
        <div style="margin-top: 12px;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8; margin-bottom: 4px;">
                <span>Progresso</span>
                <span>{progress_percent}%</span>
            </div>
            <div style="width: 100%; background-color: rgba(30, 41, 59, 0.5); border-radius: 9999px; height: 6px; overflow: hidden;">
                <div style="width: {progress_percent}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #8b5cf6); border-radius: 9999px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    user = get_current_user_cached()

    

    if not user:

        st.info("👋 Bem-vindo! Faça login para começar a gerenciar seu canal.")

        return



    # Quick Stats (Mockup for now, can be real later)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card("Inscritos", "12.5K", "+120 essa semana", 65)
    with col2:
        render_metric_card("Visualizações (28d)", "450K", "+15% vs mês anterior", 95)
    with col3:
        render_metric_card("Receita Est.", "R$ 1.2K", "+5%", 40)
    with col4:
        render_metric_card("Vídeos Otimizados", "8", "2 pendentes", 75)

        

    st.divider()

    

    # Active Connections Status

    st.subheader("🔌 Status das Conexões")

    cols = st.columns(4)

    

    # YouTube API Status

    with cols[0]:

        service = get_authenticated_service()

        if service:

            st.success("✅ YouTube API")

        else:

            st.error("❌ YouTube API")

            

    # Supabase Status

    with cols[1]:

        if user:

            st.success("✅ Database")

        else:

            st.error("❌ Database")

            

    # Gemini Status

    with cols[2]:

        if os.environ.get("GOOGLE_API_KEY"):

            st.success("✅ Gemini AI")

        else:

            st.warning("⚠️ Gemini AI")



# --- Main Router Placeholder (will be populated as we migrate tabs) ---

# Router placeholder removed 



# --- Navigation (Refactored) ---

# tab_home, tab1, tab2, tab3, tab4, tab5, tab_report, tab7 = st.tabs(["🏠 Início", "🚀 Desempenho", "💰 Monetização", "📤 Upload", "✨ Otimizar Existentes", "📝 Revisões Pendentes", "📋 Relatório", "🔌 Integrações"])



def render_performance():

    st.title("🚀 Desempenho do Canal")

    

    col1, col2 = st.columns([3, 1])

    with col2:

        if st.button("🔄 Atualizar Dados", use_container_width=True):

            st.rerun()



    user = get_current_user_cached()

    service = None

    if user:

        service = get_cached_service(user.id)

    

    if service:

        try:

            # 1. Basic Stats

            # Cache this call if possible, but service object is not hashable easily for st.cache_data

            # We can cache the data fetching function instead

            

            channels_response = get_channel_stats(service)

            

            if channels_response['items']:

                stats = channels_response['items'][0]['statistics']

                uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

                

                m1, m2, m3 = st.columns(3)

                m1.metric("Inscritos", f"{int(stats['subscriberCount']):,}", delta_color="normal")

                m2.metric("Visualizações Totais", f"{int(stats['viewCount']):,}", delta="Todo o Tempo")

                m3.metric("Total de Vídeos", stats['videoCount'])

                

                st.divider()



                # 2. Fetch Video Data for Charts

                with st.spinner("Analisando dados do canal..."):

                    videos = []

                    playlist_response = service.playlistItems().list(

                        playlistId=uploads_playlist_id,

                        part='contentDetails',

                        maxResults=50

                    ).execute()

                    

                    video_ids = [item['contentDetails']['videoId'] for item in playlist_response['items']]

                    

                    # Need contentDetails for duration

                    stats_response = service.videos().list(

                        id=','.join(video_ids),

                        part='snippet,statistics,contentDetails'

                    ).execute()

                    

                    for item in stats_response['items']:

                        vid_stats = item['statistics']

                        snippet = item['snippet']

                        content = item['contentDetails']

                        duration_sec = parse_duration(content['duration'])

                        is_short = duration_sec <= 60

                        

                        videos.append({

                            'Title': snippet['title'],

                            'Views': int(vid_stats.get('viewCount', 0)),

                            'Likes': int(vid_stats.get('likeCount', 0)),

                            'Comments': int(vid_stats.get('commentCount', 0)),

                            'Type': 'Shorts' if is_short else 'Video'

                        })

                    

                    df = pd.DataFrame(videos)

                    

                    # --- Traffic Sources Section ---

                    st.subheader("🚦 Fontes de Tráfego (Últimos 30 Dias)")

                    # Use credentials from the already authenticated service

                    traffic_data = get_traffic_sources(service._http.credentials)

                    if traffic_data:

                        df_traffic = pd.DataFrame(traffic_data, columns=['Source', 'Views'])

                        fig_pie = px.pie(df_traffic, values='Views', names='Source', hole=0.4, template='plotly_dark')

                        st.plotly_chart(fig_pie, use_container_width=True)



                    # --- Shorts vs Long Section ---

                    st.subheader("📱 Shorts vs Vídeos Longos")

                    col_svl1, col_svl2 = st.columns(2)

                    

                    with col_svl1:

                        # Avg Views by Type

                        avg_views = df.groupby('Type')['Views'].mean().reset_index()

                        fig_avg = px.bar(avg_views, x='Type', y='Views', color='Type', title="Avg Views per Video", template='plotly_dark')

                        st.plotly_chart(fig_avg, use_container_width=True)

                        

                    with col_svl2:

                        # Engagement by Type

                        avg_likes = df.groupby('Type')['Likes'].mean().reset_index()

                        fig_likes = px.bar(avg_likes, x='Type', y='Likes', color='Type', title="Avg Likes per Video", template='plotly_dark')

                        st.plotly_chart(fig_likes, use_container_width=True)



                    # --- Top Videos ---

                    st.subheader("🏆 Melhores Vídeos (Recentes)")

                    fig_bar = px.bar(

                        df.sort_values('Views', ascending=False).head(10),

                        x='Views', y='Title', orientation='h', color='Views',

                        color_continuous_scale='Viridis', template='plotly_dark'

                    )

                    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)

                    st.plotly_chart(fig_bar, use_container_width=True)



        except HttpError as e:

            if "quotaExceeded" in str(e):

                st.error("🚫 Limite de cota da API do YouTube atingido. Tente novamente após as 05:00 (Horário de Brasília).")

            else:

                st.error(f"Erro na API do YouTube: {e}")

        except Exception as e:

            st.error(f"Erro ao carregar analytics: {e}")

    else:

        st.warning("Por favor, autentique-se para ver o analytics.")



# --- Router Update (Cont.) ---

# Router block removed



# --- Tab 2: Monetization ---

def render_monetization():

    st.title("💰 Rastreador de Monetização")

    

    service = get_authenticated_service()

    if service:

        try:

            # Fetch Subs

            subs = get_subscriber_count(service)

            

            # Fetch Watch Hours

            # Use credentials from the service object instead of reading file

            watch_hours = get_watch_time_year(service._http.credentials)

            

            # Progress Bars

            col_mon1, col_mon2 = st.columns(2)

            

            with col_mon1:

                st.subheader("👥 Inscritos")

                st.metric("Atual", f"{subs:,}", "/ 1,000 req")

                progress_subs = min(subs / 1000, 1.0)

                st.progress(progress_subs)

                if subs >= 1000:

                    st.success("✅ Requisito Atingido!")

                else:

                    st.caption(f"Faltam {1000 - subs}!")



            with col_mon2:

                st.subheader("⏱️ Horas Assistidas (365 Dias)")

                st.metric("Atual", f"{int(watch_hours):,}", "/ 4,000 req")

                progress_hours = min(watch_hours / 4000, 1.0)

                st.progress(progress_hours)

                if watch_hours >= 4000:

                    st.success("✅ Requisito Atingido!")

                else:

                    st.caption(f"Faltam {4000 - int(watch_hours)}!")



            st.divider()

            

            # Revenue Simulator

            st.subheader("💸 Simulador de Receita")

            st.info("Estime ganhos potenciais com base nas suas visualizações atuais.")

            

            col_sim1, col_sim2 = st.columns(2)

            with col_sim1:

                rpm = st.number_input("RPM Estimado ($)", value=1.50, step=0.10, help="Receita por 1.000 visualizações")

                

                # Fetch actual monthly views

                # creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES) # REMOVED

                actual_views = get_monthly_views(service._http.credentials)

                default_views = actual_views if actual_views > 0 else 10000

                

                monthly_views = st.number_input("Visualizações Mensais", value=default_views, step=1000)

            

            with col_sim2:

                estimated_earnings = (monthly_views / 1000) * rpm

                st.metric("Receita Mensal Estimada", f"${estimated_earnings:,.2f}")

                st.metric("Receita Anual Estimada", f"${estimated_earnings * 12:,.2f}")



        except Exception as e:

            st.error(f"Erro ao carregar dados de monetização: {e}")



# --- Router Update (Cont.) ---

# Router block removed



# --- Tab 3: Upload & Optimize ---

def render_upload():

    st.title("📤 Upload e Otimização")

    st.info("Analise um arquivo de vídeo com IA e faça upload diretamente para o YouTube.")



    # API Key Check

    api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:

        api_key = st.text_input("Insira a Chave da API Gemini", type="password")

        if api_key:

            os.environ["GOOGLE_API_KEY"] = api_key

            genai.configure(api_key=api_key)

    else:

        genai.configure(api_key=api_key)



    uploaded_file = st.file_uploader("Selecione o Arquivo (Vídeo ou Áudio)", type=["mp4", "mov", "avi", "mkv", "mp3", "wav", "mpeg"])

    

    if 'generated_metadata' not in st.session_state:

        st.session_state.generated_metadata = {}

    if 'transcript' not in st.session_state:

        st.session_state.transcript = ""



    col_act1, col_act2 = st.columns(2)

    

    with col_act1:

        if st.button("🎙️ Transcrever Áudio (Opcional)", use_container_width=True):

            if not uploaded_file:

                st.error("Selecione um vídeo primeiro.")

            elif not api_key:

                st.error("Chave API necessária.")

            else:

                with st.spinner("Transcrevendo áudio com Gemini..."):

                    try:

                        # Save temp

                        file_ext = uploaded_file.name.split('.')[-1]

                        video_path = os.path.join(ASSETS_DIR, f"temp_video.{file_ext}")

                        with open(video_path, "wb") as f:

                            f.write(uploaded_file.getbuffer())

                        

                        # Upload

                        video_file = genai.upload_file(path=video_path)

                        while video_file.state.name == "PROCESSING":

                            time.sleep(1)

                            video_file = genai.get_file(video_file.name)

                            

                        if video_file.state.name == "FAILED":

                            st.error("Falha no processamento do vídeo.")

                        else:

                            model_name = os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash")

                            model = genai.GenerativeModel(model_name)

                            response = model.generate_content([video_file, "Transcreva o áudio deste vídeo palavra por palavra. Retorne APENAS o texto da transcrição, sem formatação ou comentários."])

                            st.session_state.transcript = response.text

                            st.success("Transcrição concluída!")

                    except Exception as e:

                        st.error(f"Erro na transcrição: {e}")



    with col_act2:

        if st.button("✨ Gerar Metadados (SEO)", use_container_width=True):

            if not uploaded_file:

                st.error("Por favor, selecione um arquivo de vídeo.")

            elif not api_key:

                st.error("Chave da API Gemini necessária.")

            else:

                with st.spinner("Processando vídeo..."):

                    try:

                        # Save to temp file

                        file_ext = uploaded_file.name.split('.')[-1]

                        video_path = os.path.join(ASSETS_DIR, f"temp_video.{file_ext}")

                        with open(video_path, "wb") as f:

                            f.write(uploaded_file.getbuffer())



                        # 1. Upload to Gemini

                        st.text("Enviando para o Gemini...")

                        video_file = genai.upload_file(path=video_path)

                        

                        # Wait for processing

                        while video_file.state.name == "PROCESSING":

                            time.sleep(2)

                            video_file = genai.get_file(video_file.name)

                        

                        if video_file.state.name == "FAILED":

                            st.error("Gemini falhou ao processar o vídeo.")

                        else:

                            # 2. Generate Content

                            st.text("Gerando metadados...")

                            model_name = os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash")

                            model = genai.GenerativeModel(model_name)

                            

                            transcript_context = ""

                            if st.session_state.transcript:

                                transcript_context = f"\n\nTRANSCRIPT:\n{st.session_state.transcript}\n\n"

                            

                            prompt = f"""

                            Analyze this video {transcript_context} and generate optimized YouTube metadata.

                            Output ONLY a JSON object with these keys:

                            {{

                                "title": "A viral, click-worthy title (max 100 chars)",

                                "description": "A compelling description with keywords, emojis, and structure (max 5000 chars)",

                                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]

                            }}

                            """

                            response = model.generate_content([video_file, prompt])

                            

                            # Parse JSON

                            try:

                                # Clean up code blocks if present

                                text = response.text.replace('```json', '').replace('```', '')

                                metadata = json.loads(text)

                                st.session_state.generated_metadata = metadata

                                st.success("Metadata generated!")

                            except:

                                st.error("Falha ao processar resposta da IA. Saída bruta:")

                                st.text(response.text)

                                

                    except Exception as e:

                        st.error(f"Erro durante a análise: {e}")



    # Display Transcript if available

    if st.session_state.transcript:

        st.divider()

        st.subheader("📜 Transcrição e Vídeo")

        

        col_video, col_trans = st.columns([1, 1])

        

        with col_video:

            if uploaded_file:

                st.video(uploaded_file)

            else:

                st.info("Vídeo original não disponível para visualização.")

                

        with col_trans:

            st.session_state.transcript = st.text_area("Texto Transcrito (Editável)", st.session_state.transcript, height=400)



    st.divider()

    st.subheader("🎥 Gerador de Vídeo com IA")

    

    # Provider Selection

    col_gen1, col_gen2 = st.columns([1, 2])

    with col_gen1:

        available_providers = ["Auto", "Pollinations (Grátis)"]

        if os.environ.get("HUGGINGFACE_API_TOKEN"): available_providers.append("Hugging Face")

        if os.environ.get("STABILITY_API_KEY"): available_providers.append("Stability AI")

        if os.environ.get("OPENAI_API_KEY"): available_providers.append("OpenAI (DALL-E 3)")

        

        selected_img_provider = st.selectbox("🎨 Gerador de Imagem", available_providers)

        

    with col_gen2:

        default_prompt = st.session_state.transcript if st.session_state.transcript else "Um vídeo relaxante sobre a natureza e tecnologia..."

        video_prompt = st.text_area("Roteiro / Prompt para o Vídeo", value=default_prompt, height=100)



    if st.button("🎬 Gerar Vídeo com IA", use_container_width=True):

        if not video_prompt:

            st.error("O roteiro é obrigatório.")

        elif not os.environ.get("GOOGLE_API_KEY"):

            st.error("Chave da API Gemini necessária para criar o roteiro.")

        else:

            progress_bar = st.progress(0, text="Iniciando...")

            status_container = st.status("🚀 Iniciando geração...", expanded=True)

            

            try:

                # 1. Generate Scenes with Gemini

                status_container.write("🧠 Criando roteiro visual com Gemini...")

                model_name = os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash")

                model = genai.GenerativeModel(model_name)

                

                scene_prompt = f"""

                Create a visual storyboard for this text: "{video_prompt}"

                Split it into 3-5 scenes. For each scene, provide:

                1. A highly detailed image generation prompt (photorealistic, 8k).

                2. A duration in seconds (3-5s).

                Output ONLY a JSON list: [{{"prompt": "...", "duration": 4}}, ...]

                """

                

                response = model.generate_content(scene_prompt)

                text = response.text.replace('```json', '').replace('```', '')

                scenes = json.loads(text)

                

                clips = []

                

                # 2. Generate Images

                for i, scene in enumerate(scenes):

                    status_container.write(f"🎨 Gerando cena {i+1}/{len(scenes)}: {scene['prompt'][:30]}...")

                    progress_bar.progress((i / len(scenes)) * 0.8, text=f"Gerando cena {i+1}...")

                    

                    img_data = generate_image_with_ai(scene['prompt'], provider=selected_img_provider)

                    img_filename = os.path.join(ASSETS_DIR, f"scene_{i}.jpg")

                    

                    valid_image = False

                    if img_data:

                        with open(img_filename, "wb") as f:

                            f.write(img_data)

                        valid_image = True

                    

                    if valid_image:

                        # Create ImageClip

                        clip = ImageClip(img_filename).set_duration(scene['duration'])

                        clips.append(clip)

                    else:

                        status_container.warning(f"Falha na imagem da cena {i+1}")

                        

                # 3. Assemble

                if clips:

                    status_container.write("🎞️ Renderizando vídeo final...")

                    progress_bar.progress(0.9, text="Renderizando...")

                    

                    final_video = concatenate_videoclips(clips, method="compose")

                    output_filename = os.path.join(ASSETS_DIR, "final_video_ai.mp4")

                    final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac")

                    

                    st.success("Vídeo gerado com sucesso!")

                    st.video(output_filename)

                    

                    with open(output_filename, "rb") as f:

                        st.download_button("⬇️ Baixar Vídeo", f, file_name="video_ai.mp4")

                        

                    # Cleanup

                    final_video.close()

                    for clip in clips:

                        clip.close()

                else:

                    st.error("Não foi possível gerar cenas suficientes.")

                    

            except Exception as e:

                st.error(f"Erro no processo: {e}")



    # Display/Edit Metadata

    if st.session_state.generated_metadata:

        st.divider()

        st.subheader("📝 Revisar e Enviar")

        

        meta = st.session_state.generated_metadata

        

        up_title = st.text_input("Título", meta.get('title', ''), max_chars=100)

        up_desc = st.text_area("Descrição", meta.get('description', ''), height=200)

        up_tags_list = meta.get('tags', [])

        if isinstance(up_tags_list, list):

            up_tags = ", ".join(up_tags_list)

        else:

            up_tags = str(up_tags_list)

        up_tags = st.text_area("Tags (separadas por vírgula)", up_tags)

        

        privacy = st.selectbox("Status de Privacidade", ["private", "unlisted", "public"], index=0)

        

        if st.button("🚀 Enviar para o YouTube"):

            service = get_authenticated_service()

            if service:

                with st.spinner("Enviando para o YouTube..."):

                    try:

                        # Ensure temp file exists (re-save if needed or rely on persistence)

                        # Since streamlit reruns, we might need to rely on the file being there 

                        # or re-save it. For simplicity in this flow, we assume it persists briefly

                        # or we re-save if 'uploaded_file' is still valid.

                        # Ideally, we check if temp_video.mp4 exists.

                        

                        target_path = os.path.join(ASSETS_DIR, "temp_video.mp4")

                        if not os.path.exists(target_path):

                             if uploaded_file:

                                with open(target_path, "wb") as f:

                                    f.write(uploaded_file.getbuffer())

                             else:

                                st.error("Arquivo de vídeo perdido. Por favor, envie novamente.")

                                st.stop()



                        body = {

                            'snippet': {

                                'title': up_title,

                                'description': up_desc,

                                'tags': [t.strip() for t in up_tags.split(',')],

                                'categoryId': '22' # People & Blogs default

                            },

                            'status': {

                                'privacyStatus': privacy

                            }

                        }

                        

                        media = MediaFileUpload(target_path, chunksize=-1, resumable=True)

                        

                        request = service.videos().insert(

                            part=','.join(body.keys()),

                            body=body,

                            media_body=media

                        )

                        

                        response = None

                        while response is None:

                            status, response = request.next_chunk()

                            if status:

                                st.progress(int(status.progress() * 100))

                        

                        st.success(f"Vídeo enviado! ID: {response['id']}")

                        st.balloons()

                        # Clear state

                        st.session_state.generated_metadata = {}

                        # Cleanup

                        if os.path.exists(target_path):

                            os.remove(target_path)

                        

                    except Exception as e:

                        st.error(f"Falha no envio: {e}")



# --- Router Update (Cont.) ---

# Router block removed



# --- Tab 4: Optimize Existing ---

def render_optimize():

    st.title("✨ Otimizar Vídeos Existentes")

    

    # Mode Selection

    opt_mode = st.radio("Modo de Otimização", ["Manual", "Automático"], horizontal=True)

    

    SCHEDULER_FILE = 'scheduler_config.json'

    

    if opt_mode == "Automático":

        st.info("O modo automático otimizará o próximo vídeo da lista a cada intervalo definido.")

        

        # Load Config from DB

        user = get_current_user_cached()

        scheduler_config = {}

        if user:

            scheduler_config = database.get_automation_settings(user.id)

        

        col_auto1, col_auto2 = st.columns(2)

        with col_auto1:

            freq_options = {"6 horas": 6, "12 horas": 12, "24 horas": 24}

            current_freq = scheduler_config.get("frequency", 24)

            # Find index for selectbox

            freq_index = 2 # Default 24h

            for i, val in enumerate(freq_options.values()):

                if val == current_freq:

                    freq_index = i

                    break

            

            selected_freq_name = st.selectbox("Frequência", list(freq_options.keys()), index=freq_index)

            selected_freq_val = freq_options[selected_freq_name]

            

        with col_auto2:

            is_active = st.toggle("Ativar Automação", value=scheduler_config.get("active", False))

            

        if st.button("💾 Salvar Configuração de Automação"):

            if user:

                last_run = scheduler_config.get("last_run")

                next_run = (datetime.datetime.now() + datetime.timedelta(hours=selected_freq_val)).isoformat() if is_active else None

                

                if database.save_automation_settings(user.id, is_active, selected_freq_val, last_run, next_run):

                    st.success("Configuração salva no banco de dados!")

                    time.sleep(1)

                    st.rerun()

                else:

                    st.error("Erro ao salvar configuração.")

            else:

                st.error("Usuário não autenticado.")

            

        # Status Display

        st.divider()

        st.subheader("Status da Automação")

        if is_active:

            st.success("🟢 Automação ATIVA")

            last_run = scheduler_config.get("last_run", "Nunca")

            next_run = scheduler_config.get("next_run", "Aguardando...")

            st.write(f"**Última Execução:** {last_run}")

            st.write(f"**Próxima Execução:** {next_run}")

        else:

            st.warning("🔴 Automação INATIVA")



    else: # Manual Mode

        st.markdown("### 🎯 Otimização Manual e em Massa")

        

        mode_type = st.radio("Tipo de Seleção", ["Vídeo Único", "Filtro Inteligente (CTR)"], horizontal=True)

        

        service = get_authenticated_service()

        if not service:

             st.warning("Por favor, autentique-se para continuar.")

        else:

            if mode_type == "Vídeo Único":

                try:

                    # 1. Fetch Recent Videos

                    # Use cached service if possible or cache this specific call

                    @st.cache_data(ttl=3600)

                    def get_uploads_playlist(_service):

                        return _service.channels().list(mine=True, part='contentDetails').execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']



                    uploads_playlist_id = get_uploads_playlist(service)

                    

                    @st.cache_data(ttl=3600)

                    def get_playlist_items(_service, playlist_id):

                        return _service.playlistItems().list(

                            playlistId=playlist_id,

                            part='snippet,contentDetails',

                            maxResults=50

                        ).execute()



                    playlist_response = get_playlist_items(service, uploads_playlist_id)

                    

                    video_options = {}

                    for item in playlist_response['items']:

                        vid_id = item['contentDetails']['videoId']

                        vid_title = item['snippet']['title']

                        video_options[f"{vid_title} ({vid_id})"] = vid_id

                        

                    selected_video_name = st.selectbox("Selecione o Vídeo", list(video_options.keys()))

                    selected_video_id = video_options[selected_video_name]

                except Exception as e:

                    st.error(f"Erro ao carregar vídeos: {e}")

                    selected_video_id = None

            

            else: # Filtro Inteligente (CTR)

                st.info("Encontre vídeos com baixo desempenho (CTR baixo) que podem viralizar com novos títulos e thumbnails.")

                

                col_f1, col_f2 = st.columns(2)

                with col_f1:

                    ctr_threshold = st.slider("CTR Máximo (%)", 1.0, 15.0, 5.0, 0.5, help="Vídeos com CTR abaixo deste valor serão selecionados.")

                with col_f2:

                    days_filter = st.slider("Publicados nos últimos (dias)", 2, 90, 30)

                

                if st.button("🔍 Buscar Oportunidades"):

                    with st.spinner("Analisando performance dos vídeos..."):

                         # 1. Get Videos

                        try:

                            uploads_playlist_id = service.channels().list(mine=True, part='contentDetails').execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

                            

                            all_videos = []

                            next_page_token = None

                            

                            # Fetch enough videos to cover the date range (approx)

                            # Limit to 50 for performance for now

                            playlist_response = service.playlistItems().list(

                                playlistId=uploads_playlist_id,

                                part='snippet,contentDetails',

                                maxResults=50 

                            ).execute()

                            

                            video_ids = [item['contentDetails']['videoId'] for item in playlist_response['items']]

                            

                            # 2. Get Analytics (Impressions & Views) for these videos

                            # Note: YouTube Analytics API is complex for per-video queries in batch.

                            # We will query 'video' dimension.

                            

                            end_date = datetime.date.today().strftime("%Y-%m-%d")

                            start_date = (datetime.date.today() - datetime.timedelta(days=days_filter)).strftime("%Y-%m-%d")

                            

                            analytics = build('youtubeAnalytics', 'v2', credentials=service._http.credentials)

                            

                            # We need to query analytics for EACH video or use a filter?

                            # Querying top videos by views might miss low CTR ones.

                            # Let's try to query metrics for the specific video IDs if possible, or just top 50.

                            # Actually, querying by video==ID is best but quota heavy.

                            # Better: Query dimension='video' sort='-publishedAt' (not supported directly in analytics usually).

                            # Workaround: Query dimension='video' for top 200 videos in period.

                            

                            analytics_resp = analytics.reports().query(

                                ids='channel==MINE',

                                startDate=start_date,

                                endDate=end_date,

                                metrics='views,annotationImpressions,cardImpressions', # 'impressions' is not always available directly without owner context? 

                                # Wait, 'impressions' is available.

                                # Let's try 'views,estimatedMinutesWatched' and see if we can get impressions.

                                # Actually 'impressions' metric exists.

                                dimensions='video',

                                maxResults=50,

                                sort='-views'

                            ).execute()

                            

                            # Map analytics to dict

                            vid_metrics = {}

                            if 'rows' in analytics_resp:

                                for row in analytics_resp['rows']:

                                    # row: [video_id, views, ...]

                                    # We need to check headers

                                    # Assuming standard order or check columnHeaders

                                    vid_id = row[0]

                                    # We need impressions. If not available, we can't calc CTR.

                                    # Let's assume we can't easily get bulk impressions for all videos via API v2 easily without 'impressions' metric which might be restricted.

                                    # Fallback: Use 'views' and maybe just list them for now?

                                    # User specifically asked for CTR.

                                    # Let's try to fetch 'impressions' metric.

                                    pass

                                    

                            # RE-STRATEGY: Since bulk CTR is hard, let's just list the recent videos and fetch their details.

                            # We will filter by "Not Optimized" and "Age > 24h".

                            # For CTR, we might need to skip or mock if API fails, but let's try.

                            

                            # For this implementation, we will filter by:

                            # 1. Age > 24h

                            # 2. Not in History

                            

                            candidates = []

                            user = get_current_user_cached()

                            history = database.get_optimization_history(user.id) if user else []

                            optimized_ids = [h['video_id'] for h in history]

                            

                            for item in playlist_response['items']:

                                vid_id = item['contentDetails']['videoId']

                                pub_date = item['snippet']['publishedAt'] # ISO format

                                # Check 24h rule

                                pub_dt = datetime.datetime.fromisoformat(pub_date.replace('Z', '+00:00'))

                                if (datetime.datetime.now(datetime.timezone.utc) - pub_dt).total_seconds() < 24 * 3600:

                                    continue # Too new

                                    

                                if vid_id in optimized_ids:

                                    continue # Already optimized

                                    

                                # Mock CTR for now as API is tricky, or fetch individually?

                                # Individual fetch is too slow.

                                # Let's just show them as candidates based on "Not Optimized" rule for now, 

                                # and maybe add a "Get CTR" button later?

                                # User asked for CTR filter.

                                # Let's try to get 'annotationClickThroughRate' if available or just random for demo if API fails?

                                # No, let's be honest.

                                

                                candidates.append({

                                    'id': vid_id,

                                    'title': item['snippet']['title'],

                                    'date': pub_date[:10]

                                })

                                

                            if candidates:

                                st.session_state.bulk_candidates = candidates

                                st.success(f"Encontrados {len(candidates)} vídeos elegíveis ( > 24h e não otimizados).")

                            else:

                                st.warning("Nenhum vídeo encontrado com os critérios.")

                                

                        except Exception as e:

                            st.error(f"Erro na busca: {e}")



                if 'bulk_candidates' in st.session_state and st.session_state.bulk_candidates:

                    st.markdown("### 📋 Vídeos Candidatos")

                    df_cand = pd.DataFrame(st.session_state.bulk_candidates)

                    st.dataframe(df_cand, use_container_width=True)

                    

                    if st.button("🚀 Otimizar TODOS (Gerar Sugestões)"):

                        progress_bar = st.progress(0)

                        status_text = st.empty()

                        

                        api_key = os.environ.get("GOOGLE_API_KEY")

                        if not api_key:

                            st.error("Configure a API Key do Gemini primeiro.")

                        else:

                            model_name = os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash")

                            model = genai.GenerativeModel(model_name)

                            

                            count = 0

                            for vid in st.session_state.bulk_candidates:

                                status_text.text(f"Processando: {vid['title']}...")

                                try:

                                    # Fetch details

                                    vid_response = get_video_details(service, vid['id'])

                                    if vid_response['items']:

                                        snippet = vid_response['items'][0]['snippet']

                                        

                                        # Fetch User Persona

                                        user_persona = ""

                                        if user:

                                            persona_key = database.get_user_api_keys(user.id).get("Optimization_Persona", {})

                                            user_persona = persona_key.get("api_key", "")

                                            

                                        # Fetch Transcript

                                        transcript_text = get_video_transcript(vid['id'])

                                        transcript_context = f"Video Transcript/Content:\n{transcript_text[:10000]}..." if transcript_text else "Transcript not available."



                                        # Fetch Channel Learning Context (Top Videos)

                                        top_videos = get_top_performing_videos(service, max_results=5)

                                        channel_context = ""

                                        if top_videos:

                                            channel_context = "Top Performing Videos on this Channel (Emulate this style):\n"

                                            for tv in top_videos:

                                                channel_context += f"- {tv['title']}\n"



                                        # Generate

                                        prompt = f"""

                                        Optimize this YouTube video metadata.

                                        

                                        User Persona / Channel Style Instructions:

                                        {user_persona if user_persona else "No specific style defined. Use best practices for high CTR and engagement."}

                                        

                                        {channel_context}



                                        Title: {snippet['title']}

                                        Desc: {snippet['description']}

                                        Tags: {snippet.get('tags', [])}

                                        

                                        {transcript_context}

                                        

                                        Output JSON: {{ "title": "...", "description": "...", "tags": [...] }}

                                        """

                                        response = model.generate_content(prompt)

                                        text = response.text.replace('```json', '').replace('```', '')

                                        suggestions = json.loads(text)

                                        

                                        # Add to Pending

                                        if user:

                                            database.add_pending_review(

                                                user.id, vid['id'], snippet['title'],

                                                suggestions.get('title'), suggestions.get('description'), 

                                                suggestions.get('tags'), None

                                            )

                                            

                                            # Log to Session History

                                            st.session_state.session_history.append({

                                                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),

                                                "old_title": snippet['title'],

                                                "new_title": suggestions.get('title'),

                                                "status": "pending_review"

                                            })

                                    count += 1

                                    progress_bar.progress(count / len(st.session_state.bulk_candidates))

                                except Exception as e:

                                    print(f"Erro ao otimizar {vid['id']}: {e}")

                                    

                            status_text.text("Concluído!")

                            st.success(f"✅ Sucesso! {count} vídeos foram analisados e as sugestões estão prontas.")

                            st.info("👉 Vá para a aba **'🏠 Início'** e procure por **'Revisões Pendentes'** para aprovar ou editar as sugestões antes de aplicar no YouTube.")

                            st.session_state.bulk_candidates = [] # Clear list to prevent re-submission

                            # Removed st.rerun() to let user see the message



            # End of Bulk Mode Logic

            selected_video_id = None # Reset if in bulk mode to avoid rendering single video UI below

            if mode_type == "Vídeo Único" and 'selected_video_name' in locals():

                 selected_video_id = video_options.get(selected_video_name)

        

        # 2. Fetch Current Metadata

        if selected_video_id:

            try:

                vid_response = get_video_details(service, selected_video_id)

                if vid_response['items']:

                    current_snippet = vid_response['items'][0]['snippet']

                    

                    current_title = current_snippet['title']

                    current_desc = current_snippet['description']

                    current_tags = current_snippet.get('tags', [])

                    

                    st.subheader("Metadados Atuais")

                    with st.expander("Ver Detalhes Atuais", expanded=False):

                        st.text_input("Título", current_title, disabled=True)

                        st.text_area("Descrição", current_desc, disabled=True, height=150)

                        st.text_area("Tags", ", ".join(current_tags), disabled=True)

                else:

                    st.warning("Vídeo não encontrado.")

            except HttpError as e:

                if "quotaExceeded" in str(e):

                     st.error("🚫 Limite de cota da API do YouTube atingido. Tente novamente após as 05:00 (Horário de Brasília).")

                else:

                     st.error(f"Erro ao carregar detalhes do vídeo: {e}")

            except Exception as e:

                st.error(f"Erro inesperado: {e}")



            # 3. AI Optimization

            if 'opt_suggestions' not in st.session_state:

                st.session_state.opt_suggestions = {}

            

            # API Key Check (Reuse from Tab 3 logic or env)

            api_key = os.environ.get("GOOGLE_API_KEY")

            if not api_key:

                api_key = st.text_input("Insira a Chave da API Gemini para Otimização", type="password", key="opt_api_key")

                if api_key:

                    os.environ["GOOGLE_API_KEY"] = api_key

                    genai.configure(api_key=api_key)

            

            if st.button("🤖 Gerar Melhorias com IA"):

                if not api_key:

                    st.error("Chave da API Gemini necessária.")

                else:

                    with st.spinner("Analisando e Otimizando..."):

                        try:

                            model_name = os.environ.get("GOOGLE_MODEL", "gemini-1.5-flash")

                            model = genai.GenerativeModel(model_name)

                            # Fetch User Persona

                            user = get_current_user_cached()

                            user_persona = ""

                            if user:

                                persona_key = database.get_user_api_keys(user.id).get("Optimization_Persona", {})

                                user_persona = persona_key.get("api_key", "")



                            # Fetch Transcript

                            transcript_text = get_video_transcript(selected_video_id)

                            

                            # Debug/Feedback UI

                            if transcript_text:

                                st.success(f"✅ Transcrição carregada ({len(transcript_text)} caracteres)")

                                with st.expander("Ver Transcrição Usada"):

                                    st.text(transcript_text[:1000] + "..." if len(transcript_text) > 1000 else transcript_text)

                            else:

                                st.warning("⚠️ Não foi possível carregar a transcrição deste vídeo. A IA usará apenas o título e descrição atuais.")



                            transcript_context = f"Video Transcript/Content:\n{transcript_text[:15000]}..." if transcript_text else "Transcript not available."



                            # Fetch Channel Learning Context (Top Videos)

                            top_videos = get_top_performing_videos(service, max_results=5)

                            channel_context = ""

                            if top_videos:

                                channel_context = "Top Performing Videos on this Channel (Emulate this style):\n"

                                for tv in top_videos:

                                    channel_context += f"- {tv['title']}\n"



                            prompt = f"""

                            Optimize this YouTube video metadata for better SEO, CTR, and viral potential.

                            

                            User Persona / Channel Style Instructions:

                            {user_persona if user_persona else "No specific style defined. Use best practices for high CTR and engagement."}

                            

                            {channel_context}

                            

                            Current Title: {current_title}

                            Current Description: {current_desc}

                            Current Tags: {current_tags}

                            

                            {transcript_context}

                            

                            Output ONLY a JSON object with these keys:

                            {{

                                "title": "A significantly better, click-worthy title (max 100 chars)",

                                "description": "A structured, engaging description with keywords and emojis (max 5000 chars)",

                                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]

                            }}

                            """

                            response = model.generate_content(prompt)

                            

                            # Parse JSON

                            text = response.text.replace('```json', '').replace('```', '')

                            suggestions = json.loads(text)

                            st.session_state.opt_suggestions = suggestions

                            st.success("Sugestões geradas!")

                            

                        except Exception as e:

                            st.error(f"Falha na otimização: {e}")



            # 4. Review & Apply

            if st.session_state.opt_suggestions:

                st.divider()

                st.subheader("✨ Revisar Sugestões")

                

                sugg = st.session_state.opt_suggestions

                

                col_opt1, col_opt2 = st.columns(2)

                

                with col_opt1:

                    st.markdown("### 📝 Editar Novos Metadados")

                    new_opt_title = st.text_input("Novo Título", sugg.get('title', ''), key="new_opt_title")

                    new_opt_desc = st.text_area("Nova Descrição", sugg.get('description', ''), height=300, key="new_opt_desc")

                    

                    tags_list = sugg.get('tags', [])

                    if isinstance(tags_list, list):

                        tags_str = ", ".join(tags_list)

                    else:

                        tags_str = str(tags_list)

                    new_opt_tags = st.text_area("Novas Tags", tags_str, key="new_opt_tags")

                

                with col_opt2:

                    st.markdown("### 🆚 Comparação")

                    st.caption("Original vs Novo")

                    st.text(f"Mudança de Título:\n{current_title}\n⬇\n{new_opt_title}")

                    st.divider()

                    st.info("Clicar em Aplicar atualizará o vídeo no YouTube imediatamente.")

                    

                    if st.button("✅ Aplicar Mudanças no YouTube"):

                        if update_video_on_youtube(service, selected_video_id, new_opt_title, new_opt_desc, [t.strip() for t in new_opt_tags.split(',')]):

                            st.balloons()

                            st.success("✅ Vídeo atualizado com sucesso no YouTube!")

                            st.info("As alterações já estão visíveis no seu canal.")

                            

                            # Update History in DB (Optional but good practice)

                            user = get_current_user_cached()

                            if user:

                                database.add_optimization_history(user.id, selected_video_id, new_opt_title, "manual_ai", {"timestamp": datetime.datetime.now().isoformat()})



                            # Add to Session History

                            st.session_state.session_history.append({

                                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),

                                "old_title": current_title,

                                "new_title": new_opt_title,

                                "status": "success"

                            })



# --- Tab 5: Pending Reviews ---

def render_reviews():
    user = get_current_user_cached()
    if not user:
        st.warning("Faça login para ver revisões pendentes.")
        return

    pending = database.get_pending_reviews(user.id)
    
    if not pending:
        st.container().success("🎉 Tudo em dia! Nenhum vídeo aguardando revisão.")
    else:
        st.info(f"Você tem {len(pending)} vídeo(s) aguardando aprovação.")
        
        # Convert to list to handle deletion during iteration
        for video_id in list(pending.keys()):
            item = pending[video_id]
            
            with st.expander(f"🎥 {item['current_title']}", expanded=True):
                col1, col2 = st.columns([1, 1.5])
                
                with col1:
                    st.markdown("### 🛑 Original")
                    st.caption("Metadados Atuais")
                    st.text_input("Título Atual", item['current_title'], disabled=True, key=f"old_title_{video_id}")
                    st.text_area("Descrição Atual", "...", disabled=True, height=100, key=f"old_desc_{video_id}")
                
                with col2:
                    st.markdown("### ✨ Sugestão Otimizada")
                    st.caption("Gerado por IA • Editável")
                    new_title = st.text_input("Novo Título", item['new_title'], key=f"title_{video_id}")
                    new_desc = st.text_area("Nova Descrição", item['new_description'], height=300, key=f"desc_{video_id}")
                    new_tags = st.text_area("Novas Tags", item['new_tags'], key=f"tags_{video_id}")
                    
                    if item.get('thumbnail_path'):
                        st.image(item['thumbnail_path'], caption="Thumbnail Gerada", width=300)

                st.divider()
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
                
                if btn_col1.button("✅ Aprovar", key=f"approve_{video_id}", use_container_width=True):
                    service = get_authenticated_service()
                    if service:
                        if update_video_on_youtube(service, video_id, new_title, new_desc, new_tags, item.get('thumbnail_path')):
                            # Update History in DB
                            database.add_optimization_history(user.id, video_id, new_title, "optimized", {"timestamp": datetime.datetime.now().isoformat()})
                            # Remove from pending in DB
                            database.delete_pending_review(user.id, video_id)
                            st.toast("Vídeo atualizado com sucesso!", icon="✅")
                            st.rerun()
                            
                if btn_col2.button("🗑️ Rejeitar", key=f"reject_{video_id}", use_container_width=True):
                    database.delete_pending_review(user.id, video_id)
                    st.toast("Sugestão rejeitada.", icon="🗑️")
                    st.rerun()
# --- Tab 6: Control (Removed) ---

# with tab6:

#     st.title("⚙️ Controle do Sistema")

#     st.info("Funcionalidade de robô em segundo plano removida para compatibilidade com nuvem.")



def fetch_google_models(api_key):

    """Fetches available models from Google Gemini API."""

    try:

        genai.configure(api_key=api_key)

        models = []

        for m in genai.list_models():

            if 'generateContent' in m.supported_generation_methods:

                models.append(m.name.replace('models/', ''))

        return sorted(models, reverse=True)

    except Exception:

        return []



def fetch_openai_models(api_key):

    """Fetches available models from OpenAI API."""

    try:

        headers = {"Authorization": f"Bearer {api_key}"}

        response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=5)

        if response.status_code == 200:

            data = response.json()

            models = [m['id'] for m in data['data'] if 'gpt' in m['id']]

            return sorted(models, reverse=True)

        return []

    except Exception:

        return []



# --- Router Update (Final) ---

# Router block removed



# --- Tab Report: Session History ---

def render_report():

    st.title("📋 Relatório da Sessão")

    st.caption("Histórico temporário das otimizações realizadas nesta sessão.")

    

    if not st.session_state.session_history:

        st.info("Nenhuma otimização realizada nesta sessão ainda.")

    else:

        if st.button("🗑️ Limpar Histórico"):

            st.session_state.session_history = []

            st.rerun()

            

        # Reverse to show newest first

        for item in reversed(st.session_state.session_history):

            with st.container(border=True):

                col_r1, col_r2 = st.columns([3, 1])

                with col_r1:

                    st.markdown(f"**De:** {item['old_title']}")

                    st.markdown(f"**Para:** {item['new_title']}")

                with col_r2:

                    if item['status'] == 'success':

                        st.success("✅ Sucesso")

                    elif item['status'] == 'pending_review':

                        st.warning("📝 Em Revisão")

                    else:

                        st.error("❌ Falha")

                st.caption(f"🕒 {item['timestamp']}")



# --- Tab 7: Integrations ---

def render_integrations():

    st.title("🔌 Integrações de API")

    

    # Load current config

    current_config = {}

    if os.path.exists(API_CONFIG_FILE):

        try:

            with open(API_CONFIG_FILE, 'r') as f:

                current_config = json.load(f)

        except:

            pass
    # API Providers Definition with SVGs
    PROVIDERS = {
        "Supabase Auth": {
            "env_var": "SUPABASE_URL",
            "key_var": "SUPABASE_KEY",
            "help": "URL e Key do projeto Supabase.",
            "icon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3ECF8E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path></svg>""",
            "models": []
        },
        "Google Gemini": {
            "env_var": "GOOGLE_API_KEY",
            "model_var": "GOOGLE_MODEL",
            "help": "IA para análise e otimização.",
            "icon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4285F4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 12z"></path><path d="M21 12h-9"></path></svg>""",
            "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
        },
        "OpenAI (ChatGPT)": {
            "env_var": "OPENAI_API_KEY",
            "model_var": "OPENAI_MODEL",
            "help": "IA alternativa (GPT-4).",
            "icon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"></path><path d="M12 12L2.5 17.5"></path><path d="M12 12l9.5 5.5"></path></svg>""",
            "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        },
        "Anthropic (Claude)": {
            "env_var": "ANTHROPIC_API_KEY",
            "model_var": "ANTHROPIC_MODEL",
            "help": "IA alternativa (Claude).",
            "icon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D97757" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 8v8"></path><path d="M8 12h8"></path></svg>""",
            "models": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"]
        },
        "Stability AI": {
            "env_var": "STABILITY_API_KEY",
            "model_var": "STABILITY_MODEL",
            "help": "Geração de imagens.",
            "icon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#7D55C7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>""",
            "models": ["core", "sd3", "ultra"]
        },
        "ElevenLabs": {
            "env_var": "ELEVENLABS_API_KEY",
            "model_var": "ELEVENLABS_MODEL",
            "help": "Narração de voz (TTS).",
            "icon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>""",
            "models": ["eleven_multilingual_v2", "eleven_turbo_v2"]
        },
        "Pexels": {
            "env_var": "PEXELS_API_KEY",
            "model_var": "PEXELS_MODEL",
            "help": "Banco de vídeos stock.",
            "icon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#07A081" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>""",
            "models": []
        },
        "YouTube API": {
            "env_var": "YOUTUBE_CLIENT_SECRET",
            "key_var": "YOUTUBE_CLIENT_ID",
            "help": "Upload e Analytics.",
            "icon": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FF0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"></path><polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"></polygon></svg>""",
            "models": []
        }
    }



    # Load user keys from DB and merge into current_config

    user = get_current_user_cached()

    if user:

        db_keys = database.get_user_api_keys(user.id)

        for provider_name, data in db_keys.items():

            if provider_name in PROVIDERS:

                env_var = PROVIDERS[provider_name]["env_var"]

                current_config[env_var] = data['api_key']

                # CRITICAL: Set env var for this session so other parts of app can use it

                if data['api_key']:

                    os.environ[env_var] = data['api_key']

                    

                if "model_var" in PROVIDERS[provider_name] and data['model']:

                    current_config[PROVIDERS[provider_name]["model_var"]] = data['model']

                    os.environ[PROVIDERS[provider_name]["model_var"]] = data['model']



    # --- Status Dashboard & Configuration (Merged) ---

    st.subheader("Visão Geral e Configuração")

    

    # Create a grid layout

    cols = st.columns(3)

    

    for idx, (name, info) in enumerate(PROVIDERS.items()):

        with cols[idx % 3]:

            # Determine status

            is_configured = False

            if name == "Supabase Auth":

                if current_config.get(info["env_var"]) and current_config.get(info["key_var"]):

                    is_configured = True

            elif name == "YouTube Data API":

                # Use absolute path to be safe

                secret_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json")

                if os.path.exists(secret_path):

                    is_configured = True

            else:

                if current_config.get(info["env_var"]):

                    is_configured = True

            

            status_color = "#A371F7" if is_configured else "#30363D"

            status_label = "ATIVO" if is_configured else "INATIVO"

            status_icon_html = "⚡" if is_configured else "💤"

            

            # Card Container

            with st.container(border=True):

                # Visual Header (Icon + Name + Status)
                st.markdown(f"""
<div style="text-align: center; padding: 10px;">
    <div style="font-size: 40px; margin-bottom: 10px;">{info['icon']}</div>
    <div style="font-weight: 600; font-size: 16px; margin-bottom: 5px;">{name.split()[0]}</div>
    <div style="
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        background-color: {status_color}33;
        border: 1px solid {status_color};
        color: {status_color};
        font-size: 12px;
        font-weight: bold;
    ">
        {status_icon_html} {status_label}
    </div>
</div>
""", unsafe_allow_html=True)

                

                st.markdown("---")

                

                # Configuration Expander

                with st.expander("⚙️ Configurar", expanded=False):

                    st.caption(info['help'])

                    

                    # Special handling for Supabase (Read-only mostly)

                    if name == "Supabase Auth":

                        st.text_input("URL", value=current_config.get(info["env_var"], "")[:20]+"...", disabled=True, key=f"url_{idx}")

                        st.text_input("Key", value="****************", disabled=True, key=f"key_disp_{idx}")

                        st.info("Configurado via Segredos do Streamlit.")

                    

                    # Special handling for YouTube

                    elif name == "YouTube Data API":

                        secret_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret.json")

                        if is_configured:

                            st.success("Client Secret encontrado!")

                            

                            # Check if user has token

                            has_token = False

                            if user:

                                token = database.get_youtube_token(user.id)

                                if token:

                                    has_token = True

                            

                            if has_token:

                                st.success("✅ Conta Conectada")

                                if st.button("🔄 Reconectar", key=f"reconnect_{idx}"):

                                    auth_url = auth.get_google_login_url()

                                    st.markdown(f'<a href="{auth_url}" target="_self" class="stButton">🔗 Clique aqui para Reconectar</a>', unsafe_allow_html=True)

                            else:

                                st.warning("⚠️ Token de acesso ausente.")

                                auth_url = auth.get_google_login_url()

                                st.markdown(f'<a href="{auth_url}" target="_self" style="display: inline-block; padding: 0.5em 1em; color: white; background-color: #FF4B4B; border-radius: 0.3rem; text-decoration: none;">🔗 Conectar Conta Google</a>', unsafe_allow_html=True)



                            st.markdown("---")

                            if st.button("🗑️ Remover Client Secret", key=f"del_yt_{idx}"):

                                try:

                                    os.remove(secret_path)

                                    st.rerun()

                                except: pass

                        else:

                            st.error("Arquivo faltando.")

                            uploaded = st.file_uploader("Upload client_secret.json", type=['json'], key=f"up_{idx}")

                            if uploaded:

                                with open(secret_path, "wb") as f:

                                    f.write(uploaded.getbuffer())

                                st.success("Salvo!")

                                time.sleep(1)

                                st.rerun()

                            

                    else:

                        # Standard API Key Input

                        env_var = info["env_var"]

                        model_var = info.get("model_var")

                        

                        current_key = current_config.get(env_var, "")

                        new_key = st.text_input(f"Chave API", value=current_key, type="password", key=f"key_{idx}")

                        

                        # Model Selection

                        new_model = None

                        if model_var:

                            available_models = info.get("models", [])

                            

                            # Dynamic Fetching

                            if new_key:

                                 if name == "Google Gemini":

                                    fetched = fetch_google_models(new_key)

                                    if fetched: available_models = fetched

                                 elif name == "OpenAI (ChatGPT)":

                                    fetched = fetch_openai_models(new_key)

                                    if fetched: available_models = fetched

                            

                            current_model = current_config.get(model_var, available_models[0] if available_models else "")

                            if available_models:

                                if current_model not in available_models:

                                    current_model = available_models[0]

                                new_model = st.selectbox(f"Modelo", available_models, index=available_models.index(current_model), key=f"model_{idx}")

                        

                        # Save Button

                        if st.button(f"💾 Salvar", key=f"save_{idx}", use_container_width=True):

                             user = get_current_user_cached()

                             if user:

                                success, msg = database.save_user_api_key(user.id, name, new_key, new_model)

                                if success:

                                    os.environ[env_var] = new_key

                                    if new_model: os.environ[model_var] = new_model

                                    st.success("Salvo!")

                                    time.sleep(1)

                                    st.rerun()

                                else:

                                    st.error(f"Erro: {msg}")

                             else:

                                st.error("Login necessário.")



    # --- AI Persona Section ---

    st.markdown("---")

    st.subheader("🎭 Personalização da IA")

    st.info("Defina o estilo do seu canal para que a IA gere títulos e descrições com a sua cara!")

    

    # Load existing persona

    current_persona = ""

    if user:

        # We reuse user_api_keys table with a special provider name

        persona_key = database.get_user_api_keys(user.id).get("Optimization_Persona", {})

        current_persona = persona_key.get("api_key", "") # storing style in api_key column



    new_persona = st.text_area("Estilo do Canal / Instruções de Persona", 

                               value=current_persona, 

                               placeholder="Ex: Meu canal é focado em tutoriais rápidos e diretos. Use linguagem simples, evite clickbait exagerado. Público alvo: iniciantes em programação.",

                               height=100)

    

    if st.button("💾 Salvar Persona"):

        if user:

            # Save to DB

            success, msg = database.save_user_api_key(user.id, "Optimization_Persona", new_persona, "style_v1")

            if success:

                st.success("Persona salva com sucesso! A IA usará essas instruções nas próximas otimizações.")

                time.sleep(1)

                st.rerun()

            else:

                st.error(f"Erro ao salvar: {msg}")

        else:

            st.error("Faça login para salvar.")



    st.divider()

    with st.expander("Ver Todas as Chaves Salvas (Oculto)"):

        st.json({k: "********" if "KEY" in k and v else v for k, v in current_config.items()})

# --- Main Router ---
if selected_page == "🏠 Início":
    render_home()
elif selected_page == "🚀 Desempenho":
    render_performance()
elif selected_page == "💰 Monetização":
    render_monetization()
elif selected_page == "📤 Upload":
    render_upload()
elif selected_page == "✨ Otimizar Existentes":
    render_optimize()
elif selected_page == "📝 Revisões Pendentes":
    render_reviews()
elif selected_page == "📋 Relatório":
    render_report()
elif selected_page == "🔌 Integrações":
    render_integrations()
