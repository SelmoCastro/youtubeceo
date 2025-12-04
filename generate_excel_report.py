import os
import datetime
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# --- Configuration ---
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
TOKEN_FILE = 'token.json'
CLIENT_SECRETS_FILE = 'client_secret.json'
REPORT_FILE = 'channel_report.xlsx'

def get_authenticated_service():
    """Authenticates with YouTube Data API using saved token or new auth flow."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"Error: {CLIENT_SECRETS_FILE} not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build(API_SERVICE_NAME, API_VERSION, credentials=creds)

def get_all_videos_stats(service):
    """Fetches all videos with their statistics."""
    print("Fetching video list...")
    videos = []
    
    # 1. Get Uploads Playlist ID
    channels_response = service.channels().list(
        mine=True,
        part='contentDetails'
    ).execute()
    
    if not channels_response['items']:
        return []
        
    uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    # 2. Fetch all video IDs from playlist
    video_ids = []
    next_page_token = None
    while True:
        playlist_response = service.playlistItems().list(
            playlistId=uploads_playlist_id,
            part='contentDetails',
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        
        for item in playlist_response['items']:
            video_ids.append(item['contentDetails']['videoId'])
            
        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break
            
    # 3. Fetch Video Statistics (Batching 50 at a time)
    print(f"Found {len(video_ids)} videos. Fetching stats...")
    
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        stats_response = service.videos().list(
            id=','.join(batch_ids),
            part='snippet,statistics'
        ).execute()
        
        for item in stats_response['items']:
            stats = item['statistics']
            snippet = item['snippet']
            videos.append({
                'Video ID': item['id'],
                'Title': snippet['title'],
                'Published At': snippet['publishedAt'],
                'Views': int(stats.get('viewCount', 0)),
                'Likes': int(stats.get('likeCount', 0)),
                'Comments': int(stats.get('commentCount', 0))
            })
            
    return videos

def get_video_ctr(creds, video_id):
    """Fetches CTR for a specific video (Last 30 Days)."""
    try:
        analytics = build('youtubeAnalytics', 'v2', credentials=creds)
        end_date = datetime.date.today().strftime("%Y-%m-%d")
        start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        # Try fetching daily data which is often more reliable for CTR
        response = analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='impressionsClickThroughRate,impressions',
            dimensions='day',
            filters=f'video=={video_id}'
        ).execute()

        rows = response.get('rows', [])
        if not rows:
            return 0.0
            
        # Calculate weighted average CTR
        total_impressions = 0
        total_clicks = 0
        
        for row in rows:
            # row[0] is date (dimension)
            ctr = row[1]
            impressions = row[2]
            
            clicks = impressions * ctr
            total_impressions += impressions
            total_clicks += clicks
            
        if total_impressions > 0:
            return total_clicks / total_impressions
        return 0.0

    except Exception as e:
        # Log to file instead of spamming console, or just print a small 'x'
        # print(f"x", end="", flush=True) 
        return 0.0

def get_channel_evolution(creds):
    """Fetches daily views and subscribers for the last 30 days."""
    print("Fetching channel evolution data...")
    try:
        analytics = build('youtubeAnalytics', 'v2', credentials=creds)
        end_date = datetime.date.today().strftime("%Y-%m-%d")
        start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        response = analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='views,subscribersGained',
            dimensions='day',
            sort='day'
        ).execute()

        data = []
        for row in response.get('rows', []):
            data.append({
                'Date': row[0],
                'Daily Views': row[1],
                'Daily Subs': row[2]
            })
        return data
    except Exception as e:
        print(f"Error fetching evolution data: {e}")
        return []

def main():
    service = get_authenticated_service()
    if not service:
        return

    # 1. Get Video Data
    videos_data = get_all_videos_stats(service)
    
    # 2. Enrich with CTR (Requires separate Analytics calls - might be slow for many videos)
    # Optimization: We could try to fetch CTR in bulk, but Analytics API has limits on filters.
    # For now, we loop.
    print("Fetching CTR for each video (this might take a moment)...")
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    for video in videos_data:
        video['CTR (%)'] = get_video_ctr(creds, video['Video ID'])

    # 3. Get Evolution Data
    evolution_data = get_channel_evolution(creds)

    # 4. Create DataFrames
    df_videos = pd.DataFrame(videos_data)
    df_evolution = pd.DataFrame(evolution_data)

    # 5. Write to Excel
    print(f"Generating {REPORT_FILE}...")
    with pd.ExcelWriter(REPORT_FILE, engine='xlsxwriter') as writer:
        # --- Sheet 1: Video Overview ---
        df_videos.to_excel(writer, sheet_name='Videos', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Videos']
        
        # Format Columns
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3'})
        for col_num, value in enumerate(df_videos.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15) # Default width
        
        worksheet.set_column('B:B', 50) # Title column wider

        # Chart: Top 10 Videos by Views
        chart_top = workbook.add_chart({'type': 'bar'})
        # Sort by views for the chart (descending)
        df_top = df_videos.sort_values(by='Views', ascending=False).head(10)
        # We can't easily reference sorted data in Excel without writing it. 
        # Let's write the sorted data to a hidden sheet or just use the main sheet if it's sorted.
        # Simpler: Just chart the first 10 rows assuming user might sort later, 
        # OR better: Write a small summary table for the chart.
        
        # Let's create a "Dashboard" sheet for charts
        
        # --- Sheet 2: Evolution ---
        df_evolution.to_excel(writer, sheet_name='Evolution', index=False)
        worksheet_evo = writer.sheets['Evolution']
        
        # Chart: Daily Views Evolution
        chart_evo = workbook.add_chart({'type': 'line'})
        chart_evo.add_series({
            'name':       'Daily Views',
            'categories': ['Evolution', 1, 0, len(df_evolution), 0], # Date column
            'values':     ['Evolution', 1, 1, len(df_evolution), 1], # Daily Views column
        })
        chart_evo.set_title({'name': 'Daily Views (Last 30 Days)'})
        chart_evo.set_x_axis({'name': 'Date'})
        chart_evo.set_y_axis({'name': 'Views'})
        
        # Insert Chart in Evolution Sheet
        worksheet_evo.insert_chart('E2', chart_evo)

        # --- Sheet 3: Dashboard (Top Videos) ---
        # Write Top 10 data specifically for charting
        df_top.to_excel(writer, sheet_name='Dashboard', index=False)
        worksheet_dash = writer.sheets['Dashboard']
        worksheet_dash.set_column('B:B', 40)
        
        chart_bar = workbook.add_chart({'type': 'bar'})
        chart_bar.add_series({
            'name':       'Views',
            'categories': ['Dashboard', 1, 1, 10, 1], # Title
            'values':     ['Dashboard', 1, 3, 10, 3], # Views
        })
        chart_bar.set_title({'name': 'Top 10 Videos by Views'})
        chart_bar.set_style(11)
        
        # Scatter Plot: Views vs CTR
        # We need data from the 'Videos' sheet.
        chart_scatter = workbook.add_chart({'type': 'scatter'})
        chart_scatter.add_series({
            'name': 'Views vs CTR',
            'categories': ['Videos', 1, 5, len(df_videos), 5], # CTR column (F)
            'values':     ['Videos', 1, 3, len(df_videos), 3], # Views column (D)
        })
        chart_scatter.set_title({'name': 'Views vs CTR Correlation'})
        chart_scatter.set_x_axis({'name': 'CTR (%)'})
        chart_scatter.set_y_axis({'name': 'Views'})

        worksheet_dash.insert_chart('H2', chart_bar)
        worksheet_dash.insert_chart('H18', chart_scatter)

    print("Report generated successfully!")

if __name__ == '__main__':
    main()
