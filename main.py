from flask import Flask, render_template , request, flash, redirect

from flask_login import LoginManager, login_user

import pymysql 

from dynaconf import Dynaconf 


app = Flask(__name__)

config = Dynaconf(settings_files=["settings.toml"],)

app.secret_key = config.secret_key

login_manager = LoginManager(app)

class User:
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __init__(self, result):
        self.name = result['Name']
        self.email = result['Email']
        self.address = result['Address']
        self.id = result['ID']
    def get_id(self):
        return str(self.id)
    
@login_manager.user_loader    
def load_user(user_id):
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `User` WHERE `ID` = %s", (user_id,))

    result = cursor.fetchone()
    connection.close()

    if result is None:
        return None
    return User(result)





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


@app.route("/register", methods=["POST", "GET"])
def register():  
    if request.method == "POST":
        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        address = request.form["address"]

        if password != confirm_password:
            flash("Passwords do not match!")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long!")
            flash("password is too short")
        else:
            connection = connect_db()

            cursor = connection.cursor()
       
        try:    
            cursor.execute("""
                INSERT INTO `User` ( `Name`, `Email`, `Password`, `Address`)
                            VALUES (%s, %s, %s, %s)
                """, (name, email, password, address))
            connection.close()

        except pymysql.err.IntegrityError: 
                flash("Email already registered!")
                connection.close()
        else:
            return redirect('/login')
        
        return render_template("register.html.jinja")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form.get('email')
        password = request.form.get('password')

        connection = connect_db()

        cursor = connection.cursor()

        connection.close()

        cursor.execute("SELECT * FROM `User` WHERE `Email` = %s", (email,))

        result = cursor.fetchone()

        connection.close()

        if result is None:
            flash("Email not registered!")
        elif password != result['Password']:
            flash("Incorrect password!")
        else:
            login_user(User(result))
            return redirect('/browse')
       
        
    return render_template("login.html.jinja")



   

     