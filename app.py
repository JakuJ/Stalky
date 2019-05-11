from flask import Flask, render_template, send_file, request, Response
from functools import wraps
from typing import Callable
import os
import fbapi
import hashlib
import csv

AUTH_HASH_PATH = "auth_hash.txt"

application = Flask('Stalky')

def check_auth(username: str, password: str) -> bool:
    """Verifies provided credentials against the stored hash"""
    hasher = hashlib.md5()
    hasher.update(username.encode('utf-8'))
    hasher.update(password.encode('utf-8'))

    with open(AUTH_HASH_PATH, 'r') as f:
        return hasher.hexdigest() == f.read(32)

def requires_auth(f: Callable) -> Callable:
    """Enables basic authentication on web page"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if os.path.exists(AUTH_HASH_PATH):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return Response(
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'}
                )
        return f(*args, **kwargs)
    return decorated

@application.after_request
def disable_cache(response: Response) -> Response:
    """Prevents cached responses"""
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
def get_data_for_query(query: str, timespan: int, unit: str):
    print('Query: "{query}"'.format(query=query))
    
    with fbapi.DBConnection() as cursor:
        uname = fbapi.find_user_name(cursor, query)

        if not uname:
            print("Couldn't find profile name containing:", query)
            return render_template("main.html")

        uid = fbapi.get_user_id(cursor, uname)
        print('Found:', uid, uname)

    timespan_seconds = {
        'Day': 24 * 60 * 60,
        'Hour': 60 * 60,
        'Minute': 60
    }
    
    if uid:
        data = fbapi.get_logs(uid, timespan * timespan_seconds[unit])
    else:
        raise TypeError("Couldn't get logs from database")

    with open('tmp.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_NONE, escapechar='\\')
        writer.writerow(['Time', 'Activity', 'Messenger Status', 'FB App Status', 'Web Status', 'Other Status'])
        writer.writerows(data)

    print('Created data file, sending...')
    return send_file("tmp.csv")

if __name__ == '__main__':
    application.run(host='localhost', port=5001, debug=True)
