"""Content-only news records for the existing homepage builder."""
import json
import re

def load_news(root, copy):
    source = root / 'content/home/news.json'
    if not source.exists():
        return []
    records = json.loads(source.read_text())
    if not isinstance(records, list) or len(records) > 60:
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


def news_category(root, href):
    """Use existing article bylines / owning site without changing content records."""
    from urllib.parse import urlparse
    host = urlparse(href).hostname
    if host:
        if host.split('.')[0] in ('training', 'bjt', 'kiso', 'progress', 'lab'):
            return 'learning'
        if host.split('.')[0] in ('japanusedcars', 'translation'):
            return 'trade'
    path = root / href.lstrip('/') / 'index.html'
    if path.is_file():
        source = path.read_text()
        for raw in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', source, re.S):
            data = json.loads(raw)
            nodes = data if isinstance(data, list) else data.get('@graph', [data])
            for node in nodes:
                author = node.get('author', {})
                names = author if isinstance(author, list) else [author]
                for name in names:
                    name = name.get('name', '') if isinstance(name, dict) else name
                    if re.search(r'深耕|Shinko|Sinko', name, re.I):
                        return 'learning'
                    if re.search(r'CATALINA JAPAN', name, re.I):
                        return 'trade'
                    if name == 'Nice Okinawa':
                        return 'travel'
    print('HB-391 unclassified (travel fallback):', href)
    return 'travel'


def render_news_lists(root, copy):
    from html import escape
    entries = [dict(item, href='/zh-hans/news/' + item['slug'] + '/', attrs='data-news-slug="' + item['slug'] + '"') for item in load_news(root, copy)]
    entries += [
        dict(id='TRAVEL-TRANSPORT-20261104-01', title='transportTitle', date='2026.11.04', href='/zh-hans/news/okinawa-licensed-transport-guide-20261104/', attrs='data-route="transport"'),
        dict(id='legacy-training', title='grantTitle', date='2026.11.03', href='https://training.nice.okinawa/news/naha-foreign-talent-training-grant-2026/', attrs=''),
        dict(id='legacy-tourism', title='tourismTitle', date='2026.11.03', href='/zh-hant/news/okinawa-tourism-h1-2026/', attrs='data-route="tourism"'),
    ]
    categories = [('travel', 'newsTravel'), ('trade', 'newsTrade'), ('learning', 'newsLearning')]
    groups = {key: [] for key, _ in categories}
    for item in entries:
        groups[news_category(root, item['href'])].append(item)
    def row(item):
        title = escape(copy[item['title']][0])
        return (f'<li class="news-row"><a href="{escape(item["href"], quote=True)}" {item["attrs"]}>'
                f'<time datetime="{item["date"].replace(".", "-")}">{item["date"]}</time>'
                f'<span data-i18n="{item["title"]}">{title}</span></a></li>')
    result = '<div class="news-tabs" role="tablist" aria-label="' + escape(copy['newsCategories'][0]) + '" data-news-tabs>'
    for key, label in categories:
        result += f'<button type="button" role="tab" id="news-tab-{key}" aria-controls="news-panel-{key}" aria-selected="{str(key == "travel").lower()}" tabindex="{0 if key == "travel" else -1}" data-news-tab="{key}" data-i18n="{label}">{escape(copy[label][0])}</button>'
    result += '</div><div class="news-columns">'
    for key, label in categories:
        items = sorted(groups[key], key=lambda item: item['date'], reverse=True)
        result += f'<section class="news-column" id="news-panel-{key}" aria-labelledby="news-heading-{key}" data-news-panel="{key}"><h3 id="news-heading-{key}" data-i18n="{label}">{escape(copy[label][0])}</h3><ul class="news-items">'
        result += ''.join(row(item) for item in items[:3]) + '</ul>'
        if len(items) > 3:
            result += '<details class="news-more"><summary data-i18n="newsMore">' + escape(copy['newsMore'][0]) + '</summary><ul class="news-items">'
            result += ''.join(row(item) for item in items[3:]) + '</ul></details>'
        result += '</section>'
        print('HB-391 category:', key, len(items))
    return result + '</div><!-- TRAVEL-TRANSPORT-20261104-01 START --><!-- TRAVEL-TRANSPORT-20261104-01 END -->'
