from flask import Flask, request, jsonify
from pyairtable import Api
import re

app = Flask(__name__)

# Airtable Config
BASE_ID = 'app5s8zl7DsUaDmtx'
AIRTABLE_API_KEY = 'patELEdV0LAx6Aba3.393bf0e41eb59b4b80de15b94a3d122eab50035c7c34189b53ec561de590dff3'
CUR_TABLE = "cur_influencer_data"

FIELDS = [
    "avg_comments",
    "avg_likes",
    "avg_video_play_counts",
    "business_category_name",
    "created_time",
    "email_id",
    "external_urls",
    "full_name",
    "id",
    "influencer_location",
    "influencer_nationality",
    "influencer_type",
    "instagram_bio",
    "instagram_captions",
    "instagram_comments_counts",
    "instagram_followers_count",
    "instagram_follows_count",
    "instagram_hashtags",
    "instagram_likes_counts",
    "instagram_post_urls",
    "instagram_posts_count",
    "instagram_profile_pic",
    "instagram_url",
    "instagram_username",
    "instagram_video_play_counts",
    "instagram_video_urls",
    "linkedin_url",
    "phone",
    "profile_type",
    "snapchat_url",
    "social_media_profile_type",
    "targeted_audience",
    "targeted_domain",
    "tiktok_url",
    "twitter_url"
]


# === Cleaning Helpers ===
def clean_value(value):
    if isinstance(value, str) and value.strip().lower() in {"na", "n/a", "none", ""}:
        return ""
    return value

def clean_email(email):
    if isinstance(email, str):
        email = email.strip().lower()
        return email if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) else ""
    return ""

def clean_phone(phone):
    if isinstance(phone, str):
        digits = re.sub(r"\D", "", phone)
        return f"+{digits}" if digits else ""
    return ""

def is_valid_ig_url(url):
    return isinstance(url, str) and re.match(r"^https?://(www\.)?instagram\.com/(?!reel)[^/?#]+/?", url)

def is_valid_tt_url(url):
    return isinstance(url, str) and url.strip().startswith("https://www.tiktok.com/")

# === Sanitization Function ===
def sanitize_and_upload(data_list):
    api = Api(AIRTABLE_API_KEY)
    dst = api.table(BASE_ID, CUR_TABLE)

    existing_keys = set()
    cleaned_count = 0
    skipped_count = 0
    errors = []

    for index, fields in enumerate(data_list):
        social_type = fields.get("social_media_profile_type", "").strip().lower()
        ig_url = fields.get("instagram_url", "").strip()
        tt_url = fields.get("tiktok_url", "").strip()

        # Social URL validation
        if social_type == "instagram":
            if not is_valid_ig_url(ig_url):
                skipped_count += 1
                continue
            key = (social_type, ig_url)
        elif social_type == "tiktok":
            if not is_valid_tt_url(tt_url):
                skipped_count += 1
                continue
            key = (social_type, tt_url)
        else:
            skipped_count += 1
            continue

        if key in existing_keys:
            skipped_count += 1
            continue
        existing_keys.add(key)

        cleaned = {}
        for field in FIELDS:
            val = clean_value(fields.get(field, ""))
            if field == "email_id":
                val = clean_email(val)
            elif field == "phone":
                val = clean_phone(val)
            elif field == "id":
                val = str(val)
            cleaned[field] = val

        try:
            dst.create(cleaned)
            cleaned_count += 1
        except Exception as e:
            errors.append({"index": index, "error": str(e)})

    return {
        "cleaned_records": cleaned_count,
        "skipped_records": skipped_count,
        "errors": errors
    }


# === Run Flask Server ===
if __name__ == "__main__":
    app.run(debug=True)
