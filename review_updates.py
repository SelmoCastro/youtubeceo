import os
import json
import datetime
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

# --- Configuration ---
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
TOKEN_FILE = 'token.json'
PENDING_FILE = 'pending_reviews.json'
HISTORY_FILE = 'optimization_history.json'
LOG_FILE = 'log.txt'

# Configure Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_authenticated_service():
    """Authenticates with YouTube Data API using saved token."""
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            return build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    print("Error: Valid token.json not found. Run the main script first to authenticate.")
    return None

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
            print(f"Video {video_id} not found.")
            return False

        snippet = video_response['items'][0]['snippet']
        snippet['title'] = title
        snippet['description'] = description
        snippet['tags'] = tags

        service.videos().update(
            part='snippet',
            body={'id': video_id, 'snippet': snippet}
        ).execute()
        print("Metadata updated successfully.")

        # 2. Update Thumbnail (if exists)
        if thumbnail_path and os.path.exists(thumbnail_path):
            print(f"Uploading thumbnail from {thumbnail_path}...")
            service.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("Thumbnail uploaded successfully.")
        
        return True
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        logging.error(f"Update error for {video_id}: {e}")
        return False

def main():
    print("--- YouTube SEO Reviewer ---")
    pending = load_json(PENDING_FILE)
    history = load_json(HISTORY_FILE)
    
    if not pending:
        print("No pending reviews found.")
        return

    service = get_authenticated_service()
    if not service:
        return

    # Iterate over a copy of keys to allow modification of dict
    for video_id in list(pending.keys()):
        item = pending[video_id]
        
        print("\n" + "="*50)
        print(f"Video ID: {video_id}")
        print(f"Current Title: {item['current_title']}")
        print("-" * 20)
        print(f"NEW Title:       {item['new_title']}")
        print(f"NEW Description: {item['new_description'][:100]}...") # Show snippet
        print(f"NEW Tags:        {item['new_tags']}")
        print(f"Thumbnail:       {item['thumbnail_path']}")
        print("="*50)

        choice = input("Approve this change? (y/n/skip/quit): ").lower().strip()

        if choice == 'y':
            success = update_video_on_youtube(
                service, 
                video_id, 
                item['new_title'], 
                item['new_description'], 
                item['new_tags'],
                item['thumbnail_path']
            )
            
            if success:
                # Update History
                history[video_id] = datetime.datetime.now().isoformat()
                save_json(HISTORY_FILE, history)
                
                # Remove from pending
                del pending[video_id]
                save_json(PENDING_FILE, pending)
                print("Change applied and removed from pending list.")
            else:
                print("Failed to apply change.")

        elif choice == 'n':
            # Reject: remove from pending
            del pending[video_id]
            save_json(PENDING_FILE, pending)
            print("Rejected. Removed from pending list.")
        
        elif choice == 'skip':
            print("Skipped.")
        
        elif choice == 'quit':
            break

    print("\nReview session finished.")

if __name__ == '__main__':
    main()
