from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import quote
import requests

# Создаем приложение FastAPI
app = FastAPI(
    title="HDRezka Unofficial API",
    description="API для поиска контента с использованием cloudscraper для обхода защиты.",
    version="1.2.0",
)

# Создаем экземпляр скрейпера. Он будет вести себя как сессия requests.
scraper = cloudscraper.create_scraper()

# Базовый URL сайта
BASE_URL = "https://hdrezka.ag"

# --- Маршруты API ---

@app.get("/", tags=["General"])
def root():
    """Корневой маршрут для проверки. Перенаправляет на документацию API."""
    return RedirectResponse(url="/docs")


@app.get("/api/search", tags=["Content"])
def search_content(q: str):
    """
    Поиск контента на сайте по названию.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Параметр 'q' не может быть пустым.")
    
    encoded_q = quote(q)
    search_url = f"{BASE_URL}/search/?do=search&subaction=search&q={encoded_q}"
    
    try:
        # Используем scraper вместо requests.get
        response = scraper.get(search_url)
        response.raise_for_status() # Проверяем на ошибки HTTP
        
        soup = BeautifulSoup(response.text, "lxml")
        
        results = []
        items = soup.find_all("div", class_="b-content__inline_item")

        for item in items:
            link_tag = item.find("a", class_="b-content__inline_item-link")
            img_tag = item.find("img")
            
            if link_tag and img_tag:
                details_url = link_tag.get("href")
                title = img_tag.get("alt")
                poster_url = img_tag.get("src")
                description = " ".join(link_tag.text.split())

                results.append({
                    "title": title,
                    "description": description,
                    "poster_url": poster_url,
                    "details_url": details_url,
                })
        
        if not results:
            raise HTTPException(status_code=404, detail="Ничего не найдено по вашему запросу.")
            
        return {"results": results}

    except requests.exceptions.RequestException as e:
        # Обрабатываем возможные ошибки сети или ответа от сайта
        status_code = e.response.status_code if e.response else 500
        raise HTTPException(status_code=status_code, detail=f"Ошибка при обращении к сайту: {e}")
    except Exception as e:
        # Обрабатываем другие возможные ошибки
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {e}")
