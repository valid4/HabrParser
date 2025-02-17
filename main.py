import os
import re
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import argparse

def sanitize_filename(filename):
    """Удаляет недопустимые символы из названия файла."""
    return re.sub(r'[\\/*?:"<>|]', '', filename)

def get_fullsize_image_url(img_tag):
    """
    Извлекает ссылку на полноразмерное изображение из тега <img>.
    Проверяет сначала атрибут data-src, затем src.
    """
    # Пробуем получить полноразмерное изображение из data-src
    fullsize_url = img_tag.get('data-src')
    if fullsize_url:
        return fullsize_url
    
    # Если data-src отсутствует, используем src
    src_url = img_tag.get('src')
    if src_url:
        # Удаляем параметры после '?', если они есть
        if '?' in src_url:
            src_url = src_url.split('?')[0]
        return src_url
    
    # Если ни один из атрибутов не найден, возвращаем None
    return None

def parse_habr_article(url, save_path="."):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Отправляем GET-запрос к странице статьи
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Не удалось получить доступ к статье. Код ошибки: {response.status_code}")
        return None

    # Парсим HTML-код страницы
    soup = BeautifulSoup(response.content, 'html.parser')

    # Ищем заголовок статьи
    title_element = soup.find('h1', class_='tm-title tm-title_h1')
    if not title_element:
        print("Не удалось найти заголовок статьи.")
        return None
    title = title_element.text.strip()

    # Ищем основной контент статьи
    article_content = soup.find('div', class_='tm-article-body')
    if not article_content:
        print("Не удалось найти содержимое статьи.")
        return None

    # Улучшаем качество изображений
    for img in article_content.find_all('img'):
        fullsize_url = get_fullsize_image_url(img)
        if fullsize_url:
            img['src'] = fullsize_url  # Заменяем src на полноразмерную версию

    # Ищем теги статьи
    tags_elements = soup.find_all('li', class_='tm-separated-list__item')
    tags = [tag.text.strip().replace(' ', '_') for tag in tags_elements]

    # Преобразуем HTML в Markdown
    markdown_text = md(str(article_content))

    # Формируем имя файла на основе заголовка статьи
    sanitized_title = sanitize_filename(title)
    file_name = f"{sanitized_title}.md"
    full_path = os.path.join(save_path, file_name)

    # Создаем директорию, если её нет
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Сохраняем результат в файл с тегами в формате YAML
    with open(full_path, 'w', encoding='utf-8') as file:
        # Добавляем метаданные в формате YAML
        file.write("---\n")
        file.write("tags:\n")
        for tag in tags:
            file.write(f"- {tag}\n")
        file.write("---\n\n")

        # Добавляем заголовок статьи
        #file.write(f"# {title}\n\n")

        # Добавляем основной текст статьи
        file.write(markdown_text)

    print(f"Статья успешно сохранена в файл: {full_path}")

if __name__ == "__main__":
    # Настройка парсера аргументов командной строки
    parser = argparse.ArgumentParser(description="Парсер статей с Habr.com")
    parser.add_argument("url", type=str, help="Ссылка на статью на Habr")
    parser.add_argument("save_path", type=str, nargs="?", default=".", help="Путь для сохранения файла (по умолчанию текущая директория)")

    args = parser.parse_args()

    # Вызов функции с передачей аргументов из терминала
    parse_habr_article(args.url, args.save_path)