import requests
import fetcher
from time import time
import sqlite3
import os

DB_PATH = "data.db"

class DBConnection:
    """Handles automatic database transaction commiting"""
    def __init__(self, timeout=None):
        if timeout:
            self.con = sqlite3.connect(DB_PATH, timeout=timeout)
        else:
            self.con = sqlite3.connect(DB_PATH)

    def __enter__(self):
        self.cursor = self.con.cursor()
        return self.cursor

    def __exit__(self, typ, value, traceback):
        self.cursor.close()
        self.con.commit()
        self.con.close()

def fetch_user_name(fbid):
    """Query Facebook API for the profile name"""
    try:
        resp = requests.get(
            "https://www.facebook.com/app_scoped_user_id/" + str(fbid),
            headers=fetcher.Fetcher.REQUEST_HEADERS,
            allow_redirects=True)
        return resp.url.split("/")[-1]
    except:
        return None

def create_database():
    """Create new SQLite database at DB_PATH"""
    script = open('create_database.sql', 'r').read()
    with DBConnection() as c:
        c.executescript(script)

def query_database_one(query: str, args: tuple):
    """Query the database for a single record"""
    with DBConnection() as c:
        data = c.execute(query, args).fetchone()
    if data:
        return data[0]
    return None

def get_user_id(uname: str) -> str:
    """Get User ID from the profile name"""
    return query_database_one('SELECT User_ID from Users where Profile_Name = ?', (uname,))

def get_user_name(uid: str) -> str:
    """Get profile name from the User ID"""
    return query_database_one('SELECT Profile_Name FROM Users WHERE User_ID = ?', (uid,))

def find_user_name(query: str):
    """Search the database for a profile name matching a specified string"""
    return query_database_one("SELECT Profile_Name FROM Users WHERE Profile_Name LIKE ?", ('%' + query + '%',))

def insert_uid_uname(uid: str, uname: str):
    """Update or add a new user to the database"""
    with DBConnection() as c:
        if query_database_one('SELECT * FROM Users WHERE User_ID = ?', (uid,)):
            c.execute('UPDATE Users SET Profile_Name = ? WHERE User_ID = ?', (uname, uid))
        else:
            c.execute('INSERT INTO Users (User_ID, Profile_Name) VALUES (?, ?)', (uid, uname))

def insert_log(c, uid: str, data: dict):
    """Append a new logged datapoint to the Logs table"""
    mapping = {
        None: None,
        'a0': '1',
        'a2': '2',
        'p0': '3',
        'p2': '4'
    }
    c.execute('INSERT INTO Logs (User_ID, Time, Activity, VC_ID, AP_ID) VALUES (?, ?, ?, ?, ?)', (uid, data['Time'], data['Activity'], data['VC_ID'], mapping[data['type']]))

def get_logs(uid: str, timeframe: int):
    """Return log data formatted for graphing"""
    now = int(time())
    query="""
        SELECT
            datetime(Time, "unixepoch", "localtime"),
            CASE WHEN VC_ID IS NULL AND Activity = 1 THEN 0.2 ELSE 0 END,
            CASE WHEN VC_ID = 74 THEN 0.4 ELSE 0.2 END,
            CASE WHEN VC_ID = 8 THEN 0.6 ELSE 0.4 END,
            CASE WHEN VC_ID = 0 THEN 0.8 ELSE 0.6 END,
            CASE WHEN VC_ID = 10 THEN 1 ELSE 0.8 END
        FROM 
            Logs 
        WHERE 
            User_ID = ?
            AND
            Time >= ? 
        ORDER BY
            Time ASC
    """
    with DBConnection(timeout=20) as c:
        data = c.execute(query, (uid, now - timeframe)).fetchall()
    return data