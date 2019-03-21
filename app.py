from flask import Flask, render_template, send_file, request, Response
from functools import wraps
import os
import fbapi
import hashlib
import csv

AUTH_HASH_PATH = "auth_hash.txt"

application = Flask('stalky')

def check_auth(username: str, password: str) -> bool:
    hasher = hashlib.md5()
    hasher.update(username.encode('utf-8'))
    hasher.update(password.encode('utf-8'))
    
    with open(AUTH_HASH_PATH, 'r') as f:
        return hasher.hexdigest() == f.read(32)

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\nYou have to login with proper credentials',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if os.path.exists(AUTH_HASH_PATH):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
        return f(*args, **kwargs)
    return decorated

# Prevent cached responses
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

@application.route('/query/<string:query>/<int:timespan>/<string:unit>')
@requires_auth
def get_data_for_query(query, timespan, unit):
    print('Query: "{query}"'.format(query=query))
    uname = fbapi.find_user_name(query)
    if not uname:
        print("Couldn't find profile name containing:", query)
        return render_template("main.html")
    else:
        uid = fbapi.get_user_id(uname)
        print('Found:', uid, uname)

        timespan_seconds = {
            'day': 24 * 60 * 60,
            'hour': 60 * 60,
            'minute': 60
        }

        data = fbapi.get_logs(uid, timespan * timespan_seconds[unit])
        with open('tmp.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_NONE, escapechar='\\')
            writer.writerow(['Time', 'Activity', 'Messenger Status', 'FB App Status', 'Web Status', 'Other Status'])
            writer.writerows(data)

        print('Created data file, sending...')
        return send_file("tmp.csv")

if __name__ == '__main__':
    application.run(host='localhost', port=5001, debug=True)
