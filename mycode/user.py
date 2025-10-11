from flask import Blueprint
from config import get_connection

bp = Blueprint("user_bp", __name__)

# Directly fetch users from DB
conn = get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT id, first_name, last_name, email, phone_no FROM users")
citizens = cursor.fetchall()
cursor.close()
conn.close()
