 from fastapi import FastAPI, HTTPException
    2 from fastapi.responses import RedirectResponse
    3 import requests
    4 from bs4 import BeautifulSoup
    5 import re
    6 from urllib.parse import quote
    7
    8 # Создаем приложение FastAPI
    9 app = FastAPI(
   10     title="HDRezka Unofficial API",
   11     description="API для поиска контента и получения 
      информации о фильмах/сериалах с hdrezka.ag",
   12     version="1.1.0",
   13 )
   14
   15 # Базовый URL сайта и новые, более "человечные" заголовки
   16 BASE_URL = "https://hdrezka.ag"
   17 HEADERS = {
   18     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X
      10.15; rv:109.0) Gecko/20100101 Firefox/115.0',
   19     'Accept':
      'text/html,application/xhtml+xml,application/xml;q=0.9,imag
      e/avif,image/webp,*/*;q=0.8',
   20     'Accept-Language':
      'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
   21     'Referer': BASE_URL + '/',
   22     'Connection': 'keep-alive',
   23     'Upgrade-Insecure-Requests': '1',
   24     'Sec-Fetch-Dest': 'document',
   25     'Sec-Fetch-Mode': 'navigate',
   26     'Sec-Fetch-Site': 'same-origin',
   27     'Sec-Fetch-User': '?1',
   28 }
   29
   30 # --- Вспомогательные функции ---
   31
   32 def get_page_soup(url: str):
   33     """Получает soup-объект для указанного URL."""
   34     try:
   35         response = requests.get(url, headers=HEADERS,
      timeout=10)
   36         response.raise_for_status()
   37         # Явно указываем кодировку, чтобы избежать проблем
      с кириллицей
   38         response.encoding = 'utf-8'
   39         return BeautifulSoup(response.text, "lxml")
   40     except requests.RequestException as e:
   41         # Возвращаем текст ошибки от сайта, если он есть
   42         error_detail = f"Ошибка при доступе к сайту: {e}"
   43         if e.response is not None:
   44             error_detail = f"Ошибка при досту-пе к сайту: 
      {e.response.status_code} {e.response.reason} for url:
      {e.request.url}"
   45         raise HTTPException(status_code=503,
      detail=error_detail)
   46
   47 # --- Маршруты API ---
   48
   49 @app.get("/", tags=["General"])
   50 def root():
   51     """Корневой маршрут для проверки. Перенаправляет на 
      документацию API."""
   52     return RedirectResponse(url="/docs")
   53
   54
   55 @app.get("/api/search", tags=["Content"])
   56 def search_content(q: str):
   57     """
   58     Поиск контента на сайте по названию.
   59     """
   60     if not q:
   61         raise HTTPException(status_code=400, detail=
      "Параметр 'q' не может быть пустым.")
   62
   63     # Явно кодируем поисковый запрос для URL
   64     encoded_q = quote(q)
   65     search_url = f"{BASE_URL}
      /search/?do=search&subaction=search&q={encoded_q}"
   66
   67     soup = get_page_soup(search_url)
   68
   69     results = []
   70     items = soup.find_all("div", class_=
      "b-content__inline_item")
   71
   72     for item in items:
   73         link_tag = item.find("a", class_=
      "b-content__inline_item-link")
   74         img_tag = item.find("img")
   75
   76         if link_tag and img_tag:
   77             details_url = link_tag.get("href")
   78             title = img_tag.get("alt")
   79             poster_url = img_tag.get("src")
   80             description = " ".join(link_tag.text.split())
   81
   82             results.append({
   83                 "title": title,
   84                 "description": description,
   85                 "poster_url": poster_url,
   86                 "details_url": details_url,
   87             })
   88
   89     if not results:
   90         raise HTTPException(status_code=404, detail="Ничего
      не найдено по вашему запросу.")
   91
   92     return {"results": results}
   93
   94 # Маршрут /api/details пока остается без изменений
