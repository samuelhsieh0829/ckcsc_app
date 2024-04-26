from flask import Flask, render_template, request, redirect, url_for, abort, make_response, session, flash
import os
import dotenv
import random, string
from pymongo import MongoClient
from hashlib import sha256

#load env
dotenv.load_dotenv()

#connect db
mongodb_url = os.getenv("MONGODB_URL")
dbclient = MongoClient(mongodb_url)

try:
    dbclient.admin.command("ping")
    print("Database connected")
except Exception as e:
    print(e)

db = dbclient["ckcsc_app"]
db_users = db["users"]

#sussy word
sus_list = ["'", '"', "$", ";", "/", "!", "@", "#", "%", "^", "&", "*","(", ")", "-", "\\", "|"]

#flask init
app = Flask(__name__)
config = {"DEBUG": True, "TESTING": True, "MAX_CONTENT_LENGTH": 16*1024*1024}
app.config.update(config)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'

#cookie
logged_user_list = {"decoy": ""}

# @app.route('/favicon.ico')
# def favicon():
#     return url_for("static", filename="image/favicon.ico")

#index
@app.route("/")
def index():
    #redirect message
    msg = request.args.get("message")
    if msg == None:
        msg = ""
    #logged in
    if session.get("logged_in"):
        usernick = request.cookies.get("user")
        if session.get("user") == usernick:
            try:
                username = logged_user_list[str(usernick)]
                return render_template("logged.html", user=username, message=msg)
            except KeyError:
                session["logged_in"] = False
                resp = make_response(render_template("index.html", message="Deleted sussy cookie"))
                resp.delete_cookie("user")
                return resp
        else:
            session["logged_in"] = False
            resp = make_response(render_template("index.html", message="Deleted sussy cookie"))
            resp.delete_cookie("user")
            return resp
    #not logged
    else:
        if request.cookies.get("user") == None:
            return render_template("index.html", message=msg)
        #clear cookie
        else:
            resp = make_response(render_template("index.html", message="Deleted sussy cookie"))
            resp.delete_cookie("user")
            return resp

#login index
@app.route("/login")
def login():
    if session.get("logged_in"):
        return redirect("/")
    else:
        return render_template("login.html")

#login
@app.route("/log", methods=["GET","POST"])
def log():
    global logged_user_list
    #get username and password
    username = request.values["username"]
    password = request.values["password"]
    #check if sussy words in input
    for i in sus_list:
        if i in username:
            return redirect(url_for("index", message="Username is invalid"))
        if i in password:
             return redirect(url_for("index", message="Password is invalid"))
    #get user data from db
    password = sha256(password.encode()).hexdigest()
    find = db_users.find_one({"name": username, "password": password})
    print(find)
    #login successfully
    if find:
        session["logged_in"] = True
        resp = make_response(render_template("login_successful.html", username=username))
        #generate cookie
        usernick = "decoy"
        while usernick in logged_user_list:
            usernick = string.ascii_letters
            usernick = list(usernick)
            random.shuffle(usernick)
            usernick = "".join(usernick[:10])
        logged_user_list[usernick] = username
        resp.set_cookie("user", usernick)
        session["user"] = usernick
        return resp
    #login failed
    else:
        return redirect(url_for("index", message="User name or password incorrect"))

#logout
@app.route("/logout")
def logout():
    global logged_user_list
    usernick = request.cookies.get("user")
    try:
        logged_user_list.pop(usernick)
    finally:
        resp = make_response(redirect("/"))
        resp.delete_cookie("user")
        session.pop("logged_in", None)
        session.pop("user", None)
        return resp

#clear cookie
@app.route("/clear_cookie")
def clear_cookie():
    resp = make_response(redirect("/"))
    resp.delete_cookie("user")
    return resp

@app.route("/clear_session")
def clear_session():
    session.pop("logged_in", None)
    session.pop("user", None)
    return redirect("/")

#register index
@app.route("/register")
def register():
    return render_template("register.html")

#register
@app.route("/reg", methods=["GET","POST"])
def reg():
    #get value
    username = request.values["username"]
    password = request.values["password"]
    password_2 = request.values["password_2"]
    #password != password_2
    if password != password_2:
        return redirect(url_for("index", message="Password error"))
    #no password
    elif password == "":
        return redirect(url_for("index", message="Set a password pls"))
    else:
        #check if password contain sussy words
        for i in sus_list:
            if i in username:
                return redirect(url_for("index", message="Username is invalid"))
            if i in password:
                return redirect(url_for("index", message="Password is invalid"))
        #check if user is in db
        find = db_users.find_one({"name":username})
        if find:
            return redirect(url_for("/", message="Username already exist"))
        #add user to db
        password = sha256(password.encode()).hexdigest()
        user_data = {"name": username, "password": password}
        x = db_users.insert_one(user_data)
        print(x.inserted_id)
        #login
        session["logged_in"] = True
        resp = make_response(render_template("owo.html"))
        #generate cookie
        usernick = "decoy"
        while usernick in logged_user_list:
            usernick = string.ascii_letters
            usernick = list(usernick)
            random.shuffle(usernick)
            usernick = "".join(usernick[:10])
        logged_user_list[usernick] = username
        resp.set_cookie("user", usernick)
        session["user"] = usernick
        return resp

#terminal, but no terminal
@app.route("/terminal")
def terminal():
    if session.get("logged_in"):
        user = request.cookies.get("user")
        if user:
            username_session = session.get("user")
            if user == username_session:
                username = logged_user_list[user]
                username = sha256(username.encode()).hexdigest()
                db_admin = db["admin"]
                find = db_admin.find_one({"name":username})
                if find:
                    return render_template("terminal.html")
                else:
                    return redirect(url_for("index", message="Oh?"))
            else:
                print(username, username_session)
                return redirect(url_for("index", message="Why?"))
        else:
            return redirect(url_for("index", message="Where tf is your cookie?"))
    else:
        return redirect(url_for("index", message="Login first"))

#404
@app.errorhandler(404)
def error404(error):
    return redirect(url_for("index", message="404"))

app.run()