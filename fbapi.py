import requests
import fetcher
from time import time
import sqlite3
import os

DB_PATH = "data.db"
OLD_DB_PATH = 'names.db'

class DBConnection:
    def __init__(self):
        self.con = sqlite3.connect(DB_PATH)

    def __enter__(self):
        self.cursor = self.con.cursor()
        return self.cursor

    def __exit__(self, typ, value, traceback):
        self.cursor.close()
        self.con.commit()
        self.con.close()

def fetch_user_name(fbid):
    try:
        resp = requests.get(
            "https://www.facebook.com/app_scoped_user_id/" + str(fbid),
            headers=fetcher.Fetcher.REQUEST_HEADERS,
            allow_redirects=True)
        return resp.url.split("/")[-1]
    except:
        return None

def create_database():
    script = open('create_database.sql', 'r').read()
    with DBConnection() as c:
        c.executescript(script)
        if os.path.exists(OLD_DB_PATH):
            c.executescript("ATTACH '{path}' AS OLD; INSERT INTO Users SELECT * FROM OLD.Users;".format(path=OLD_DB_PATH))

def query_database_one(query: str, args: tuple):
    with DBConnection() as c:
        data = c.execute(query, args).fetchone()
    if data:
        return data[0]
    return None

def query_database_all(query: str, args: tuple):
    with DBConnection() as c:
        data = c.execute(query, args).fetchall()
    return data

def get_user_id(uname: str) -> str:
    return query_database_one('SELECT User_ID from Users where Profile_Name = ?', (uname,))

def get_user_name(uid: str) -> str:
    return query_database_one('SELECT Profile_Name FROM Users WHERE User_ID = ?', (uid,))

def find_user_name(query: str):
    return query_database_one("SELECT Profile_Name FROM Users WHERE Profile_Name LIKE ?", ('%' + query + '%',))

def insert_uid_uname(uid: str, uname: str):
    with DBConnection() as c:
        if query_database_one('SELECT * FROM Users WHERE User_ID = ?', (uid,)):
            c.execute('UPDATE Users SET Profile_Name = ? WHERE User_ID = ?', (uname, uid))
        else:
            c.execute('INSERT INTO Users (User_ID, Profile_Name) VALUES (?, ?)', (uid, uname))

def insert_log(uid: str, data: dict):
    mapping = {
        None: None,
        'a0': '1',
        'a2': '2',
        'p0': '3',
        'p2': '4'
    }
    with DBConnection() as c:
        c.execute('INSERT INTO Logs (User_ID, Time, Activity, VC_ID, AP_ID) VALUES (?, ?, ?, ?, ?)', (uid, data['Time'], data['Activity'], data['VC_ID'], mapping[data['type']]))

def get_logs(uid: str, timeframe: int):
    now = int(time())
    return query_database_all('SELECT Time, Activity, VC_ID, AP_ID FROM Logs where User_ID = ? and Time >= ? ORDER BY Time ASC', (uid, now - timeframe))