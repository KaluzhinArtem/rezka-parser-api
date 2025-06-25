from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from scrapingbee import ScrapingBeeClient
from bs4 import BeautifulSoup
from urllib.parse import quote
import os

# --- FastAPI App ---
app = FastAPI(
    title="HDRezka Unofficial API",
    description="API для поиска контента через ScrapingBee прокси.",
    version="2.0.0",
)

# --- Конфигурация ---
BASE_URL = "https://hdrezka.ag"

# Получаем API ключ из переменных окружения Vercel
API_KEY = os.environ.get('SCRAPINGBEE_API_KEY')

# Проверяем, доступен ли ключ
if not API_KEY:
    # Эта ошибка будет видна в логах Vercel, если ключ не установлен
    raise RuntimeError("SCRAPINGBEE_API_KEY is not set in environment variables")

client = ScrapingBeeClient(api_key=API_KEY)

# --- Маршруты API ---

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
        # Отправляем запрос через ScrapingBee
        response = client.get(search_url)
        
        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Прокси-сервис вернул ошибку: {response.text}"
            )

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
        raise HTTPException(status_code=500, detail=f"Произошла внутренняя ошибка: {e}")
