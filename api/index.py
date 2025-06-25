from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import quote
import requests
from requests.adapters import HTTPAdapter

# --- SSL/TLS Handshake Fix ---
# hdrezka.ag uses advanced TLS fingerprinting. We need to mimic a browser's cipher suite.
# This is a robust cipher suite from a modern browser.
CIPHERS = (
    'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:'
    'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:'
    'DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384'
)

class TlsV1_2HttpAdapter(HTTPAdapter):
    """A custom HTTP adapter that forces TLSv1.2 and a specific cipher suite."""
    def __init__(self, *args, **kwargs):
        # We need to import this within the class on some platforms
        from ssl import PROTOCOL_TLSv1_2
        self.ssl_context = requests.packages.urllib3.util.ssl_.create_urllib3_context(
            ciphers=CIPHERS,
            ssl_version=PROTOCOL_TLSv1_2
        )
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = requests.packages.urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context
        )

# --- FastAPI App ---

app = FastAPI(
    title="HDRezka Unofficial API",
    description="API for searching content, with advanced TLS handshake bypass.",
    version="1.3.0",
)

# Create a scraper instance and mount our custom adapter
scraper = cloudscraper.create_scraper()
scraper.mount("https://", TlsV1_2HttpAdapter())

BASE_URL = "https://hdrezka.ag"

@app.get("/", tags=["General"])
def root():
    return RedirectResponse(url="/docs")

@app.get("/api/search", tags=["Content"])
def search_content(q: str):
    if not q:
        raise HTTPException(status_code=400, detail="Параметр 'q' не может быть пустым.")
    
    encoded_q = quote(q)
    search_url = f"{BASE_URL}/search/?do=search&subaction=search&q={encoded_q}"
    
    try:
        response = scraper.get(search_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        
        results = []
        items = soup.find_all("div", class_="b-content__inline_item")

        for item in items:
            link_tag = item.find("a", class_="b-content__inline_item-link")
            img_tag = item.find("img")
            
            if link_tag and img_tag:
                results.append({
                    "title": img_tag.get("alt"),
                    "description": " ".join(link_tag.text.split()),
                    "poster_url": img_tag.get("src"),
                    "details_url": link_tag.get("href"),
                })
        
        if not results:
            raise HTTPException(status_code=404, detail="Ничего не найдено по вашему запросу.")
            
        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")