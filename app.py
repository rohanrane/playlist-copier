import os
import json
import pickle

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = '1'
os.environ["OAUTH_FILE"] = 'oauth2_installed.json'

moosic_id = 'PL9d2u7QMazbWOn1eGJuTQo3x64otSujB9'
liked_songs = 'LLPkmyUMgr1Fj_Yv3p3WD7nw'

def get_credentials(scopes):
    try:
        with open('credentials', 'rb') as stream:
            credentials = pickle.load(stream)

    except:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            os.getenv('OAUTH_FILE'), scopes)
        credentials = flow.run_console()

        with open('credentials', 'wb') as stream:
            pickle.dump(credentials, stream)
    
    return credentials

def get_playlist(youtube_client, playlist_id, recent=False):
    playlist = {'playlistId': playlist_id, 'items': []}
    current_page_token = None

    while True:
        try:
            request = youtube_client.playlistItems().list(
                part="snippet",
                maxResults=50,
                playlistId=playlist_id,
                pageToken=current_page_token
            )
            response = request.execute()
        except Exception as e:
            print(e)

        for item in response.get('items', []):
            try:
                del item.get('snippet')['thumbnails']
            except:
                response.get('items', []).remove(item)
                print('Deleted Video: https://www.youtube.com/watch?v={}'.format(item.get('snippet', {}).get('resourceId', {}).get('videoId')))

        playlist.get('items').extend(response.get('items', []))
        current_page_token = response.get('nextPageToken', '')
        
        if current_page_token == '' or recent: 
            break

    return playlist

def update_playlist(youtube_client, playlist_id, items):
    current_playlist = load_from_file('moosic.json')
    current_items = current_playlist.get('items')

    for item in items:
        resource_id = item.get('snippet').get('resourceId')

        if not any(current_item.get('snippet').get('resourceId') == resource_id for current_item in current_items):
            try:
                request = youtube_client.playlistItems().insert(
                part="snippet",
                body={
                    'snippet': {
                        'playlistId': moosic_id,
                        'resourceId': resource_id
                        }
                    }
                )
                response = request.execute()
                print('Updated Playlist with {}'.format(resource_id))
            except Exception as e:
                print(e)
        else:
            print('Skipping {}. Already in Playlist'.format(resource_id))

def write_to_file(filename, data):
    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=4)

def load_from_file(filename):
     with open(filename, 'r') as infile:
        return json.loads(infile.read())

def main():
    scopes = ["https://www.googleapis.com/auth/youtube"]

    api_service_name = 'youtube'
    api_version = 'v3'

    # Get credentials and create an API client
    credentials = get_credentials(scopes)
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    #playlist = get_playlist(youtube, moosic_id)
    playlist = get_playlist(youtube, 'PL9d2u7QMazbV3BQbnEqoQK6VIb4aqM28l')
    write_to_file('power_hour.json', playlist)
    '''
    #playlist = load_from_file('liked_songs.json')
    playlist = get_playlist(youtube, liked_songs, recent=True)
    items = playlist.get('items')
    items.reverse()

    update_playlist(youtube, moosic_id, items)

    '''

if __name__ == "__main__":
    main()