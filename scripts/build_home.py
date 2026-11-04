#!/usr/bin/env python3
"""Homepage: Chinese original + aligned overlays. Run after editing content/home/copy.json."""
import json
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
copy = json.loads((ROOT / 'content/home/copy.json').read_text())
assert all(len(v) == 4 and all(isinstance(s, str) and s for s in v) for v in copy.values())
def t(key, tag='span', attrs=''):
    return f'<{tag} data-i18n="{key}" {attrs}>{escape(copy[key][0])}</{tag}>'
def a(key, url, cls='', extra=''):
    return t(key, 'a', f'href="{url}" class="{cls}" {extra}')
def card(name, domain, icon):
    return f'<a class="card" href="https://{domain}.nice.okinawa/"><span class="card-icon" aria-hidden="true">{icon}</span><span class="domain">{domain}.nice.okinawa</span>' + t(name+'Title','h3') + t(name+'Desc','p') + t('visit',attrs='class="text-link"') + '</a>'
def head(key, desc=None):
    return f'<div class="section-head">{t(key,"h2")}{t(desc,"p") if desc else ""}</div>'
def news(title, desc, date, href, link, route=''):
    return f'<a href="{href}" class="card tips-card" data-route="{route}"><time class="tips-kicker">{date}</time>' + t(title,'h3','class="tips-title"') + t(desc,'p','class="tips-desc"') + t(link,attrs='class="text-link"') + '</a>'
html = '''<!doctype html>
<html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>冲绳旅游・语言教室・出口贸易｜Nice Okinawa</title>
<meta name="description" content="以冲绳那霸为据点，提供旅游、日语学习、翻译口译与日本中古车出口服务。CatalinaJapan 株式会社，2009 年创立。">
<meta name="theme-color" content="#EFF6FA"><meta name="author" content="CatalinaJapan株式会社">
<link rel="canonical" href="https://nice.okinawa/">
<meta property="og:type" content="website"><meta property="og:site_name" content="Nice Okinawa">
<meta property="og:title" content="冲绳旅游・语言教室・出口贸易｜Nice Okinawa">
<meta property="og:description" content="旅行、学习与跨境合作，从冲绳开始。">
<meta property="og:url" content="https://nice.okinawa/"><meta property="og:image" content="https://nice.okinawa/og-cover.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="assets/home.css">
<script src="assets/js/ui-language-resolver.js"></script>
<script src="assets/js/home-copy.js"></script>
</head><body>'''
html += a('skip','#main','skip')
html += '<header class="masthead"><div class="wrap header-inner"><a class="logo" href="#main">Nice <em>Okinawa</em><small>CATALINA JAPAN · SINCE 2009</small></a><nav class="nav">'
html += ''.join(a(k,v) for k,v in [('navSites','#sites'),('navNews','#news'),('navAbout','#about'),('navContact','#contact')])
html += '</nav><select id="language" class="language" aria-label="选择语言"><option value="zh-Hans">简体中文</option><option value="zh-Hant">繁體中文</option><option value="ja">日本語</option><option value="en">English</option></select></div></header><main id="main">'
html += '<section class="hero wrap"><div class="hero-grid"><div class="hero-copy">'+t('eyebrow','p','class="eyebrow"')+t('heroTitle','h1','style="white-space:pre-line"')+t('heroDesc','p')+'<div class="actions">'+a('explore','#sites','button')+a('navContact','#contact','button secondary')+'</div></div>'
html += '<div class="hero-art"><img src="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1000&amp;q=85" alt="" width="1000" height="700" fetchpriority="high">'+t('photo','span','class="photo-caption"')+'</div></div><div class="gateway" id="services">'
for i,key in enumerate(['travel','learn','business']):
    html += f'<a href="#{key}"><small>0{i+1}</small>{t(key,"h2")}{t(key+"Short","p")}<span class="arrow" aria-hidden="true">↗</span></a>'
html += '</div></section><section class="block wrap" id="sites">'+head('servicesTitle','servicesDesc')
for group,cards in [('travel',[('snorkel','snorkel','◌'),('fishing','fishing','⌁'),('activity','activity','☀'),('golf','golf','⚑'),('rental','rental','↗')]),('learn',[('bjt','bjt','文'),('kiso','kiso','あ'),('progress','progress','↻'),('training','training','↗')]),('business',[('cars','japanusedcars','↗'),('translation','translation','文')])]:
    html += f'<div class="site-group" id="{group}">' + t(group,'h3','class="group-title"') + '<div class="cards">'
    html += ''.join(card(*item) for item in cards)+'</div>'
    if group == 'travel': html += a('kerama','/zh-hans/kerama-snorkeling/','sub-link','data-route="kerama"')
    html += '</div>'
