import requests
from fetcher import Fetcher
import pandas as pd
import graph

def fetch_user_name(fbid):
    resp = requests.get(
        "https://www.facebook.com/app_scoped_user_id/" + str(fbid),
        headers=Fetcher.REQUEST_HEADERS,
        allow_redirects=True)
    return resp.url.split("/")[-1]

def get_user_id(uname):
    names = pd.read_json(graph.NAME_FILE)
    return names.loc[names['name'] == uname, 'id'].iloc[0]

def get_user_name(uid):
    names = pd.read_json(graph.NAME_FILE)
    return names.loc[names['id'] == uid, 'name'].iloc[0]
