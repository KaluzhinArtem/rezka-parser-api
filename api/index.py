from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote

# Создаем приложение FastAPI
app = FastAPI(
    title="HDRezka Unofficial API",
    description="API для поиска контента и получения информации о фильмах/сериалах с hdrezka.ag",
    version="1.1.0",
)

# Базовый URL сайта и новые, более "человечные" заголовки
BASE_URL = "https://hdrezka.ag"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Referer': BASE_URL + '/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
}

# --- Вспомогательные функции ---

def get_page_soup(url: str):
    """Получает soup-объект для указанного URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        # Явно указываем кодировку, чтобы избежать проблем с кириллицей
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, "lxml")
    except requests.RequestException as e:
        # Возвращаем текст ошибки от сайта, если он есть
        error_detail = f"Ошибка при доступе к сайту: {e}"
        if e.response is not None:
            error_detail = f"Ошибка при досту-пе к сайту: {e.response.status_code} {e.response.reason} for url: {e.request.url}"
        raise HTTPException(status_code=503, detail=error_detail)

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
    
    # Явно кодируем поисковый запрос для URL
    encoded_q = quote(q)
    search_url = f"{BASE_URL}/search/?do=search&subaction=search&q={encoded_q}"
    
    soup = get_page_soup(search_url)
    
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