html += '</section><section class="block news-section" id="news"><div class="wrap">'+head('newsTitle','newsDesc')+'<div class="tips-grid cards">'
html += '<!-- TRAVEL-TRANSPORT-20261104-01 START -->'+news('transportTitle','transportDesc','2026.11.04','/zh-hans/news/okinawa-licensed-transport-guide-20261104/','readTransport','transport')+'<!-- TRAVEL-TRANSPORT-20261104-01 END -->'
html += news('grantTitle','grantDesc','2026.11.03','https://training.nice.okinawa/news/naha-foreign-talent-training-grant-2026/','readJa')
html += news('tourismTitle','tourismDesc','2026.11.03','/zh-hant/news/okinawa-tourism-h1-2026/','readTourism','tourism')
html += '</div></div></section><section class="block wrap" id="travel-tips">'+head('guides')+'<div class="cards">'+news('typhoon','typhoonDesc','','/en/travel-tips/okinawa-typhoon-travel-safety/','readEn')+'</div></section>'
html += '<section class="block wrap" id="about"><div class="about-grid"><div>'+head('aboutTitle')+t('aboutBody','p')+t('aboutBody2','p')+'<div class="facts"><div><strong>2009</strong>'+t('founded')+'</div><div>'+t('base','strong')+t('baseLabel')+'</div></div><details id="history">'+t('history','summary')+'<ol class="timeline">'+''.join(t('history'+str(i),'li') for i in range(1,6))+'</ol></details></div><div class="partners-panel" id="partners">'+t('partnerTitle','h2')+t('partnerBody','p')+t('partnerDivision','p')+a('partnerCta','/zh/partners/','button','data-route="partners"')+t('partnerNote','p','class="form-note"')+'</div></div></section>'
html += '<section class="block contact" id="contact"><div class="wrap contact-grid"><div>'+t('contactTitle','h2')+t('contactDesc','p','style="margin-top:22px"')+'<div class="contact-links"><a href="mailto:info@nice.okinawa">info@nice.okinawa</a><a href="https://wa.me/817089523968" target="_blank" rel="noopener">WhatsApp · +81 70-8952-3968</a><button id="copy-wechat" type="button">'+t('wechat')+' · OkinawaOnline</button></div></div><form id="contact-form" novalidate><div class="form-grid">'
for key,typ in [('name','text'),('email','email')]:
    html += '<div>'+t(key,'label',f'for="cf-{key}"')+f'<input type="{typ}" id="cf-{key}" name="{key}" autocomplete="{key}" required aria-required="true"></div>'
html += '<div class="wide">'+t('topic','label','for="cf-type"')+'<select id="cf-type" name="topic">'+''.join(t(k,'option',f'value="{k if k != "choose" else ""}"') for k in ['choose','travel','snorkelTitle','bjtTitle','trainingTitle','business','other'])+'</select></div><div class="wide">'+t('message','label','for="cf-message"')+'<textarea id="cf-message" name="message" required aria-required="true"></textarea></div></div><div class="actions">'+t('sendEmail','button','class="button" id="submitBtn" type="submit"')+t('sendWa','button','class="button secondary" id="waBtn" type="button"')+'</div>'+t('formNote','p','class="form-note"')+'<p id="form-status" class="status" role="status" aria-live="polite"></p></form></div></section></main><footer><div class="wrap footer-inner">'+t('footer')+a('navAbout','#about')+a('navContact','#contact')+'</div></footer>'+a('navContact','#contact','float-contact')+'<script src="assets/js/home.js"></script>'
html += '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'Organization','name':'Nice Okinawa','legalName':'CatalinaJapan株式会社','url':'https://nice.okinawa/','foundingDate':'2009','email':'info@nice.okinawa','knowsLanguage':['zh','ja','en'],'address':{'@type':'PostalAddress','addressLocality':'Naha','addressRegion':'Okinawa','addressCountry':'JP'}},ensure_ascii=False)+'</script>'
html += '<script src="https://analytics.nice.okinawa/beacon.js" data-site="nice-okinawa" defer></script></body></html>\n'
(ROOT/'index.html').write_text(html)
(ROOT/'assets/js/home-copy.js').write_text('/* Generated from content/home/copy.json. Order: zh-Hans original, zh-Hant, ja, en. */\nwindow.NiceHomeCopy = '+json.dumps(copy,ensure_ascii=False)+';\n')
