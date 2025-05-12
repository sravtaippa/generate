from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

def connect_to_postgres():
    return psycopg2.connect(
        dbname="taippa",
        user="super",
        password="drowsapp_2025",
        host="magmostafa-4523.postgres.pythonanywhere-services.com",
        port="14523"
    )

def fetch_recent_leads_from_db(client_id):
    try:
        conn = connect_to_postgres()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get campaign ID for client
        cur.execute("""
            SELECT instantly_campaign_id 
            FROM client_info 
            WHERE client_id = %s
        """, (client_id,))
        client_row = cur.fetchone()

        if not client_row:
            return {"error": "Client not found"}, 404

        campaign_id = client_row['instantly_campaign_id']

        # Step 2: Fetch recent replies
        cur.execute("""
            SELECT full_name, job_title, email, profile_picture_url
            FROM email_response_guideline
            WHERE campaign_id = %s
            ORDER BY created_time DESC
            LIMIT 5
        """, (campaign_id,))
        leads = cur.fetchall()

        return {"client_id": client_id, "recent_leads": leads}, 200

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
