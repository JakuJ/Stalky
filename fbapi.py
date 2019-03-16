import requests
import fetcher
import sqlite3

DB_PATH = "names.db"

def fetch_user_name(fbid):
    try:
        resp = requests.get(
            "https://www.facebook.com/app_scoped_user_id/" + str(fbid),
            headers=fetcher.Fetcher.REQUEST_HEADERS,
            allow_redirects=True)
        return resp.url.split("/")[-1]
    except:
        return None

def query_database_one(query: str, args: tuple):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    data = c.execute(query, args).fetchone()
    conn.close()
    
    if data:
        return data[0]
    return None

def get_user_id(uname: str) -> str:
    return query_database_one('SELECT User_ID from Users where Profile_Name = ?', (uname,))

def get_user_name(uid: str) -> str:
    return query_database_one('SELECT Profile_Name FROM Users WHERE User_ID = ?', (uid,))

def find_user_name(query: str):
    return query_database_one("SELECT Profile_Name FROM Users WHERE Profile_Name LIKE ?", ('%' + query + '%',))

def insert_uid_uname(uid: str, uname: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if query_database_one('SELECT * FROM Users WHERE User_ID = ?', (uid,)):
        c.execute('UPDATE Users SET Profile_Name = ? WHERE User_ID = ?', (uname, uid))
    else:
        c.execute('INSERT INTO Users (User_ID, Profile_Name) VALUES (?, ?);', (uid, uname))
    conn.commit()
    conn.close()