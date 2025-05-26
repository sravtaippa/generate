from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from psycopg2 import errors
from db.db_ops import db_manager
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
            SELECT full_name, email, linkedin_profile_url, sentiment, photo_url
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

def get_booking_count():
    try:
        client_id = request.args.get("client_id")
        if not client_id:
            return jsonify({"error": "client_id is required"}), 400

        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT COUNT(*) FROM booking_records WHERE client_id = %s", (client_id,))
        result = cursor.fetchone()

        booking_count = result['count'] if result and 'count' in result else 0

        return jsonify({"value": booking_count}), 200

    except Exception as e:
        print("Error in get_booking_count_dashboard:", e)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def email_sent_chart(username):
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get the campaign ID from client_info
        cursor.execute("""
            SELECT instantly_campaign_id 
            FROM client_info 
            WHERE client_id = %s
        """, (username,))
        result = cursor.fetchone()
        if not result or not result['instantly_campaign_id']:
            return jsonify({'error': 'No campaign ID found'}), 404

        campaign_id = result['instantly_campaign_id']

        # Step 2: Determine current week's start and end dates
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)          # Sunday

        # Step 3: Fetch email records from dashboard_inbox within the week
        cursor.execute("""
            SELECT created 
            FROM dashboard_inbox 
            WHERE campaign_id = %s
            AND CAST(created AS date) >= %s 
            AND CAST(created AS date) <= %s
        """, (campaign_id, start_of_week.date(), end_of_week.date()))
        emails = cursor.fetchall()

        # Step 4: Aggregate email count by day of week
        day_counts = {'Mon': 0, 'Tue': 0, 'Wed': 0, 'Thu': 0, 'Fri': 0, 'Sat': 0, 'Sun': 0}
        for row in emails:
            try:
                created_date = datetime.strptime(row['created'], '%Y-%m-%d')
            except:
                created_date = row['created']  # If already a datetime
            created_day = created_date.strftime('%a')
            if created_day in day_counts:
                day_counts[created_day] += 1

        return jsonify(day_counts)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if conn:
            conn.close()

def get_campaign_details(username):
    if not username:
        return jsonify({'error': 'Missing username'}), 400

    try:
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        
        cursor.execute("""
            SELECT * FROM campaign_details
            WHERE client_id = %s
        """, (username,))
        campaigns = cursor.fetchall()

        if not campaigns:
            return jsonify({'message': 'No campaigns found'}), 404

        campaign_data = []

        for campaign in campaigns:
            campaign_id = campaign.get('instantly_campaign_id')
            profile_pictures = []

            try:
                cursor.execute("""
                    SELECT photo_url
                    FROM email_response_guideline
                    WHERE campaign_id = %s
                    ORDER BY created_time DESC
                    LIMIT 5
                """, (campaign_id,))
                replies = cursor.fetchall()
                profile_pictures = [reply['photo_url'] for reply in replies]

            except errors.UndefinedTable:
                
                profile_pictures = []

            campaign['profile_pictures'] = profile_pictures
            campaign_data.append(campaign)

        cursor.close()
        conn.close()

        return jsonify({'campaigns': campaign_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
def get_recent_replies(client_id):  # now using client_id directly
    if not client_id:
        return jsonify({"error": "Missing 'client_id' in query parameters"}), 400

    try:
        conn = connect_to_postgres()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get all campaign IDs for the client
        cursor.execute("""
            SELECT campaign_id FROM client_info WHERE client_id = %s
        """, (client_id,))
        campaign_ids = [row['instantly_campaign_id'] for row in cursor.fetchall()]
        if not campaign_ids:
            return jsonify({"error": "No campaigns found for the given client_id"}), 404

        # Step 2: Get latest 5 replies for those campaign IDs
        cursor.execute("""
            SELECT id, campaign_id, email, reply, created_time
            FROM email_response_guideline
            WHERE campaign_id = ANY(%s)
            ORDER BY created_time DESC
            LIMIT 5
        """, (campaign_ids,))
        replies = cursor.fetchall()

        response_data = []
        profile_table = f"cleaned_table_{client_id}"

        for reply in replies:
            reply_id = reply['id']
            campaign_id = reply['campaign_id']
            email = reply['email']
            reply_text = reply['reply']
            created_time = reply['created_time']

            # Step 3: Fetch matching profile
            cursor.execute(f"""
                SELECT name, title, company_name, domain, enriched_data
                FROM {profile_table}
                WHERE email = %s
                LIMIT 1
            """, (email,))
            profile = cursor.fetchone()
            if profile:
                name = profile['name']
                title = profile['title']
                company_name = profile['company_name']
                domain = profile['domain']
                enriched_data = profile['enriched_data']
            else:
                name = title = company_name = domain = enriched_data = None

            response_data.append({
                "reply_id": reply_id,
                "campaign_id": campaign_id,
                "email": email,
                "reply_text": reply_text,
                "created_time": created_time,
                "profile": {
                    "name": name,
                    "title": title,
                    "company_name": company_name,
                    "domain": domain,
                    "enriched_data": enriched_data
                }
            })

        cursor.close()
        conn.close()
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
if __name__ == '__main__':
    app.run(debug=True)
