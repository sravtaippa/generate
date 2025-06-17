import asyncio
from flask import Flask, request, jsonify
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import nodriver as uc
import re

app = Flask(__name__)

async def scrape_tiktok_profile(browser, username: str) -> Dict[str, Optional[str]]:
    url = f"https://www.tiktok.com/@{username}"
    page = await browser.get(url)
    await asyncio.sleep(10)
    html_content = await page.evaluate('document.documentElement.outerHTML')
    soup = BeautifulSoup(html_content, 'html.parser')

    profile_info = {
        'username': username,
        'display_name': None,
        'follower_count': None,
        'following_count': None,
        'likes_count': None,
        'bio': None,
        'profile_image_url': None,
        'verified': False,
        'external_link': None
    }

    display_name_elem = soup.select_one('h2[data-e2e="user-subtitle"]')
    if display_name_elem:
        profile_info['display_name'] = display_name_elem.text.strip()

    follower_count_elem = soup.select_one('strong[data-e2e="followers-count"]')
    if follower_count_elem:
        profile_info['follower_count'] = follower_count_elem.text.strip()

    following_count_elem = soup.select_one('strong[data-e2e="following-count"]')
    if following_count_elem:
        profile_info['following_count'] = following_count_elem.text.strip()

    likes_count_elem = soup.select_one('strong[data-e2e="likes-count"]')
    if likes_count_elem:
        profile_info['likes_count'] = likes_count_elem.text.strip()

    bio_elem = soup.select_one('h2[data-e2e="user-bio"]')
    if bio_elem:
        profile_info['bio'] = bio_elem.text.strip()

    avatar_elem = soup.select_one('img[data-e2e="user-avatar"]')
    if avatar_elem and avatar_elem.has_attr('src'):
        profile_info['profile_image_url'] = avatar_elem['src']
    else:
        avatar_elem = soup.select_one('img[class*="avatar"]')
        if avatar_elem and avatar_elem.has_attr('src'):
            profile_info['profile_image_url'] = avatar_elem['src']
        else:
            avatar_div = soup.select_one('div[class*="avatar"]')
            if avatar_div and avatar_div.has_attr('style'):
                match = re.search(r'url\((.*?)\)', avatar_div['style'])
                if match:
                    profile_info['profile_image_url'] = match.group(1).strip('"\'')
    
    verified_elem = soup.select_one('span[data-e2e="user-verified"]')
    profile_info['verified'] = bool(verified_elem)

    link_elem = soup.select_one('a[data-e2e="user-link"]')
    if link_elem and link_elem.has_attr('href'):
        profile_info['external_link'] = link_elem['href']

    return profile_info

async def scrape_multiple_profiles(usernames: List[str]) -> List[Dict[str, Optional[str]]]:
    browser = await uc.start(headless=True)
    try:
        results = []
        for username in usernames:
            print(f"Scraping: {username}")
            profile = await scrape_tiktok_profile(browser, username)
            results.append(profile)
        return results
    finally:
        browser.stop()