# app.py
# Copyright (C) 2021  Qijun Gu
# Modified to add PyAudio speaker/mic capture

from flask import Flask, request, flash, session
from flask_bootstrap import Bootstrap
from flask.templating import render_template
import json, argparse
from screen import screenlive, audiolive   # import both
from werkzeug.utils import redirect

secret_key = u'f71b10b68b1bc00019cfc50d6ee817e75d5441bd5db0bd83453b398225cede69'

app = Flask(__name__)
app.secret_key = secret_key
Bootstrap(app)

###### general ##########################################
@app.route('/')
def welcome():
    session.clear()
    if len(screenlive.password) == 0:
        session['access'] = True
        return render_template("screen.html")
    else:
        return render_template("login.html")

@app.route('/login', methods=['POST'])
def login():
    session.clear()
    if len(screenlive.password) == 0:
        session['access'] = True
        return render_template("screen.html")

    p = request.form["password"]
    if p == screenlive.password:
        session['access'] = True
        return render_template("screen.html")
    else:
        session.clear()
        flash("Wrong password")
        return render_template("login.html")

@app.route('/screenfeed/', methods=["POST"])
def screenfeed():
    if 'access' in session and session['access']:
        return json.dumps([True, screenlive.gen()])
    else:
        redirect('/')

# route for audio
@app.route('/audiofeed/', methods=["POST"])
def audiofeed():
    if 'access' in session and session['access']:
        return json.dumps([True, audiolive.gen()])
    else:
        redirect('/')

### main ###
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="port, default 18331", type=int, default=18331)
    parser.add_argument("-w", "--password", help="password, default no password", default="")
    parser.add_argument("-s", "--https", help="enable https, default http", action="store_true")
    parser.add_argument("-c", "--cert", help="certificate file")
    parser.add_argument("-k", "--key", help="private key file")

    parser.print_help()
    args = parser.parse_args()
    port = args.port
    screenlive.password = args.password

    try:
        if args.https:
            if args.cert and args.key:
                app.run(host='0.0.0.0', port=port, threaded=True, ssl_context=(args.cert, args.key))
            else:
                app.run(host='0.0.0.0', port=port, threaded=True, ssl_context='adhoc')
        else:
            app.run(host='0.0.0.0', port=port, threaded=True)
    except Exception as e:
        print(str(e))
        print("Some errors in the command, fall back to the default http screen sharing!!!\n")
        app.run(host='0.0.0.0', port=port, threaded=True)
