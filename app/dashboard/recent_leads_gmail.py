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
            SELECT full_name, email, linkedin_profile_url, sentiment
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

def fetch_metric_value(username, field):
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get campaign ID from client_info
        cursor.execute("""
            SELECT instantly_campaign_id 
            FROM client_info 
            WHERE client_id = %s
            LIMIT 1;
        """, (username,))
        result = cursor.fetchone()

        if not result or 'instantly_campaign_id' not in result:
            return 0

        instantly_campaign_id = result['instantly_campaign_id']

        # Step 2: Fetch the desired metric
        cursor.execute(f"""
            SELECT {field} 
            FROM metrics 
            WHERE campaign_id = %s
            LIMIT 1;
        """, (instantly_campaign_id,))
        metric_result = cursor.fetchone()

        return int(metric_result[field]) if metric_result and field in metric_result else 0

    except Exception as e:
        print("Error:", e)
        return 0

    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
