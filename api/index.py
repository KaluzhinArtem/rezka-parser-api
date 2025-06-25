from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import requests
from bs4 import BeautifulSoup
import re
import base64

# Создаем приложение FastAPI
app = FastAPI(
    title="HDRezka Unofficial API",
    description="API для поиска контента и получения информации о фильмах/сериалах с hdrezka.ag",
    version="1.0.0",
)

# Базовый URL сайта и заголовки для запросов
BASE_URL = "https://hdrezka.ag"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
}

# --- Вспомогательные функции ---

def get_page_soup(url: str):
    """Получает soup-объект для указанного URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Ошибка при доступе к сайту: {e}")

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
    
    soup = get_page_soup(f"{BASE_URL}/search/?do=search&subaction=search&q={q}")
    
    results = []
    items = soup.find_all("div", class_="b-content__inline_item")

    for item in items:
        link_tag = item.find("a", class_="b-content__inline_item-link")
        img_tag = item.find("img")
        
        if link_tag and img_tag:
            details_url = link_tag.get("href")
            title = img_tag.get("alt")
            poster_url = img_tag.get("src")
            # Извлекаем описание (год, страна, жанр)
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


@app.get("/api/details", tags=["Content"])
def get_details(url: str):
    """
    Получение детальной информации о фильме/сериале и ссылок на видеопотоки.
    Принимает полный URL страницы с контентом.
    """
    if not url.startswith(BASE_URL):
        raise HTTPException(status_code=400, detail="URL должен начинаться с " + BASE_URL)

    soup = get_page_soup(url)
    
    # Находим "id" контента и другую информацию для запроса видео
    init_script = soup.find("script", text=re.compile("sof.tv.initCDN"))
    if not init_script:
        raise HTTPException(status_code=404, detail="Не удалось найти скрипт для получения видео.")

    # Извлекаем параметры из скрипта с помощью регулярных выражений
    post_id = re.search(r"sof.tv.initCDN\((\d+),", init_script.string)
    translator_id = re.search(r"(\d+), 'default'", init_script.string)
    
    if not post_id or not translator_id:
        raise HTTPException(status_code=500, detail="Не удалось извлечь ID контента или перевода.")

    # Это упрощенная логика. Настоящая логика сайта сложнее и может потребовать
    # выполнения JS кода. Мы эмулируем основной запрос.
    # В base64 кодируется строка вида "id,translator_id"
    # Этот эндпоинт может потребовать доработки, если сайт изменит логику
    try:
        # Эмуляция получения видеопотоков (это самая сложная часть)
        # Сайт использует сложную обфускацию JS. 
        # Этот код является заглушкой и показывает, как мог бы выглядеть результат.
        # Реальная реализация потребует обратного инжиниринга JS-кода сайта.
        
        # Пример того, как могут выглядеть ссылки (это ненастоящие ссылки)
        mock_streams = {
            "360p": "https://.../video.mp4?quality=360p",
            "480p": "https://.../video.mp4?quality=480p",
            "720p": "https://.../video.mp4?quality=720p",
            "1080p": "https://.../video.mp4?quality=1080p",
        }

        title = soup.find("h1", itemprop="name").text.strip()
        description = soup.find("div", class_="b-post__description_text").text.strip()

        return {
            "title": title,
            "description": description,
            "streams": mock_streams,
            "message": "ВНИМАНИЕ: Ссылки на видео являются заглушками. Реализация этой части требует сложного анализа."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось обработать данные для видео: {e}")
