from flask import Flask, render_template , request , redirect

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
def homepage():  
    return render_template("homepage.html.jinja")


@app.route("/browse")
def browse():
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product` ") 

    result = cursor.fetchall()
    connection .close() 

    return render_template("browse.html.jinja", products=result)

@app.route("/product/<product_id>")
def product_page(product_id):
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product` WHERE `ID` = %s", (product_id,) )

    result = cursor.fetchone()

    connection .close() 

    return render_template("product.html.jinja", product=result)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        connection = connect_db()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM User WHERE Email = %s", (email,))
        user = cursor.fetchone()
        connection.close()

        if user is None:
            return "Email not found"
        
    return render_template("login.html.jinja")


@app.route("/register", methods=['GET', 'POST'])
def register():  
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute(
            "INSERT INTO User (Name, Email, Password) VALUES (%s, %s, %s)",
            (name, email ("utf-8"))
        )

    if request.method == "POST":

        name = request.form.get("name")

        email = request.form.get("email")

        password = request.form.get("password")

        confirm = request.form.get("confirm_password")
        if password != confirm:
            return "Passwords do not match"
        
        connection.close()

    return render_template("register.html.jinja")
   

     