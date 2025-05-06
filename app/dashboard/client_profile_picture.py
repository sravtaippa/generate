from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

@app.route("/get_profile_picture_dashboard")
def get_profile_picture_dashboard():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Missing username parameter"}), 400

    try:
        with psycopg2.connect(
            host="localhost",
            port="5432",
            dbname="taippa",
            user="super",
            password="drowsapp_2025"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT profile_picture FROM client_info WHERE client_id = %s LIMIT 1", 
                    (username,)
                )
                row = cur.fetchone()
                return jsonify({"profile_picture": row[0] if row else ""})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
