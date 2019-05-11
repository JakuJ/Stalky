import requests
import fetcher
import sqlite3
import os
from time import time
from typing import Optional, List, Tuple

DB_PATH = "data.db"

class DBConnection:
    """Database connection context manager"""
    def __init__(self, timeout=None):
        if timeout:
            self.con = sqlite3.connect(DB_PATH, timeout=timeout)
        else:
            self.con = sqlite3.connect(DB_PATH)

    def __enter__(self):
        self.cursor = self.con.cursor()
        return self.cursor

    def __exit__(self, _type, _value, _traceback):
        self.cursor.close()
        self.con.commit()
        self.con.close()

def fetch_user_name(fbid: str) -> Optional[str]:
    """Query Facebook API for the profile name"""
    try:
        resp = requests.get(
            "https://www.facebook.com/app_scoped_user_id/" + fbid,
            headers=fetcher.Fetcher.REQUEST_HEADERS,
            allow_redirects=True)
        return resp.url.split("/")[-1]
    except:
        return None

def create_database() -> None:
    """Create new SQLite database at DB_PATH"""
    script = open('create_database.sql', 'r').read()
    with DBConnection() as c:
        c.executescript(script)

def query_database_one(cursor: sqlite3.Cursor, query: str, args: Tuple[str, ...]) -> Optional[str]:
    """Query the database for a single record"""
    data = cursor.execute(query, args).fetchone()
    if data:
        return data[0]
    return None

def get_user_id(cursor: sqlite3.Cursor, uname: str) -> Optional[str]:
    """Get User ID from the profile name"""
    return query_database_one(cursor, 'SELECT User_ID from Users where Profile_Name = ?', (uname,))

def get_user_name(cursor: sqlite3.Cursor, uid: str) -> Optional[str]:
    """Get profile name from the User ID"""
    return query_database_one(cursor, 'SELECT Profile_Name FROM Users WHERE User_ID = ?', (uid,))

def find_user_name(cursor: sqlite3.Cursor, query: str) -> Optional[str]:
    """Search the database for a profile name matching a specified string"""
    return query_database_one(cursor, "SELECT Profile_Name FROM Users WHERE Profile_Name LIKE ?", ('%' + query + '%',))

def insert_uid_uname(cursor: sqlite3.Cursor, uid: str, uname: str) -> None:
    """Update or add a new user to the database"""
    if query_database_one(cursor, 'SELECT * FROM Users WHERE User_ID = ?', (uid,)):
        cursor.execute('UPDATE Users SET Profile_Name = ? WHERE User_ID = ?', (uname, uid))
    else:
        cursor.execute('INSERT INTO Users (User_ID, Profile_Name) VALUES (?, ?)', (uid, uname))

def insert_log(cursor: sqlite3.Cursor, uid: str, data: dict) -> None:
    """Append a new logged datapoint to the Logs table"""
    mapping = {
        None: None,
        'a0': '1',
        'a2': '2',
        'p0': '3',
        'p2': '4'
    }
    cursor.execute('INSERT INTO Logs (User_ID, Time, Activity, VC_ID, AP_ID) VALUES (?, ?, ?, ?, ?)',\
                    (uid, data['Time'], data['Activity'], data['VC_ID'], mapping[data['type']]))

Log = Tuple[str, float, float, float, float]
def get_logs(uid: str, timeframe: int) -> List[Log]:
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
    with DBConnection(timeout=20) as cursor:
        return cursor.execute(query, (uid, now - timeframe)).fetchall()