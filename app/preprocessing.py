import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Tuple

logger = logging.getLogger("app.preprocessing")

# 10 categories (approved)
CATEGORIES = [
    "Social Media", "Gaming", "Finance", "Travel", "Productivity",
    "Health & Fitness", "Education", "Communication", "E-Commerce", "Photography"
]

# Canonical 14 permissions
CANONICAL_PERMS = [
    "Location", "Personal info", "Financial info", "Health and fitness", "Messages",
    "Photos and videos", "Audio", "Calendar", "Files and docs", "App activity",
    "Web browsing", "App info and performance", "Device or other IDs", "Contacts"
]

# Blacklisted phrases (indicate noise, not a real permission)
BLACKLIST_PHRASES = [
    "encrypted", "deleted", "you can request", "you can request data",
    "you can request that", "we may collect", "we may use", "we may",
    "data is encrypted", "data is deleted", "not found", "see more",
    "show less", "learn more", "privacy policy"
]

def normalize_permission(raw: str) -> str:
    """
    Normalizes a raw permission string to a canonical permission label using heuristics.
    """
    if not raw:
        return raw
    r = raw.lower().strip()
    
    # Common keywords mapping to canonical forms
    mapping = {
        "microphone": "Audio",
        "audio": "Audio",
        "record": "Audio",
        "camera": "Photos and videos",
        "photo": "Photos and videos",
        "video": "Photos and videos",
        "location": "Location",
        "gps": "Location",
        "contact": "Contacts",
        "contacts": "Contacts",
        "financial": "Financial info",
        "payment": "Financial info",
        "card": "Financial info",
        "health": "Health and fitness",
        "fitness": "Health and fitness",
        "calendar": "Calendar",
        "events": "Calendar",
        "file": "Files and docs",
        "document": "Files and docs",
        "pdf": "Files and docs",
        "web": "Web browsing",
        "browser": "Web browsing",
        "performance": "App info and performance",
        "app info": "App info and performance",
        "device": "Device or other IDs",
        "id": "Device or other IDs",
        "messages": "Messages",
        "sms": "Messages",
        "chat": "Messages",
        "personal": "Personal info",
        "profile": "Personal info",
        "activity": "App activity"
    }
    
    for k, v in mapping.items():
        if k in r:
            return v
            
    # Exact match check
    for c in CANONICAL_PERMS:
        if c.lower() == r:
            return c
            
    # Fallback to title-case
    return raw.title()

def get_app_permissions_and_data_safety(app_id: str, language: str = "en") -> Tuple[List[str], str]:
    """
    Extracts raw permissions and data safety text for a given app_id by scraping Google Play Store.
    """
    headers = {"User-Agent": "Mozilla/5.0 (DemoBot)"}
    base = f"https://play.google.com/store/apps/datasafety?id={app_id}&hl={language}"
    logger.info(f"Scraping Play Store data safety page for app_id: {app_id}")
    try:
        resp = requests.get(base, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Failed to fetch Play Store page. Status code: {resp.status_code}")
            return ([], f"Error: status {resp.status_code}")
        soup = BeautifulSoup(resp.content, "html.parser")

        # Extract short data safety text
        sec = soup.find("div", class_="UugpPb")
        data_safety_text = sec.get_text(separator=" ").strip() if sec else ""

        # Extract permission headings
        raw = []
        for div in soup.find_all("div", class_="Mf2Txd"):
            sec2 = div.find("div", class_="XgPdwe")
            if not sec2:
                continue
            for h3 in sec2.find_all("h3", class_="aFEzEb"):
                txt = h3.get_text(strip=True)
                if txt:
                    raw.append(txt)

        # Fallback list items
        if not raw:
            for li in soup.find_all("li"):
                txt = li.get_text(strip=True)
                if txt:
                    raw.append(txt)

        # Filter out noise
        def is_noise(s: str) -> bool:
            if not s:
                return True
            low = s.lower()
            for phrase in BLACKLIST_PHRASES:
                if phrase in low:
                    return True
            if len(low) < 3:
                return True
            return False

        filtered = []
        seen = set()
        for p in raw:
            if is_noise(p):
                continue
            if p not in seen:
                seen.add(p)
                filtered.append(p)

        logger.info(f"Successfully scraped {len(filtered)} permissions for app_id: {app_id}")
        return filtered, data_safety_text
    except Exception as e:
        logger.exception(f"Error scraping data safety page for app_id {app_id}: {e}")
        return ([], f"Error scraping data safety: {e}")
