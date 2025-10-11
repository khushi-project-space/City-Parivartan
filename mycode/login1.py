from flask import Blueprint, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from config import get_connection

bp = Blueprint("login1", __name__, url_prefix="/auth")

# ----------------- Utility -----------------
def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, first_name, email, password FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close(); conn.close()
    return user

def get_admin_by_email(email):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT admin_id, first_name, email, password FROM admins WHERE email=%s", (email,))
    admin = cur.fetchone()
    cur.close(); conn.close()
    return admin

def update_admin_password(admin_id, hashed_password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE admins SET password=%s WHERE admin_id=%s", (hashed_password, admin_id))
    conn.commit()
    cur.close(); conn.close()

# ----------------- Routes -----------------
@bp.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email = request.form.get("email","").strip()
        password = request.form.get("password","")

        if not email or not password:
            flash("❌ Email and password are required!")
            return render_template("user/login.html")

        # --------- Admin Login ---------
        admin = get_admin_by_email(email)
        if admin:
            # 1️⃣ Try hashed password
            try:
                if check_password_hash(admin["password"], password):
                    session["admin_email"] = admin["email"]
                    session["admin_name"] = admin["first_name"]
                    return redirect("/admin/index")
            except:
                pass

            # 2️⃣ Fallback: old plain-text password
            if admin["password"] == password:
                # Automatically hash and update DB for future login
                hashed = generate_password_hash(password)
                update_admin_password(admin["admin_id"], hashed)

                session["admin_email"] = admin["email"]
                session["admin_name"] = admin["first_name"]
                return redirect("/admin/index")

        # --------- User Login ---------
        user = get_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_name"] = user["first_name"]
            session["user_email"] = user["email"]
            return redirect("/")

        flash("❌ Invalid email or password!")
        return redirect("/auth/login")

    return render_template("user/login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()   # remove user_name and user_email
    flash("You have been logged out.", "info")
    return redirect(url_for("login1.login"))   # go back to login page
