import os
import mysql.connector

SECRET_KEY = "secret123"

UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DB = "civic_database"
MYSQL_PORT = 3306

def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        port=MYSQL_PORT
    )
# ----------------- SMTP (for emails) -----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_USER = "cityparivartan@gmail.com"
SMTP_PASS = "gdwt iwwc iykm tlyq"  # Gmail App Password
SMTP_PORT = 587