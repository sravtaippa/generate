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




def get_linkedin_metrics(client_id: str):
    """Return LinkedIn-campaign metrics for the given client_id."""
    conn = connect_to_postgres()
    cur  = conn.cursor()

    # 1️⃣  find the user’s LinkedIn campaign
    cur.execute(
        "SELECT linkedin_campaign_name "
        "FROM campaign_details "
        "WHERE client_id = %s "
        "LIMIT 1",
        (client_id,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError("No LinkedIn campaign found for this user")

    linkedin_campaign_name = row[0]

    # 2️⃣  pull the metrics
    cur.execute(
        """
        SELECT metrics_date,
               invitations_sent,
               messages_sent,
               inmails_sent,
               invitations_accepted,
               message_replies,
               invitation_accepted_rate,
               message_reply_rate
        FROM linkedin_campaign_metrics
        WHERE linkedin_campaign_name = %s
        ORDER BY metrics_date DESC
        """,
        (linkedin_campaign_name,),
    )
    cols = [c[0] for c in cur.description]
    results = [dict(zip(cols, r)) for r in cur.fetchall()]

    cur.close()
    conn.close()
    return results


def fetch_campaign_details(client_id: str):
    """Return a list of campaigns (and lead pictures) for the given client_id.
       Raise ValueError if none found."""
    conn = connect_to_postgres()
    cur  = conn.cursor()
    try:
        with conn:
            with conn.cursor() as cur:
                # 1️⃣ campaigns
                cur.execute(
                    """
                    SELECT client_id,
                           linkedin_campaign_name,
                           linkedin_campaign_status,
                           created_date
                    FROM   campaign_details
                    WHERE  client_id = %s
                    """,
                    (client_id,),
                )
                campaigns = cur.fetchall()

                if not campaigns:
                    raise ValueError("No campaigns found for this client_id.")

                # 2️⃣ attach the five newest profile pictures per campaign
                result = []
                for campaign in campaigns:
                    campaign_name = campaign["linkedin_campaign_name"]

                    cur.execute(
                        """
                        SELECT picture
                        FROM   leadsin_response_linkedin
                        WHERE  campaign_name = %s
                        ORDER  BY created_time DESC
                        LIMIT  5
                        """,
                        (campaign_name,),
                    )
                    leads = cur.fetchall()
                    pics  = [
                        (lead["picture"] or "https://i.pravatar.cc/50")
                        for lead in leads
                    ]

                    result.append(
                        {
                            "created_date":            campaign["created_date"],
                            "linkedin_campaign_name":  campaign_name,
                            "linkedin_campaign_status": campaign["linkedin_campaign_status"],
                            "profile_pictures":        pics,
                        }
                    )

        return result

    finally:
        conn.close()

    
if __name__ == '__main__':
    app.run(debug=True)
