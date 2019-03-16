import json
import os
import time
import requests
import fbapi
import sqlite3

def get_secret(field: str) -> object:
    with open("SECRETS.json") as f:
        return json.load(f)[field]

SLEEP_TIME = 1
LOG_DATA_DIR = "data"

secrets = {
    'uid': get_secret('uid'),
    'cookie': get_secret('cookie'),
    'client_id': get_secret('client_id')
}

def encode_type(act_type: str) -> str:
    mapping = {
        None: '0',
        'a0': '1',
        'a2': '2',
        'p0': '3',
        'p2': '4'
    }
    return mapping[act_type]

def json_to_csv(data: object) -> str:
    statuses = ['1' if data['vc'] == i else '0' for i in [0, 8, 10, 74]]
    statuses.insert(0, str(int(data['active'])))
    statuses.append(encode_type(data['type']))

    return str(data['time']) + "," + (",".join(statuses))

class Fetcher():
    # Headers to send with every request.
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
        # Create data directory if not already existing
        if not os.path.exists(LOG_DATA_DIR):
            os.makedirs(LOG_DATA_DIR)

        # Create users database if not already existing
        if not os.path.exists(fbapi.DB_PATH):
            conn = sqlite3.connect(fbapi.DB_PATH)
            c = conn.cursor()
            c.execute('CREATE TABLE Users (User_ID CHAR(20), Profile_Name NVARCHAR)')
            conn.commit()
            conn.close()

        self.reset_params()

    def make_request(self) -> object:
        # Load balancing is for chumps. Facebook can take it.
        url = "https://edge-chat.facebook.com/pull"
        response_obj = requests.get(url, params=self.params, headers=self.REQUEST_HEADERS)

        try:
            raw_response = response_obj.text
            if not raw_response:
                return None
            if raw_response.startswith(self.JSON_PAYLOAD_PREFIX):
                data = raw_response[len(self.JSON_PAYLOAD_PREFIX) - 1:].strip()
                data = json.loads(data)
            else:
                # Didn't start with for (;;); ... Maybe it's unprotected JSON?
                data = json.loads(raw_response)
        except ValueError as e:
            print(str(e))
            return None
        
        print("Response:" + str(data))
        return data

    def log_lat(self, uid: str, record: object, activity_key: str):
        # Update names' database if necessary
        uname = fbapi.get_user_name(uid)
        if not uname:
            uname = fbapi.fetch_user_name(uid)
            fbapi.insert_uid_uname(uid, uname)
        
        # Initialize files with valid CSV headers
        filepath = "{logdir}/{uname}.csv".format(logdir=LOG_DATA_DIR, uname=uname)
        if not os.path.exists(filepath):
            with open(filepath, "w") as f:
                f.write("time,active,vc_0,vc_8,vc_10,vc_74,type\n")

        with open(filepath, "a") as f:
            user_data = dict()
            if activity_key == 'a':
                try:
                    user_data['time'] = record['la']
                except:
                    print("ERROR: missing 'la' for {uid}".format(uid=uid))
                    return
            elif activity_key == 'p':
                try:
                    user_data['time'] = record['lat']
                except:
                    print("ERROR: missing 'lat' for {uid}".format(uid=uid))
                    return

            user_data['active'] = True
            
            if not 'vc' in record:
                user_data['vc'] = None
            else:
                if record['vc'] in [0, 8, 10, 74]: #TODO 'vc': 2
                    user_data['vc'] = record['vc']
                else:
                    print('Invalid vc value: ' + str(record['vc']))
                    user_data['vc'] = None

            # Now log their current status stored sometimes in 'a' or 'p' property
            if activity_key in record:
                user_data['type'] = activity_key + str(record[activity_key])
            else:
                user_data['type'] = None

            f.write(json_to_csv(user_data))
            f.write("\n")

            user_data = {
                'time': int(time.time()),
                'active': False,
                'vc': None,
                'type': None
            }
            f.write(json_to_csv(user_data))
            f.write("\n")

    def start_request(self):
        resp = self.make_request()
        if resp is None:
            print("Got error from request, restarting...")
            self.reset_params()
            return

        # We got info about which pool/sticky we should be using I think??? Something to do with load balancers?
        if "lb_info" in resp:
            self.params["sticky_pool"] = resp["lb_info"]["pool"]
            self.params["sticky_token"] = resp["lb_info"]["sticky"]

        if "seq" in resp:
            self.params["seq"] = resp["seq"]

        if "ms" in resp:
            for item in resp["ms"]:
                # The online/offline info we're looking for.
                if item["type"] == "buddylist_overlay":
                    # Find the key with all the message details, that one is the UID.
                    for key in item["overlay"]:
                        if type(item["overlay"][key]) == dict:
                            uid = key
                            # Log the LAT in this message.
                            self.log_lat(uid, item["overlay"][uid], 'a')
                # This list contains the last active times (lats) of users.
                if "buddyList" in item:
                    for uid in item["buddyList"]:
                        if "lat" in item["buddyList"][uid]:
                            self.log_lat(uid, item["buddyList"][uid], 'p')

    def reset_params(self):
        self.params = {
            # No idea what this is.
            'cap': '8',
            # No idea what this is.
            'cb': '2qfi',
            # No idea what this is.
            'channel': 'p_' + secrets['uid'],
            'clientid': secrets['client_id'],
            'format': 'json',
            # Is this my online status?
            'idle': '0',
            # No idea what this is.
            'isq': '173180',
            # Whether to stream the HTTP GET request. We don't want to!
            # 'mode': 'stream',
            # Is this how many messages we have got from Facebook in this session so far?
            # Previous value: 26
            'msgs_recv': '0',
            # No idea what this is.
            'partition': '-2',
            # No idea what this is.
            'qp': 'y',
            # Set starting sequence number to 0.
            # This number doesn't seem to be necessary for getting the /pull content, since setting it to 0 every time still gets everything as far as I can tell. Maybe it's used for #webscale reasons.
            'seq': '0',
            'state': 'active',
            'sticky_pool': 'atn2c06_chat-proxy',
            'sticky_token': '0',
            'uid': secrets['uid'],
            'viewer_uid': secrets['uid'],
            'wtc': '171%2C170%2C0.000%2C171%2C171'
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
