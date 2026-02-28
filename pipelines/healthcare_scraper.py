import os
import json
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Selenium (fallback for dynamic sites)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ==============================
# CONFIG – 12 HEALTHCARE URLS
# ==============================

websites = [
    {
        "url": "https://www.india.gov.in/topics/health-family-welfare",
        "scheme_name": "National Portal Health & Family Welfare",
        "ministry": "Health",
    },
    {
        "url": "https://www.myscheme.gov.in/search/category/health",
        "scheme_name": "myScheme Health Category",
        "ministry": "Multiple",
    },
    {
        "url": "https://pmjay.gov.in/",
        "scheme_name": "Ayushman Bharat PM-JAY",
        "ministry": "Health",
    },
    {
        "url": "https://www.ayush.gov.in/",
        "scheme_name": "Ministry of AYUSH",
        "ministry": "AYUSH",
    },
    {
        "url": "https://rchrpt.nhm.gov.in/",
        "scheme_name": "RCH Portal",
        "ministry": "Health",
    },
    {
        "url": "https://nhm.gov.in/",
        "scheme_name": "National Health Mission",
        "ministry": "Health",
    },
    {
        "url": "https://cghs.gov.in/",
        "scheme_name": "Central Government Health Scheme",
        "ministry": "Health",
    },
    {
        "url": "https://notto.mohfw.gov.in/",
        "scheme_name": "NOTTO",
        "ministry": "Health",
    },
    {
        "url": "https://ors.gov.in/",
        "scheme_name": "eHospital ORS Portal",
        "ministry": "Health",
    },
    {
        "url": "https://www.india.gov.in/state-portal",
        "scheme_name": "State Health Departments",
        "ministry": "Multiple",
    },
    {
        "url": "https://www.myscheme.gov.in/",
        "scheme_name": "Health Insurance Schemes",
        "ministry": "Multiple",
    },
    {
        "url": "https://cdsco.gov.in/",
        "scheme_name": "Drug Controller General of India",
        "ministry": "Health",
    },
]


# ==============================
# STATIC SCRAPER
# ==============================

def scrape_static(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text

    except:
        return None


# ==============================
# SELENIUM SCRAPER (Fallback)
# ==============================

def scrape_dynamic(url):
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(url)

        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text

    except:
        return None


# ==============================
# CLEAN TEXT
# ==============================

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ==============================
# CHUNKING (700 words approx)
# ==============================

def chunk_text(text, chunk_size=700):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


# ==============================
# MAIN EXECUTION
# ==============================

def main():
    os.makedirs("data", exist_ok=True)
    all_chunks = []

    for site in tqdm(websites):
        print(f"\nScraping: {site['scheme_name']}")

        text = scrape_static(site["url"])

        if not text:
            print("Static failed → Trying Selenium...")
            text = scrape_dynamic(site["url"])

        if not text:
            print("Failed to scrape.")
            continue

        cleaned = clean_text(text)
        chunks = chunk_text(cleaned)

        for idx, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"healthcare_{site['scheme_name'].lower().replace(' ', '_')}_{idx}",
                "text": chunk,
                "domain": "healthcare",
                "scheme_name": site["scheme_name"],
                "section": "general",
                "ministry": site["ministry"],
                "source": site["url"]
            })

    with open("data/healthcare_chunks.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=4)

    print("\n✅ All healthcare data saved to data/healthcare_chunks.json")


if __name__ == "__main__":
    main()