from flask import Blueprint, render_template, request, redirect
from werkzeug.security import generate_password_hash
from config import get_connection

bp = Blueprint("register", __name__)

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["f_nm"]
        last_name = request.form["l_nm"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm_password = request.form["confirmPassword"]

        if password != confirm_password:
            return "❌ Passwords do not match!"

        hashed_password = generate_password_hash(password)
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (first_name, last_name, email, phone_no, password)
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, email, phone, hashed_password))
            conn.commit()
            return redirect("/login")
        except Exception as e:
            return f"Database Error: {str(e)}"
        finally:
            cursor.close()
            conn.close()

    return render_template("user/signup.html")