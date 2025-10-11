from flask import Blueprint, jsonify, session
from config import get_connection

bp = Blueprint("user_issues", __name__)

@bp.route("/user/issues")
def user_issues():
    user_email = session.get("user_email")
    print("🔑 Session email:", user_email)   # 👈 debug line

    if not user_email:
        print("⚠️ User not logged in, returning empty issues")
        return jsonify([])

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT id, title, category, description, status, created_at,
                   IFNULL(updated_at, created_at) AS updated_at
            FROM reports
            WHERE email=%s
            ORDER BY created_at DESC
        """
        cursor.execute(query, (user_email,))
        issues = cursor.fetchall()
        cursor.close()
        conn.close()

        # fallback defaults
        for i in issues:
            if not i.get("status"):
                i["status"] = "Received"   # ✅ match admin default
            if not i.get("updated_at"):
                i["updated_at"] = i.get("created_at") or ""

        print(f"✅ {len(issues)} issues fetched for {user_email}")
        return jsonify(issues)

    except Exception as e:
        import traceback
        print("❌ Error fetching user issues:", e)
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500
