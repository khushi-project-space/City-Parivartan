from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import os, re, time, random, string
from config import get_connection

bp = Blueprint("profile", __name__)

UPLOAD_FOLDER = os.path.join("static", "uploads", "profile_pics")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@bp.route("/profile")
def profile():
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    user_email = session["user_email"]
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch user info
    cursor.execute("""
        SELECT id, first_name, last_name, email, phone_no, profile_pic, points, coupons
        FROM users WHERE email=%s
    """, (user_email,))
    user = cursor.fetchone()

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("auth.login"))

    # Calculate points from resolved reports
    cursor.execute("""
        SELECT id FROM reports
        WHERE email=%s AND status='Resolved' AND (points_awarded IS NULL OR points_awarded=0)
    """, (user_email,))
    resolved_reports = cursor.fetchall()
    points_to_add = 10 * len(resolved_reports)

    if points_to_add > 0:
        # Update user points
        cursor.execute("UPDATE users SET points = points + %s WHERE id=%s", (points_to_add, user['id']))
        # Mark reports as points_awarded
        report_ids = [str(r['id']) for r in resolved_reports]
        cursor.execute(f"UPDATE reports SET points_awarded=1 WHERE id IN ({','.join(report_ids)})")
        conn.commit()
        user["points"] += points_to_add

    # Generate coupon if points >= 100
    if user["points"] >= 100:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        cursor.execute("INSERT INTO coupons (user_id, code) VALUES (%s, %s)", (user["id"], code))
        cursor.execute("UPDATE users SET points = 0, coupons = coupons + 1 WHERE id=%s", (user["id"],))
        conn.commit()
        flash(f"Congratulations! You earned a coupon: {code}", "success")
        user["points"] = 0
        user["coupons"] += 1

    # Fetch detailed coupons
    cursor.execute("SELECT code, percent, created_at, used FROM coupons WHERE user_id=%s", (user["id"],))
    coupons = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("user/profile.html", user=user, coupons=coupons)


@bp.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    user_email = session["user_email"]
    conn = get_connection()
    cursor = conn.cursor()

    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    phone_no = request.form.get("phone_no")

    cursor.execute("""
        UPDATE users SET first_name=%s, last_name=%s, phone_no=%s
        WHERE email=%s
    """, (first_name, last_name, phone_no, user_email))
    conn.commit()

    cursor.close()
    conn.close()
    flash("Profile updated successfully!", "success")
    return redirect(url_for("profile.profile"))


@bp.route("/update_profile_pic", methods=["POST"])
def update_profile_pic():
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    if "profile_pic" not in request.files:
        flash("No file selected!", "danger")
        return redirect(url_for("profile.profile"))

    file = request.files["profile_pic"]
    if file.filename == "":
        flash("No file selected!", "danger")
        return redirect(url_for("profile.profile"))

    if file and re.match(r".*\.(jpg|jpeg|png|gif)$", file.filename.lower()):
        filename = f"user_{session['user_email']}_{int(time.time())}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        relative_path = os.path.join("uploads", "profile_pics", filename)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET profile_pic=%s WHERE email=%s", (relative_path, session["user_email"]))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Profile picture updated!", "success")
    else:
        flash("Invalid file type. Please upload an image.", "danger")

@bp.route("/delete_profile", methods=["POST"])
def delete_profile():
    if "user_email" not in session:
        return redirect(url_for("login1.login"))

    user_email = session["user_email"]
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Delete user
    cursor.execute("DELETE FROM users WHERE email=%s", (user_email,))
    conn.commit()
    cursor.close()
    conn.close()

    # **Clear session so navbar updates**
    session.clear()

    # Redirect to login page (or home)
    return redirect(url_for("login1.login"))




    return redirect(url_for("profile.profile"))