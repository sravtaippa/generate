import re
from flask import Flask, request, jsonify
from urllib.parse import unquote
from geotext import GeoText
import pycountry

app = Flask(__name__)

# Regex patterns
EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_REGEX = r"(\+?\d[\d\s\-\(\)]{8,})"
TIKTOK_REGEX = r"(https?://(?:www\.)?tiktok\.com/\S+)"
TWITTER_REGEX = r"twitter\.com/([a-zA-Z0-9_]+)"
SNAPCHAT_REGEX = r"snapchat\.com/add/([a-zA-Z0-9_.-]+)"
LINKEDIN_REGEX = r"(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)"
YOUTUBE_REGEX = r"(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/\S+)"

def unwrap_markdown(text):
    return re.sub(r'\[.*?\]\((https?://[^\s)]+)\)', r'\1', text)

def decode_instagram_redirects(text):
    pattern = re.compile(r'https://l\.instagram\.com/\?u=([^&]+)&[^\s]*')
    def replacer(match):
        return unquote(match.group(1))
    return pattern.sub(replacer, text)

def parse_followers_count(text):
    if not text:
        return 0
    text = text.strip().lower()
    text = re.sub(r"[^\d.km]", "", text)

    try:
        if 'm' in text:
            return int(float(text.replace('m', '')) * 1_000_000)
        elif 'k' in text:
            return int(float(text.replace('k', '')) * 1_000)
        else:
            clean = re.sub(r"[^\d]", "", text)
            return int(clean)
    except:
        return 0

def get_influencer_tier_from_count(count):
    if 1000 <= count < 10000:
        return "Nano"
    elif 10_000 <= count < 50_000:
        return "Micro"
    elif 50_000 <= count < 500_000:
        return "Mid-tier"
    elif 500_000 <= count < 1_000_000:
        return "Macro"
    elif count >= 1_000_000:
        return "Mega"
    else:
        return "Unknown"

def get_country_full_name(code_or_name):
    # Try alpha_2 lookup first
    try:
        country = pycountry.countries.get(alpha_2=code_or_name.upper())
        if country:
            return country.name
    except:
        pass
    # Try fuzzy search by name
    try:
        country = pycountry.countries.search_fuzzy(code_or_name)[0]
        return country.name
    except:
        return None

def extract_countries_with_codes(bio_text):
    # Extract countries from GeoText (full names)
    places = GeoText(bio_text)
    countries = list(places.country_mentions.keys())

    # Find all uppercase 2-letter words (possible country codes)
    country_codes = re.findall(r'\b([A-Z]{2})\b', bio_text.upper())

    # Map 2-letter codes to full country names, avoid duplicates
    for code in country_codes:
        full_name = get_country_full_name(code)
        if full_name and full_name not in countries:
            countries.append(full_name)

    return countries

def extract_info(long_text, followers_text=None, bio=None):
    if not long_text:
        return {}

    cleaned_text = unwrap_markdown(long_text)
    cleaned_text = decode_instagram_redirects(cleaned_text)

    follower_count = parse_followers_count(followers_text)
    influencer_tier = get_influencer_tier_from_count(follower_count)

    # Extract city and countries (with country code support)
    place_info = GeoText(bio or "")
    cities = place_info.cities
    countries = extract_countries_with_codes(bio or "")

    return {
        "tiktok_url": re.search(TIKTOK_REGEX, cleaned_text).group(1) if re.search(TIKTOK_REGEX, cleaned_text) else None,
        "twitter_id": re.search(TWITTER_REGEX, cleaned_text).group(1) if re.search(TWITTER_REGEX, cleaned_text) else None,
        "snapchat_id": re.search(SNAPCHAT_REGEX, cleaned_text).group(1) if re.search(SNAPCHAT_REGEX, cleaned_text) else None,
        "phone": re.search(PHONE_REGEX, cleaned_text).group(1).strip() if re.search(PHONE_REGEX, cleaned_text) else None,
        "email_id": re.search(EMAIL_REGEX, cleaned_text).group(0) if re.search(EMAIL_REGEX, cleaned_text) else None,
        "linkedin_id": re.search(LINKEDIN_REGEX, cleaned_text).group(1) if re.search(LINKEDIN_REGEX, cleaned_text) else None,
        "youtube_url": re.search(YOUTUBE_REGEX, cleaned_text).group(1) if re.search(YOUTUBE_REGEX, cleaned_text) else None,
        "influencer_tier": influencer_tier,
        "cities": cities,
        "countries": countries
    }

if __name__ == '__main__':
    app.run(debug=True)
