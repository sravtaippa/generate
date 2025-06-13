from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'
BASE_ID = 'app5s8zl7DsUaDmtx'
TABLE_NAME = 'src_influencer_data'

def index():
    return render_template('index.html')


def get_influencer_data():
    airtable_url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}

    all_records = []
    params = {}

    while True:
        response = requests.get(airtable_url, headers=headers, params=params)
        if response.status_code != 200:
            return jsonify({'error': 'Airtable fetch failed'}), 500

        data = response.json()
        all_records.extend(data.get('records', []))

        if 'offset' in data:
            params['offset'] = data['offset']
        else:
            break

    result = []
    for rec in all_records:
        fields = rec.get('fields', {})
        result.append({
            'full_name': fields.get('full_name', ''),
            'instagram_username': fields.get('instagram_username', ''),
            'influencer_type': fields.get('influencer_type', ''),
            'targeted_audience': fields.get('targeted_audience', ''),
            'targeted_domain': fields.get('targeted_domain', ''),
            'instagram_bio': fields.get('instagram_bio', ''),
            'instagram_followers_count': fields.get('instagram_followers_count', 0),
            'instagram_follows_count': fields.get('instagram_follows_count', 0),
            'instagram_posts_count': fields.get('instagram_posts_count', 0),
            'instagram_captions': fields.get('instagram_captions', ''),
            'email_id': fields.get('email_id', ''),
            'phone': fields.get('phone', ''),
            'instagram_video_urls': fields.get('instagram_video_urls', ''),
            'instagram_hashtags': fields.get('instagram_hashtags', ''),
            'instagram_url': fields.get('instagram_url', ''),
            'business_category_name': fields.get('business_category_name', ''),
            'influencer_location': fields.get('influencer_location', ''),
            'influencer_nationality': fields.get('influencer_nationality', ''),
            'instagram_likes_counts': fields.get('instagram_likes_counts', 0),
            'instagram_comments_counts': fields.get('instagram_comments_counts', 0),
            'created_time': fields.get('created_time', ''),
            'instagram_profile_pic': fields.get('instagram_profile_pic', ''),  # for profile image if needed
        })

    return jsonify(result)


