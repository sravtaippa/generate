from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

@app.route("/get-profile-picture/<username>")
def get_profile_picture(username):
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="taippa",
        user="super",
        password="drowsapp_2025"
    )
    cur = conn.cursor()
    cur.execute("SELECT profile_picture FROM client_info WHERE client_id = %s LIMIT 1", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return jsonify({"profile_picture": row[0]})
    return jsonify({"profile_picture": ""})
