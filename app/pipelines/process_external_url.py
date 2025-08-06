import re
from urllib.parse import unquote

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

# Clean followers text like "12,000,0", "12.3K", "1.5M followers"
def parse_followers_count(text):
    if not text:
        return 0
    text = text.strip().lower()
    text = re.sub(r"[^\d.km]", "", text)  # Keep only digits, dots, k, m

    try:
        if 'm' in text:
            return int(float(text.replace('m', '')) * 1_000_000)
        elif 'k' in text:
            return int(float(text.replace('k', '')) * 1_000)
        else:
            # Remove all non-digits and join the remaining parts
            clean = re.sub(r"[^\d]", "", text)
            return int(clean)
    except:
        return 0

def get_influencer_tier_from_text(text):
    count = parse_followers_count(text)

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

def extract_info(long_text, followers_text=None):
    if not long_text:
        return {}

    cleaned_text = unwrap_markdown(long_text)
    cleaned_text = decode_instagram_redirects(cleaned_text)

    return {
        "tiktok_url": re.search(TIKTOK_REGEX, cleaned_text).group(1) if re.search(TIKTOK_REGEX, cleaned_text) else None,
        "twitter_id": re.search(TWITTER_REGEX, cleaned_text).group(1) if re.search(TWITTER_REGEX, cleaned_text) else None,
        "snapchat_id": re.search(SNAPCHAT_REGEX, cleaned_text).group(1) if re.search(SNAPCHAT_REGEX, cleaned_text) else None,
        "phone": re.search(PHONE_REGEX, cleaned_text).group(1).strip() if re.search(PHONE_REGEX, cleaned_text) else None,
        "email_id": re.search(EMAIL_REGEX, cleaned_text).group(0) if re.search(EMAIL_REGEX, cleaned_text) else None,
        "linkedin_id": re.search(LINKEDIN_REGEX, cleaned_text).group(1) if re.search(LINKEDIN_REGEX, cleaned_text) else None,
        "youtube_url": re.search(YOUTUBE_REGEX, cleaned_text).group(1) if re.search(YOUTUBE_REGEX, cleaned_text) else None,
        "influencer_tier": get_influencer_tier_from_text(followers_text)
    }
