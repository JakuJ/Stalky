import argparse as ap
import json
import os
import time

import requests

import graph

secrets = ap.Namespace()

# Load the secrets from file so some scrublord like me doesn't accidentally commit them to git.
with open("SECRETS.txt") as f:
    for line in f:
        vals = line.strip().split('=', 1)
        setattr(secrets, vals[0].lower(), vals[1])

SLEEP_TIME = 1

OFFLINE_STATUS_JSON = """{"lat": "offline", "vc_0": "invisible", "vc_8": "invisible", "vc_10": "invisible", "status": "invisible", "vc_74": "invisible"}"""
ACTIVE_STATUS_JSON = """{ "lat": "online", "vc_0": "invisible", "vc_8": "invisible", "vc_10": "invisible", "status": "active", "vc_74": "invisible"}"""
# p0 | p2 | a2
# 1789 | 621 | 61
# FORMER WEB STATUS
VC0_ACTIVE = """{ "lat": "online", "vc_0": "active", "vc_8": "invisible", "vc_10": "invisible", "status": "active", "vc_74": "invisible"}"""
# 966 | 928 | 320
# FORMER MESSENGER STATUS
VC74_ACTIVE = """{ "lat": "online", "vc_0": "invisible", "vc_8": "invisible", "vc_10": "invisible", "status": "active", "vc_74": "active"}"""
# 182 | 160 | 38
# FORMER FB APP STATUS
VC8_ACTIVE = """{ "lat": "online", "vc_0": "invisible", "vc_8": "active", "vc_10": "invisible", "status": "active", "vc_74": "invisible"}"""
# 5 | 2 | 0
# FORMER OTHER STATUS
VC10_ACTIVE = """{ "lat": "online", "vc_0": "invisible", "vc_8": "invisible", "vc_10": "active", "status": "active", "vc_74": "invisible"}"""
# vc: 2 is also a thing apparently
# TODO Crack VC: 2
class Fetcher():
    # Headers to send with every request.
    REQUEST_HEADERS = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, sdch',
        'accept-language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
        'cookie': secrets.cookie,
        'dnt': '1',
        'origin': 'https://www.facebook.com',
        'referer': 'https://www.facebook.com/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36'
    }

    # Hey hey, Facebook puts this in front of all their JSON to prevent hijacking. But don't worry, we're ~verified secure~.
    JSON_PAYLOAD_PREFIX = "for (;;); "

    def __init__(self, log_path):
        if not os.path.exists(graph.LOG_DATA_DIR):
            os.makedirs(graph.LOG_DATA_DIR)
        self.reset_params()
        self.excludes = []
        if hasattr(secrets, 'excludes'):
            self.excludes = secrets.excludes.split(',',1)
        self.log_path = log_path

    def make_request(self):
        # Load balancing is for chumps. Facebook can take it.
        url = "https://5-edge-chat.facebook.com/pull"
        response_obj = requests.get(url, params=self.params, headers=self.REQUEST_HEADERS)

        try:
            raw_response = response_obj.text
            if not raw_response:
                return None
            if raw_response.startswith(self.JSON_PAYLOAD_PREFIX):
                data = raw_response[len(self.JSON_PAYLOAD_PREFIX) - 1:].strip()
                data = json.loads(data)
            else:
                # If it didn't start with for (;;); then something weird is happening.
                # Maybe it's unprotected JSON?
                data = json.loads(raw_response)
        except ValueError as e:
            print(str(e))
            return None
        
        with open(self.log_path, 'a') as f:
            print("Response:" + str(data), file=f)
        
        print("Response:" + str(data))
        return data


    def _log_lat(self, uid, record, activity_key):
        if not uid in self.excludes:
            with open("log/{uid}.txt".format(uid=uid), "a") as f:
                # Now add an online status at the user's LA(T).
                user_data = []
                if activity_key == 'a':
                    try:
                        user_data.append(str(record['la']))
                    except:
                        print('')
                elif activity_key == 'p':
                    user_data.append(str(record['lat']))
                if not 'vc' in record:
                    user_data.append(ACTIVE_STATUS_JSON)
                else:
                    if record['vc'] == 0:
                        user_data.append(VC0_ACTIVE)
                    elif record['vc'] == 8:
                        user_data.append(VC8_ACTIVE)
                    elif record['vc'] == 10:
                        user_data.append(VC10_ACTIVE)
                    elif record['vc'] == 74:
                        user_data.append(VC74_ACTIVE)
                    else:
                        print('Invalid vc value: ' + str(record['vc']))
                        user_data.append(ACTIVE_STATUS_JSON)

                f.write("|".join(user_data))
                f.write("\n")

                # Now log their current status stored sometimes in 'a' or 'p' property
                # if activity_key in record:
                #     with open("log/{uid}.txt".format(uid=uid), "a") as f:
                #         user_data = []
                #         user_data.append(str(time.time()))
                #         if str(record[activity_key]) == '2':
                #             user_data.append(ACTIVE_STATUS_JSON)
                #         elif str(record[activity_key]) == '0':
                #             user_data.append(OFFLINE_STATUS_JSON)
                #         f.write("|".join(user_data))
                #         f.write("\n")

                # Assume the user is currently offline, since we got a lat for them. (This is guaranteed I think.)
                user_data = []
                user_data.append(str(time.time()))
                user_data.append(OFFLINE_STATUS_JSON)
                f.write("|".join(user_data))
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
                            self._log_lat(uid, item["overlay"][uid], 'a')

                # This list contains the last active times (lats) of users.
                if "buddyList" in item:
                    for uid in item["buddyList"]:
                        if "lat" in item["buddyList"][uid]:
                            self._log_lat(uid, item["buddyList"][uid], 'p')



    def reset_params(self):
        self.params = {
            # No idea what this is.
            'cap': '8',
            # No idea what this is.
            'cb': '2qfi',
            # No idea what this is.
            'channel': 'p_' + secrets.uid,
            'clientid': secrets.client_id,
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
            'uid': secrets.uid,
            'viewer_uid': secrets.uid,
            'wtc': '171%2C170%2C0.000%2C171%2C171'
        }


if __name__ == "__main__":
    f = Fetcher(log_path="fetcher_log.txt")
    while True:
        try:
            f.start_request()
            time.sleep(SLEEP_TIME)
        except UnicodeDecodeError:
            f.reset_params()
            print("UnicodeDecodeError!")
