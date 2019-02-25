import requests
from fetcher import Fetcher
import pandas as pd
import graph
from bs4 import BeautifulSoup

def fetch_user_name(fbid):
    try:
        resp = requests.get(
            "https://www.facebook.com/app_scoped_user_id/" + str(fbid),
            headers=Fetcher.REQUEST_HEADERS,
            allow_redirects=True)
        return resp.url.split("/")[-1]
    except:
        return "unknown"

def get_user_id(uname):
    names = pd.read_json(graph.NAME_FILE)
    return names.loc[names['profile_name'] == uname, 'id'].iloc[0]

def get_user_name(uid):
    names = pd.read_json(graph.NAME_FILE)
    return names.loc[names['id'] == uid, 'profile_name'].iloc[0]

def fetch_full_name(uid):
    response = requests.get('https://www.facebook.com/profile.php?id={uid}'.format(uid=uid),
        headers=Fetcher.REQUEST_HEADERS,
        allow_redirects=True)

    if response.history:
        print ("Request was redirected")
        for resp in response.history:
            print (resp.status_code, resp.url)
        print ("Final destination:")
        print (response.status_code, response.url)
    else:
        print ("Request was not redirected")
        print (response.status_code, response.url)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        return soup.find('title', {'id': 'pageTitle'}).text
    except:
        return ''