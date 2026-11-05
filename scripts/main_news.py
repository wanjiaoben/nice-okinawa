"""Content-only news records for the existing homepage builder."""
import json
import re

def load_news(root, copy):
    source = root / 'content/home/news.json'
    if not source.exists():
        return []
    records = json.loads(source.read_text())
    if not isinstance(records, list) or len(records) > 20:
        raise ValueError('news records')
    seen = set()
    for item in records:
        if set(item) != {'id', 'slug', 'date', 'title', 'description', 'link'}:
            raise ValueError('news schema')
        if not re.fullmatch(r'[A-Za-z0-9-]{1,80}', item['id']) or item['id'] in seen:
            raise ValueError('news identity')
        seen.add(item['id'])
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', item['slug']):
            raise ValueError('news slug')
        if not re.fullmatch(r'\d{4}\.\d{2}\.\d{2}', item['date']):
            raise ValueError('news date')
        for key in ('title', 'description', 'link'):
            if not isinstance(item[key], str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,79}', item[key]):
                raise ValueError('unsafe news translation key')
            if item[key] not in copy:
                raise ValueError('news translation missing')
    return records

def render_news(root, copy, news):
    result = ''
    for item in load_news(root, copy):
        block = news(item['title'], item['description'], item['date'],
                     '/zh-hans/news/' + item['slug'] + '/', item['link'])
        block = block.replace('data-route=""', 'data-news-slug="' + item['slug'] + '"')
        result += block
    return result
