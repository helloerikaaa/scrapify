import requests
import pandas as pd
import base64
import argparse
import json
from tqdm import tqdm

base_endpoint = 'https://api.spotify.com/v1'
# Add your own client keys from the spotify console
client_id = ''
client_secret = ''

def get_token(client_id, client_secret):
    token_url = 'https://accounts.spotify.com/api/token'
    # Token must be encoded to make requests
    token_encoded = base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8'))
    params = {'grant_type': 'client_credentials'}
    header = {'Authorization': 'Basic ' + str(token_encoded, 'utf-8')}
    
    r = requests.post(token_url, data=params, headers=header)
    
    if r.status_code != 200:
        print(f'Error in the request: {r.json()}')
        return None
    
    print('Valid token for {} seconds'.format(r.json()['expires_in']))
    return r.json()['access_token']


def get_artist_id(artist_name, header):
    search_endpoint = '/search'
    search_url = base_endpoint + search_endpoint
    search_params = {'q': artist_name, 'type': 'artist', 'market': 'MX'}
    search_result = requests.get(search_url, headers=header, params=search_params)
    
    df = pd.DataFrame(search_result.json()['artists']['items'])
    id_artist = df.sort_values(by='popularity', ascending=False).iloc[0]['id']

    return id_artist

def get_artist_albums(artist_id, header, return_name=False, page_limit=50):
    albums_list = []
    
    albums_endpoint = '/artists/{}/albums'.format(artist_id)
    albums_url = base_endpoint + albums_endpoint
    
    params = {'limit': page_limit,
              'offset': 0,
              'country': 'MX'
             }
    
    albums_request = requests.get(albums_url, params=params, headers=header)
    print(albums_request.status_code)
    
    if albums_request.status_code != 200:
        print('Error in the request ', albums_request.json())
        return None
    
    if return_name:
        albums_list += [(item['id'], item['name']) for item in albums_request.json()['items']]
    else:
        albums_list += [item['id'] for item in albums_request.json()['items']]
    
    # Request of all result pages
    while albums_request.json()['next']:
        next_request = requests.get(albums_request.json()['next'], headers=header)
        if return_name:
            albums_list += [(item['id'], item['name']) for item in albums_request.json()['items']]
        else:
            albums_list += [item['id'] for item in albums_request.json()['items']]
        
    return albums_list

def get_album_tracks(album_id, header):
    tracks_list = []
    
    album_endpoint = '/albums/{}/tracks'.format(album_id)
    album_url = base_endpoint + album_endpoint
    
    album_request = requests.get(album_url, headers=header)
    
    if album_request.status_code != 200:
        print('Error in the request ', album_request.json())
        return None
    
    tracks_list += [(item['id'], item['name']) for item in album_request.json()['items']]

    return tracks_list


if __name__ == '__main__':
    token = get_token(client_id, client_secret)
    # Build the desired token
    header = {'Authorization': 'Bearer {}'.format(token)}

    results = {}

    parser = argparse.ArgumentParser()
    # Add artist name with '+' instead of spaces
    parser.add_argument('artist', help="Name of the artist", type=str)
    args = parser.parse_args()

    artist_id = get_artist_id(args.artist, header)
    albums_list = get_artist_albums(artist_id, header, return_name=True)

    results['artist_id'] = artist_id

    print('Scraping...')
    for album in tqdm(albums_list):
        results[album[1]] = [track[1] for track in get_album_tracks(album[0], header)]
    print('Results saved!')

    with open('results.json', 'w') as fp:
        json.dump(results, fp, indent=4)
