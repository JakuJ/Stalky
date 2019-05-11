import json
import os
import time
import requests
import fbapi
import sqlite3
from typing import Optional

SECRETS_PATH = "SECRETS.json"
SLEEP_TIME = 1
VC_TYPES = [0, 2, 8, 10, 74]

def get_secret(field: str) -> str:
    """Read a field from the secrets file"""
    with open(SECRETS_PATH) as f:
        return json.load(f)[field]

secrets = {
    'uid': get_secret('uid'),
    'cookie': get_secret('cookie'),
    'client_id': get_secret('client_id')
}

class Fetcher():
    """Handles data fetching and logging"""
    REQUEST_HEADERS = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, sdch',
        'accept-language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
        'cookie': secrets['cookie'],
        'dnt': '1',
        'origin': 'https://www.facebook.com',
        'referer': 'https://www.facebook.com/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36'
    }

    # Facebook puts this in front of all their JSON to prevent hijacking.
    JSON_PAYLOAD_PREFIX = "for (;;); "

    def __init__(self):
        self.reset_params()
        if not os.path.exists(fbapi.DB_PATH):
            fbapi.create_database()

    def make_request(self) -> Optional[dict]:
        """Make a request to Facebook's internal API"""
        url = "https://edge-chat.facebook.com/pull"
        response_obj = requests.get(url, params=self.params, headers=self.REQUEST_HEADERS, timeout=60)
        try:
            raw_response = response_obj.text
            if not raw_response:
                return None
            
            if raw_response.startswith(self.JSON_PAYLOAD_PREFIX):
                data = json.loads(raw_response[len(self.JSON_PAYLOAD_PREFIX) - 1:].strip())
            else:
                data = json.loads(raw_response)
            
            print("--- Response ---\n" + str(data))
            return data
        except ValueError as e:
            print(str(e))
            return None

    def log_lat(self, cursor: sqlite3.Cursor, uid: str, record: dict, activity_key: str) -> None:
        """Log received information to the database"""
        # Update user's info if necessary
        uname = fbapi.get_user_name(cursor, uid)
        if not uname:
            # try to get uname from FB
            uname = fbapi.fetch_user_name(uid)
            fbapi.insert_uid_uname(cursor, uid, uname)

        # Extract last active time
        user_data = dict()
        if activity_key == 'a':
            try:
                user_data['Time'] = record['la']
            except:
                print("ERROR: missing 'la' for {uid}".format(uid=uid))
                return
        elif activity_key == 'p':
            try:
                user_data['Time'] = record['lat']
            except:
                print("ERROR: missing 'lat' for {uid}".format(uid=uid))
                return

        user_data['Activity'] = True
        
        # Extract activity type info
        if not 'vc' in record:
            user_data['VC_ID'] = None
        else:
            if record['vc'] in VC_TYPES:
                user_data['VC_ID'] = record['vc']
            else:
                print('Invalid vc value: ' + str(record['vc']))
                user_data['VC_ID'] = None

        # Extract current A/P property
        if activity_key in record:
            user_data['type'] = activity_key + str(record[activity_key])
        else:
            user_data['type'] = None

        fbapi.insert_log(cursor, uid, user_data)
        
        # Assume inactivity at request time
        user_data = {
            'Time': int(time.time()),
            'Activity': False,
            'VC_ID': None,
            'type': None
        }
        fbapi.insert_log(cursor, uid, user_data)

    def start_request(self) -> None:
        """Query the internal API and log all data"""
        resp = self.make_request()
        if resp is None:
            print("Got error from request, restarting...")
            self.reset_params()
            return

        # Info about which pool/sticky we should be using. Probably something to do with the load balancers.
        if "lb_info" in resp:
            self.params["sticky_pool"] = resp["lb_info"]["pool"]
            self.params["sticky_token"] = resp["lb_info"]["sticky"]

        # Request sequence number
        if "seq" in resp:
            self.params["seq"] = resp["seq"]

        # The response message
        if "ms" in resp:
            # Timeout for handling database write locks
            with fbapi.DBConnection(timeout=60) as cursor:
                for item in resp["ms"]:
                    # The online/offline info
                    if item["type"] == "buddylist_overlay":
                        # The key with all the message details is the UID
                        for key in item["overlay"]:
                            if type(item["overlay"][key]) == dict:
                                self.log_lat(cursor, key, item["overlay"][key], 'a')
                    # List containing user last active times
                    if "buddyList" in item:
                        for uid in item["buddyList"]:
                            if "lat" in item["buddyList"][uid]:
                                self.log_lat(cursor, uid, item["buddyList"][uid], 'p')

    def reset_params(self) -> None:
        self.params = {
            # ? No idea what these are
            'cap': '8',
            'cb': '2qfi',
            'channel': 'p_' + secrets['uid'],
            'isq': '173180',
            'partition': '-2',
            'qp': 'y',
            'wtc': '171%2C170%2C0.000%2C171%2C171',
            # ? My online status
            'idle': '0',
            # ? Messages received so far
            'msgs_recv': '0',
            # ? Set starting sequence number to 0
            'seq': '0',
            'clientid': secrets['client_id'],
            'format': 'json',
            'state': 'active',
            'sticky_pool': 'atn2c06_chat-proxy',
            'sticky_token': '0',
            'uid': secrets['uid'],
            'viewer_uid': secrets['uid']
        }

if __name__ == "__main__":
    f = Fetcher()
    while True:
        try:
            f.start_request()
            time.sleep(SLEEP_TIME)
        except UnicodeDecodeError:
            f.reset_params()
            print("UnicodeDecodeError!")
