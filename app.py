from flask import Flask, jsonify, render_template, session, redirect,request
from flask import flash
from flask_socketio import SocketIO
from config import UPLOAD_FOLDER, get_connection
from mycode import register, login1, report, admin_issue, complaints
from mycode import user as user_module
from mycode.user import citizens
from mycode import garbage, roads, water, animal_rescue, drainage
from mycode import socket_utils
from mycode import user_issues
from mycode import admin_complaints,forget
from mycode import index as index
from mycode import profile

print("FLASH IMPORTED:", flash)


app = Flask(__name__)
app.secret_key = "secret123"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------- SocketIO -----------------
socketio = SocketIO(app, cors_allowed_origins="*")
socket_utils.socketio = socketio  # inject socketio

# ----------------- Register Blueprints -----------------
app.register_blueprint(login1.bp)
app.register_blueprint(user_issues.bp)
app.register_blueprint(register.bp)
app.register_blueprint(report.bp, url_prefix="/report")
app.register_blueprint(user_module.bp)
app.register_blueprint(admin_issue.bp)
app.register_blueprint(complaints.bp)
app.register_blueprint(garbage.bp)
app.register_blueprint(drainage.bp)
app.register_blueprint(roads.bp)
app.register_blueprint(water.bp)
app.register_blueprint(animal_rescue.bp)
app.register_blueprint(admin_complaints.bp)
app.register_blueprint(index.bp)
app.register_blueprint(forget.bp)
app.register_blueprint(profile.bp)


# ----------------- Routes -----------------
@app.route("/")
def index():
    return render_template("user/index.html")

@app.route("/report_issue")
def report_issue():
    if not session.get("user_email") and not session.get("admin_email"):
        return redirect("/login")
    return render_template("user/report_issue.html")

@app.route("/status")
def status():
    if not session.get("user_email"):
        return redirect("/auth/login")
    return render_template("user/status.html")

# @app.route("/profile")
# def profile():
#     if not session.get("user_email"):
#         return redirect("/auth/login")
#     return render_template("user/profile.html")

@app.route("/signup")
def signup():
    return render_template("user/signup.html")

@app.route("/login")
def login():
    return render_template("user/login.html")

@app.route("/forget")
def forget():
    return render_template("user/forget.html")

@app.route("/steps")
def steps():
    return render_template("user/steps.html")



# @app.route("/admin/index")
# def admin_index():
#     return render_template("admin/index.html")

@app.route("/admin/user")
def admin_user():
    return render_template("admin/user.html", citizens=citizens)




# ----------------- Map API -----------------
# map api
@app.route("/api/issues")
def api_issues():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, title, description, category, status, area, latitude, longitude 
        FROM reports
        WHERE status IN ('Received', 'In Progress')
    """)
    rows = cursor.fetchall()
    return jsonify(rows)





# ----------------- Context processor -----------------
@app.context_processor
def inject_user():
    return dict(
        user_name=session.get("user_name"),
        user_email=session.get("user_email"),
        admin_email=session.get("admin_email"),
        admin_name=session.get("admin_name")
    )

# ----------------- SocketIO join room -----------------
@socketio.on("join")
def on_join(data):
    email = data.get("email")
    if email:
        from flask_socketio import join_room
        join_room(email)

# ----------------- SINGLE Global Exception Handler -----------------
# @app.errorhandler(Exception)
# def handle_global_exception(e):
#     # Ignore favicon requests (browsers always ask for this)
#     if request.path == "/favicon.ico":
#         return "", 204  # 204 = No Content (silent success)

#     print(f"⚠ Unhandled Exception: {e}")
#     try:
#         flash("⚠ Oops! Something went wrong. Please try again.", "danger")
#     except Exception as fe:
#         print(f"Flash failed: {fe}")
#     return redirect(request.referrer or "/")

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)