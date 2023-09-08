import pymysql
import hashlib
import uuid
import os
from flask import Flask, render_template, request, redirect, make_response, session, flash
app = Flask(__name__)

app.secret_key = "kinnammet"

def create_connection():
    return pymysql.connect(
        host="10.0.0.17",
        #host="127.0.0.1",
        user="jusjacinto",
        #user="root",
        password="ARROW",
        #password="arrow",
        db="jusjacinto",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def can_access(id):
    if "logged_in" in session:
        matching_id  = session["id"] == int(request.args["id"])
        is_admin = session["role"] == "admin"
        return matching_id or is_admin
    else:
        return False
    

def encrypt(password):
    return hashlib.sha256(password.encode()).hexdigest()

def email_exists(email):
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM user WHERE email = %s"
            values = (email)
            cursor.execute(sql, values)
            result = cursor.fetchone()
    return result is not None

#This runs before every page request.
# If it returns something, the request will be prevented.
@app.before_request
def restrict():
    restricted = ["admin only"]
    if request.endpoint in restricted:
        if "logged_in" not in session or session["role"] != "admin":
            flash("Only admin can view that page.")
            return redirect('/')

@app.route("/")
def home():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM user"
            cursor.execute(sql)
            result = cursor.fetchall()
    return render_template("home.html", result=result)
            
@app.route("/post")
def post():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT *, count(likes.post_id) FROM post 
            LEFT JOIN user ON post.user_id = user.id 
            LEFT JOIN likes ON post.id = likes.post_id 
            WHERE post.id = %s GROUP BY (post.id)"""
            #sql = """SELECT * FROM post 
            #LEFT JOIN user ON post.user_id = user.id 
            #LEFT JOIN likes ON post.id = likes.post_id 
            #WHERE post.id = %s """
            values = (request.args["id"])
            cursor.execute(sql, values)
            result = cursor.fetchone()
    return render_template("post_view.html", result=result)

@app.route("/post/comment",  methods=["GET", "POST"])
def comment():
    if "logged_in" in session:
        if request.method == "POST":
            with create_connection() as connection:
                with connection.cursor() as cursor:
                    
                        sql = """INSERT INTO post SET
                            content = %s,
                            user_id = %s,
                            main_post_id = %s"""
                        values= (
                            request.form["content"],
                            session['id'],
                            request.args["id"]
                        )
                        cursor.execute(sql, values)
                        connection.commit()
                return redirect("/postall")
        else:
            with create_connection() as connection:
                with connection.cursor() as cursor:
                    sql = """SELECT * FROM post AS p1 
                        LEFT JOIN user AS u1 ON p1.user_id = u1.id 
                        LEFT JOIN post AS p2 ON p2.main_post_id = p1.id 
                        LEFT JOIN user AS u2 ON p2.user_id = u2.id 
                        WHERE p1.id = %s"""
                    values = (request.args["id"])
                    cursor.execute(sql, values)
                    result = cursor.fetchall()
            return render_template("comment.html", result=result)
    else: 
        flash("Log in to post a comment")
    return redirect("/login")

@app.route("/post/edit", methods=["GET", "POST"])
def editpost():
    if not can_access(id):
        flash("No permission to edit post")
        return redirect("/postall")
    
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:

                    image = request.files["image"]
                    
                    if image:
                        ext = os.path.splitext(image.filename)[1]
                        image_path = "static/images/" + str(uuid.uuid4())[:8] + ext
                        image.save(image_path)
                        if request.form["old_image"]:
                            os.remove(request.form["old_image"])
                    else:
                        image_path = request.form["old_image"]
                
                    sql = """UPDATE post SET
                        content = %s,
                        image = %s
                        WHERE id = %s"""
                    values= (
                        request.form["content"],
                        image_path,
                        request.args["id"]
                    )
                    cursor.execute(sql, values)
                    connection.commit()
            return redirect("/postall")
        
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT content,image FROM post WHERE id = %s"
                values = (request.args["id"])
                cursor.execute(sql, values)
                result = cursor.fetchone()
        return render_template("post_edit.html", result=result)

@app.route("/post/commentedit", methods=["GET", "POST"])
def editcomment():
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:

                    image = request.files["image"]

                    sql = """UPDATE post SET
                        content = %s
                        WHERE id = %s"""
                    values= (
                        request.form["content"],
                        request.args["id"]
                    )
                    cursor.execute(sql, values)
                    connection.commit()
            return redirect("/postall")
        
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT content FROM post WHERE id = %s"
                values = (request.args["id"])
                cursor.execute(sql, values)
                result = cursor.fetchone()
        return render_template("comment_edit.html", result=result)


@app.route("/post/add", methods=["GET", "POST"])
def add_post():
    if request.method == "POST":
        if "logged_in" in session:
            with create_connection() as connection:
                with connection.cursor() as cursor:
                
                    image = request.files["image"]

                    if image:
                        ext = os.path.splitext(image.filename)[1]
                        image_path = "static/images/" + str(uuid.uuid4())[:8] + ext
                        image.save(image_path)
                    else:
                        image_path = None
                    
                    sql = """INSERT INTO post (content, user_id, image) VALUES (%s, %s, %s)"""
                    values= (
                        request.form["content"],
                        session["id"],
                        image_path,
                    )
                    cursor.execute(sql,values)
                    connection.commit()
            return redirect("/postall")
        else:
            flash ("Log in first")
    else:                                                                                                                                                                                                                                                                                                                                       
        return render_template("post_add.html")
    
@app.route("/postall")
def allpost():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT *, count(likes.post_id) FROM post 
            LEFT JOIN user ON user.id = post.user_id 
            LEFT JOIN likes ON post.id = likes.post_id WHERE post.main_post_id IS NULL GROUP BY (post.id);"""
            #sql = """SELECT * FROM post 
            #LEFT JOIN user ON user.id = post.user_id 
            #WHERE post.main_post_id IS NULL;"""
            cursor.execute(sql)
            result = cursor.fetchall()
    return render_template("post_all.html", result=result)

@app.route("/post/delete")
def deletepost():
    if not can_access(id):
        flash("No permission to delete post")
        return redirect("/postall")
    
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT image FROM post WHERE id = %s"
            values  = (request.args["id"])
            cursor.execute(sql, values)
            result = cursor.fetchone()
            if result["image"]:
                os.remove(result["image"])

            sql = "DELETE FROM post WHERE id = %s"
            values = (request.args["id"])
            cursor.execute(sql, values)
            connection.commit()
    return redirect("/postall")

@app.route("/like")
def like():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """INSERT INTO likes (user_id, post_id) VALUES ( %s, %s)"""
            values = (
                session["id"],
                request.args["id"]
            )
            cursor.execute(sql, values)
            connection.commit()
    return redirect("/postall")





@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:

                sql = """SELECT * FROM user 
                    WHERE email = %s AND password = %s"""
                values = (
                    request.form["email"],
                    encrypt(request.form["password"])
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
        if result:
            session["logged_in"] = True
            session["id"] = result["id"]
            session["first_name"] = result["first_name"]
            session["role"] = result["role"]
            return redirect("/postall")
        else:
            flash ("Password incorrect")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        if email_exists(request.form["email"]):
            flash("That email already exists.")
            return redirect("/signup")
        with create_connection() as connection:
            with connection.cursor() as cursor:

                image = request.files["image"]

                if image:
                    # Choose a random filename to prevent clashes
                    ext = os.path.splitext(image.filename)[1]
                    image_path = "static/images/profile" + str(uuid.uuid4())[:8] + ext
                    image.save(image_path)
                else:
                    image_path = None

                sql = """INSERT INTO user 
                    (first_name, last_name, email, password, birthday, image)
                    VALUES (%s, %s, %s, %s, %s, %s)"""
                values = (
                    request.form["first_name"],
                    request.form["last_name"],
                    request.form["email"],
                    encrypt(request.form["password"]),
                    request.form["birthday"],
                    image_path
                )
                cursor.execute(sql, values)
                connection.commit() # <-- NEW!
                
                # Select the new user details and store them in session
                sql = "SELECT * FROM user WHERE email = %s"
                values = (request.form["email"])
                cursor.execute(sql, values)
                result = cursor.fetchone()
                session["logged_in"] = True
                session["id"] = result["id"]
                session["first_name"] = result["first_name"]
                session["role"] = result["role"]

        return redirect("/")
    else:
        return render_template("signup.html")

#/view?id=1
@app.route("/view")
def view():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT * FROM jusjacinto.post 
            LEFT JOIN user ON post.user_id = user.id 
            WHERE user.id = %s AND main_post_id IS NULL;"""
            values = (request.args["id"])
            cursor.execute(sql, values)
            result = cursor.fetchall()
    return render_template("view.html", result=result)


@app.route("/update", methods=["GET", "POST"])
def update():
    if not can_access(id):
        flash("No permission to update user")
        return redirect("/")
    
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:

                password = request.form["password"]
                if password:
                    encrypted_password = encrypt(password)
                else:
                    encrypted_password = request.form["old_password"]

                image = request.files["image"]
                if image:
                    ext = os.path.splitext(image.filename)[1]
                    image_path = "static/images/" + str(uuid.uuid4())[:8] + ext
                    image.save(image_path)
                    if request.form["old_image"]:
                        os.remove(request.form["old_image"])
                else:
                    image_path = request.form["old_image"]
                
                sql = """UPDATE user SET
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    password = %s,
                    birthday = %s,
                    image = %s
                    WHERE id = %s
                """
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    encrypted_password,
                    request.form['birthday'],
                    image_path,
                    request.form['id']
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect("/")
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM user WHERE id = %s"
                values = (request.args["id"])
                cursor.execute(sql, values)
                result = cursor.fetchone()
        return render_template("update.html", result=result)


#/delete?id=1
@app.route("/delete")
def delete():
    if not can_access(id):
        flash("No permission to delete user")
        return redirect("/")
    
    with create_connection() as connection:
        with connection.cursor() as cursor:
            # Get the imafe path before deleting the user
            sql = "SELECT image FROM user WHERE id = %s"
            values  = (request.args["id"])
            cursor.execute(sql, values)
            result = cursor.fetchone()
            if result["image"]:
                os.remove(result["image"])




            sql = "DELETE FROM user WHERE id = %s"
            values = (request.args["id"])
            cursor.execute(sql, values)
            connection.commit()
    return redirect("/")

# /checkmail?email=a@a
@app.route("/checkemail")
def check_email():
    return {
        "exists": email_exists(request.args["email"])
    }

# /admin?id=1&role=admin
@app.route("/admin")
def toggle_admin():
    if "logged_in" in session and session["role"] == "admin":
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "UPDATE user SET role = %s WHERE id = %s"
                values = (
                    request.args["role"],
                    request.args["id"]
                )
                cursor.execute(sql, values)
                connection.commit()
    else: 
        flash("You do not have permission to do that!")
    return redirect("/")

@app.route("/hidden")
def admin_only():
    return "here is where I would put restricted content, If I had any"

app.run(debug=True)