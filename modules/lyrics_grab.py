#!/Users/drewhibbard/anaconda3/bin/python3

'''
Module for using Spotipy and Genius API to obtain song lyrics.  

Get list of artist names with Spotipy search and feed those into the Genius API to get lyrics.
'''

import lyricsgenius
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import pickle
import os
import time
import requests

import sys
sys.path.append('../credentials/')
import credentials

genius = lyricsgenius.Genius(credentials.genius_access_token)

auth_manager = SpotifyClientCredentials(client_id=credentials.spotify_client_id,
                                        client_secret=credentials.spotify_client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)



def get_raw_data(genre='rock',kind='artist',n=1000):
    '''
    Searches the Spotify API for your specified query, returning n results. 
    Will save results in a list and pickle it to the current directory.
    
    Genre: can feed it any genre known to Spotify.  Spotipy will grab all sub-genres
    if you feed it a generic genre.  Ex: "rock" will return results for alternative rock, soft rock, 
    hard rock, etc.
    
    Kind: 'artist', 'album', or 'song'
    '''

    query = []

    # spotify limits a query to 50 items, but you can easily work around this with a simple loop
    # and offsetting the start value
    
    for i in range(n//50):
        data = sp.search(q=f'genre:{genre}',type=kind,limit=50,offset=50*i)
        query.append(data)
            
    return query


def extract_artist_info(spotipy_search):
    '''
    Uses your Spotipy query to return a dictionary with keys equal to artist names and values
    equal to a tuple of number of followers and Spotify popularity.
    '''
    
    artists = {}
    for i in range(len(spotipy_search)):
        for artist in spotipy_search[i]['artists']['items']:
            name = artist['name']
            followers = artist['followers']['total']
            popularity = artist['popularity']
            artists[name] = (followers,popularity)
                
    return artists


def extract_song_info(artist_list):
    '''
    Input: list of artist names from get_raw_data function
    
    Returns: list of dictionaries, each being info on a single track.
    '''
    
    song_list = []
    
    for artist in artist_list:
        
        # Spotify API only allows a track query up to 2000 tracks
        # so to get around this you can get a long list of artists (again up to the 2000 limit)
        # and get n songs per artists, significantly increasing your total song list
        
        query = sp.search(q=f'artist:{artist}',limit=50,type='track')

        for i in range(len(query['tracks']['items'])):

            d = {}
            
            #parse the relevant info from the resulting json files
            
            d['id'] = query['tracks']['items'][i]['id']
            d['song_name'] = query['tracks']['items'][i]['name']
            d['artist_name'] = query['tracks']['items'][i]['album']['artists'][0]['name']
            d['album_name'] = query['tracks']['items'][i]['album']['name']
            d['popularity'] = query['tracks']['items'][i]['popularity']
            d['duration_ms'] = query['tracks']['items'][i]['duration_ms'] 
            d['explicit'] = query['tracks']['items'][i]['explicit']
            d['link'] = query['tracks']['items'][i]['external_urls']['spotify']

            song_list.append(d)
        
        time.sleep(1)
        
    return song_list

def get_song_ids(song_list):
    
    # simple function that will extract the Spotify song IDs from the large list of song dictionaries
    # which can then be fed into get_audio_features
    
    song_ids = []
    for i in range(len(song_list)):
        song_ids.append(song_list[i]['id'])
        
    return song_ids

def get_audio_features(track_list):
    '''
    Input: a list of Spotify track IDs. (Can also be other forms of unique track ID Spotify accepts).
    Returns: list of dictionaries, each dictionary being information about each song, such as
        popularity, danceability, and other audio measures.
    '''
    
    audio = []
    counter = 1
    for track in track_list:
        if counter % 50 == 0:
            time.sleep(1)
        audio += sp.audio_features(track)
    
        counter += 1
        
    return audio


def get_lyrics(artist,n_songs=100):
    '''
    Input: artist name as string and number of desired songs.
    Returns: json file with lyrics (and a whole bunch of other stuff)
    '''
    data = genius.search_artist(artist,n_songs)
    data.save_lyrics()
    
    
def extract_from_json(json_file):
    '''
    Filters for only relevant information from the lengthy json files that Genius returns.
    
    Artist name
    Song release date
    Song page views on Genius
    Song title
    Album name
    Spotify link
    lyrics
    '''
    
    song_list = []
    
    with open(json_file,'r') as f:
        data = json.load(f)
    
    for song in data['songs']:
        d = {}

        d['artist_name'] = data['name']
        d['release_date'] = song['release_date']
        try:
            d['page_views'] = song['stats']['pageviews']
        except:
            d['page_views'] = 0

        d['song_title'] = song['title']

        try:
            d['album_name'] = song['album']['name']
        except:
            d['album_name'] = 'nan'

        for provider in song['media']:
            if provider['provider'] == 'spotify':
                d['spotify_url'] = provider['url']
            else:
                d['spotify_url'] = 'nan'

        d['lyrics'] = song['lyrics']

        song_list.append(d)
        
    os.remove(json_file)
        
    return song_list
    
    
def combine_and_delete(pickle_name):
    '''
    Goes through every json file in a directory and parses it with the extract_from_json function.
    Will delete all json files and save a pickle containing all of your information.
    '''
    
    l = []
    for file in os.listdir():
        if file[-4:] == 'json':
            print(file)
            l += extract_from_json(file)
            
    with open(f'{pickle_name}.pickle','wb') as f:
        pickle.dump(l,f)
        
    print('pickle created')