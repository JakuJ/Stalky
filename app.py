from flask import Flask, render_template, send_file
import os
import sys
import update_names
import graph
import history
from fbapi import get_user_id
import re

NAME_FILE = "names_storage.json"

application = Flask('stalky')

# prevent cached responses
@application.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@application.route('/')
def index():
    return render_template("main.html")

@application.route('/data/<string:query>')
def get_data_for_query(query):
    print('query: {query}'.format(query=query), file=sys.stderr)
    uname = ""

    for file in os.listdir('./generated_graphs/csv/'):
        if query in file:
            uname = file
            break

    print('filename: {uname}'.format(uname=uname), file=sys.stderr)
    
    if uname == "":
        return render_template("main.html")
    else:
        now = history.StatusHistory.START_TIME
        g = graph.Grapher()
        print("Updating " + uname)
        g.to_csv(get_user_id(uname[:-4]), start_time=now - 3 * graph.ONE_DAY_SECONDS, end_time=now)
        print("Done")
        return send_file("generated_graphs/csv/{uname}".format(uname=uname))

if __name__ == '__main__':
    update_names.main()
    application.run(host='localhost', port=5001, debug=True)
