'''
Module for a simple song recommendation app on Streamlit.  Recommends metal songs or artists based on user input, after analyzing the similarities in audio features such as loudness, energy, etc.
'''

import streamlit as st
import pickle
import numpy as np
import pandas as pd

# open various saved pickles for optimized file loading speed

# artist similarity sparse matrix
with open('artist_scores.pickle','rb') as rf:
    artist_scores = pickle.load(rf)
    
# song similarity sparse matrix
with open('song_similarities_sparse.pickle','rb') as rf:
    song_similarities = pickle.load(rf)
    
# song dataframe to look up "close" songs
with open('song_df.pickle','rb') as rf:
    song_df = pickle.load(rf)
    
# list of 1000 metal artists
with open('metal_artists.pickle','rb') as rf:
    metal_artists = pickle.load(rf)
    
# list of ~50,000 metal songs
with open('song_names.pickle','rb') as rf:
    song_names = pickle.load(rf)
    
    
def make_clickable(url, text):
    '''
    Will make any link a hyperlink of the given text.
    '''
    return f'<a target="_blank" href="{url}">{text}</a>'

def recommend_songs(song,artist):
    '''
    Input: song title and song artist (auto-complete lists are provided to avoid typos)
    Returns: 10 closest songs in terms of audio features
    '''
    
    # obtain index of the given song
    song_ind = song_df.index[(song_df.song_name==song) & (song_df.artist_name==artist)][0]
    
    # get the indices of the 20 closest songs from the sparse matrix
    result = pd.DataFrame(song_similarities[:,song_ind].toarray()).sort_values(by=0,ascending=False).head(20).index
    
    # sort by popularity and return the top 10
    filtered = song_df.iloc[result,:].sort_values('popularity',ascending=False).head(10)
    
    # make sure users can open the link
    filtered['link'] = filtered['link'].apply(make_clickable,args=('Open in Spotify',))
    
    return filtered


def recommend_artists(artist):
    '''
    Input: a metal artist
    Returns: 10 nearest artists in terms of aggregated audio features
    '''
    
    # obtain indices of closest artists
    data = pd.concat([artist_scores.iloc[artist_ind-20:artist_ind],artist_scores.iloc[artist_ind+1:artist_ind+21]])
    
    # return ten most popular
    filtered = data[['artist_name','popularity']].sort_values('popularity',ascending=False).head(10)
    
    return filtered


st.markdown(
    """
    <style>
    .reportview-container {
        background: url("https://cdn.architecturendesign.net/wp-content/uploads/2019/02/AD-Two-Elderly-Dudes-Went-To-A-Heavy-Metal-Concert-01.jpg")
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('''<h1> <font color='white'>A Simple Recommendation System for Metal Music</font></h1>''',unsafe_allow_html=True)
st.markdown('''<font color=‘yellow’>I want recommendations by:</font>''', unsafe_allow_html=True)

rec_type = st.selectbox('',['artist','song'])

if rec_type == 'song':

    song = st.selectbox('Choose a Song',options = song_names)
    artist = st.selectbox('Choose an Artist',options = metal_artists)
    
    if st.button('Go'):
        song_ind = song_df.index[(song_df.song_name==song) & (song_df.artist_name==artist)][0]
        
        song_predictions = recommend_songs(song,artist).to_html(escape=False)

        st.write(song_predictions, unsafe_allow_html = True)

elif rec_type == 'artist':

    artist = st.selectbox('Choose an Artist',options=metal_artists)
    
    if st.button('Go'):
        
        artist_ind = artist_scores.index[artist_scores.artist_name==artist][0]
        artist_predictions = recommend_artists(artist).to_html(escape=False)

        st.write(artist_predictions,unsafe_allow_html=True)