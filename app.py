from flask import Flask, render_template, send_file
import os
import sys
import update_names
import graph

NAME_FILE = "names_storage.json"

app = Flask('stalky')

# prevent cached responses
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/')
def index():
    return render_template("main.html")

@app.route('/data/<string:query>')
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
        return send_file("generated_graphs/csv/{uname}".format(uname=uname))


if __name__ == '__main__':
    update_names.main()
    graph.main()
    app.run(host='localhost', port=5001, debug=True)
