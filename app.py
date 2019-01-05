from flask import Flask, render_template, send_file, request, Response
from functools import wraps
import os
import sys
import update_names
import graph
from fbapi import get_user_id
import re
import time
import pandas as pd
import hashlib

NAME_FILE = "names_storage.json"
AUTH_HASH_PATH = "auth_hash.txt"

application = Flask('stalky')

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    hasher = hashlib.md5()
    hasher.update(username.encode('utf-8'))
    hasher.update(password.encode('utf-8'))
    with open(AUTH_HASH_PATH, 'r') as f:
        return hasher.hexdigest() == f.read(32)

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\nYou have to login with proper credentials',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# prevent cached responses
@application.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@application.route('/')
@requires_auth
def index():
    return render_template("main.html")

@application.route('/data/<string:query>')
@requires_auth
def get_data_for_query(query):
    print('query: {query}'.format(query=query), file=sys.stderr)
    uname = ""

    if not os.path.exists(graph.CSV_OUTPUT_DIR):
        os.makedirs(graph.CSV_OUTPUT_DIR)

    for name in pd.read_json(NAME_FILE).loc[:, 'profile_name']:
        if query in name:
            uname = name
            break

    print('found: {uname}'.format(uname=uname), file=sys.stderr)
    
    if uname == "":
        return render_template("main.html")
    else:
        g = graph.Grapher()
        now = int(time.time())
        print("Updating " + uname)
        g.to_csv(get_user_id(uname), start_time=now - 3 * graph.ONE_DAY_SECONDS, end_time=now)
        print("Done")
        return send_file("{path}/{uname}.csv".format(path=graph.CSV_OUTPUT_DIR, uname=uname))

if __name__ == '__main__':
    update_names.main()
    application.run(host='localhost', port=5001, debug=True)
