from flask import Flask, render_template

import pymysql 

from dynaconf import Dynaconf 


app = Flask(__name__)

config = Dynaconf(settings_files=["settings.toml"],)

def connect_db(): 
    conn = pymysql.connect(
        host="db.steamcenter.tech",
        user="jramirez",
        password=config.password, 
        database="jramirez_cooking_your_way",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

@app.route("/")
def home():
    return render_template("homepage.html.jinja")

@app.route("/browse")
def browse():
    connection = connect_db()

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `product` ") 

    result = cursor.fetchall()
    connection .close() 
    return render_template("browse.html.jinja")
