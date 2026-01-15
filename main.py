from flask import Flask, render_template , request, flash, redirect, abort

from flask_login import LoginManager, login_user, logout_user, login_required, current_user

import pymysql 

from dynaconf import Dynaconf 


app = Flask(__name__)

config = Dynaconf(settings_files=["settings.toml"],)

app.secret_key = config.secret_key

login_manager = LoginManager(app)

login_manager.login_view = "/login"

class User:
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __init__(self, result):
        self.name = result['Name']
        self.email = result['Email']
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
    connection.close() 

    return render_template("browse.html.jinja", products=result)

@app.route("/product/<product_id>")
def product_page(product_id):
 
    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM `Product` WHERE `ID` = %s", (product_id,) )

    result = cursor.fetchone()

    cursor.close()

    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
    SELECT * FROM `Review`
    
    JOIN `User` ON `Review`.`UserID` = `User`.`ID` 
                   
    WHERE `ProductID` = %s
    
    """, (product_id,) )

    reviews = cursor.fetchall()

    connection.close() 

    if result is None:
        abort(404)
    return render_template("product.html.jinja", product=result , reviews=reviews)


@app.route("/product/<product_id>/add_to_cart", methods=["POST"])
@login_required
def add_to_cart(product_id):

    quantity = int(request.form["qty"])

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO `Cart` (`quantity`, `ProductID`, `UserID`)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
        `Quantity` = `Quantity` + %s
    """ , (quantity, product_id, current_user.id, quantity) )
    
    connection.commit()
    connection.close()



    return redirect('/cart')

@app.route("/cart")
@login_required
def cart():
    connection = connect_db()

    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM `Cart` 
        JOIN `Product` ON `Cart`.`ProductID` = `Product`.`ID`
        WHERE `UserID` =  %s 
        """, (current_user.id,) )
    result = cursor.fetchall()

    connection.close()


    return render_template("cart.html.jinja", cart=result)

@app.route("/register", methods=["GET", "POST"])
def register():  
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Validation
        if password != confirm_password:
            flash("Passwords do not match!")
            return render_template("register.html.jinja")

        if len(password) < 8:
            flash("Password must be at least 8 characters long!")
            return render_template("register.html.jinja")

        connection = connect_db()
        cursor = connection.cursor()

        try:    
            cursor.execute("""
    INSERT INTO `User` (`Name`, `Email`, `Password`)
    VALUES (%s, %s, %s)
""", (name, email, password))


            connection.commit()

        except pymysql.err.IntegrityError: 
            flash("Email already registered!")
            return render_template("register.html.jinja")

        finally:
            connection.close()

        return redirect('/login')

    return render_template("register.html.jinja")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form.get('email')
        password = request.form.get('password')

        connection = connect_db()

        cursor = connection.cursor()


        cursor.execute("SELECT * FROM `User` WHERE `Email` = %s", (email,))
        result = cursor.fetchone()

        print(cursor)


        connection.close()

        if result is None:
            flash("Email not registered!")
        elif password != result['Password']:
            flash("Incorrect password!")
        else:
            login_user(User(result))
            return redirect('/browse')
       
        
    return render_template("login.html.jinja")

@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    return redirect('/') 

@app.route("/cart/<product_id>/update_qty", methods=["POST"])
@login_required
def update_cart(product_id):
    new_quantity = request.form["Quantity"]
    connection = connect_db()
    cursor = connection.cursor()
    
    cursor.execute("""
        UPDATE `Cart` 
        SET `Quantity` = %s
        WHERE `ProductID` =%s AND `UserID` = %s
        """, (new_quantity, product_id, current_user.id) )
    connection.close()

    return redirect('/cart')



@app.route("/cart/<product_id>/remove", methods=["POST"])
@login_required
def remove(product_id):
   
    connection = connect_db()
    cursor = connection.cursor()
    
    cursor.execute("""
        DELETE FROM `Cart` 
        WHERE `ProductID` =%s AND `UserID` = %s
        """, (product_id, current_user.id) )
    connection.close()

    return redirect('/cart')




@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    connection = connect_db()

    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM `Cart` 
        JOIN `Product` ON `Cart`.`ProductID` = `Product`.`ID`
        WHERE `UserID` =  %s 
        """, (current_user.id,) )
    result = cursor.fetchall()

    sale = cursor.lastrowid
    if request.method == "POST":
        # create the sale in the database
        cursor.execute(" INSERT INTO `Sale` (`UserID`) VALUES (%s)", (current_user.id,) )
        # store products bought
        for item in result:
            cursor.execute(" INSERT INTO `SaleProduct` (`SaleID`, `ProductID`, `Quantity`) VALUSE (%s %s %s) ", (sale, item['ProductID'], item['Quantity']) )
        # empty cart
        cursor.execute(" DELETE FROM `Cart` WHERE `UserID` = %s", (current_user.id,) )
        # thank you screen
        #TODO: Make a thank you page + Route
        redirect('/thank-you')

    connection.close()

    return render_template("checkout.html.jinja" , cart=result)


@app.route("/thank_you")
@login_required
def thank_you():
    return render_template("thank_you.html.jinja")

@app.route("/order")
@login_required
def Order():
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT
        `Sale`.`ID`,
        `Sale`.`Timestamp`, 
        SUM(`SalesCart`.`Quantity`) AS 'Quantity', 
        SUM(`SalesCart`.`Quantity` * `Product`.`Price`) AS 'Total'
    FROM `Sale`
    JOIN `SalesCart` ON `SalesCart`.`SaleID` = `Sale`.`ID`
    JOIN `Product`ON `Product`.`ID` = `SalesCart`.`ProductID`
    WHERE `UserID` = %s 
    GROUP BY `Sale`.`ID`;
    """, (current_user.id,) )

    result = cursor.fetchall()
    connection.close()  

    return render_template("order.html.jinja", order=result)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html.jinja"), 404


@app.route("/product/<product_id>/review", methods=["POST"])
@login_required
def add_review(product_id):
    # Get review from the form
    rating = request.form["rating"]
    comment = request.form["comments"]

    connection = connect_db()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO `Review` (`Rating`, `Comment`, `ProductID`, `UserID)
        VALUES (%s, %s, %s, %s)
    """, (rating , comment, product_id, current_user.id) )

    connection.close()

    return redirect(f"/product/{product_id}")

