(() => {
  'use strict';
  const locales = ['zh-Hans', 'zh-Hant', 'ja', 'en'];
  const copy = window.NiceHomeCopy;
  const resolver = window.SinkolaboUiLanguage;
  const siteRoot = new URL('../../', document.currentScript.src);
  let storage;
  try { storage = window.localStorage; } catch (_) { storage = null; }
  let locale = resolver.resolveUiLanguage({storage});
  if (!locales.includes(locale)) locale = 'en'; // Supported-overlay fallback, not browser detection.
  const text = key => copy[key][locales.indexOf(locale)];
  const pathLocales = {'zh-Hans':'zh-hans','zh-Hant':'zh-hant',ja:'ja',en:'en'};
  function applyLanguage() {
    document.documentElement.lang = locale;
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = text(el.dataset.i18n); });
    document.getElementById('language').value = locale;
    document.getElementById('language').setAttribute('aria-label', text('language'));
    document.title = [text('travel'),text('learn'),text('business')].join('・') + '｜Nice Okinawa';
    document.querySelector('meta[name="description"]').content = text('aboutBody');
    document.querySelector('meta[property="og:title"]').content = document.title;
    document.querySelector('meta[property="og:description"]').content = text('heroDesc');
    const prefix = pathLocales[locale];
    const routes = {
      b2bDesk:locale === 'zh-Hans' ? '/zh-hans/partners/' : '/en/partners/',
      kerama:`/${prefix}/kerama-snorkeling/`,
      transport:`/${locale === 'zh-Hant' ? 'zh-hans' : prefix}/news/okinawa-licensed-transport-guide-20261104/`,
      tourism:`/${locale === 'zh-Hans' ? 'zh-hant' : prefix}/news/okinawa-tourism-h1-2026/`,
      partners:({'zh-Hans':'/zh/partners/','zh-Hant':'/zh-hant/partners/',ja:'/ja/partners/',en:'/partners/'})[locale]
    };
    document.querySelectorAll('[data-route]').forEach(el => { if (routes[el.dataset.route]) el.href = new URL('.'+routes[el.dataset.route], siteRoot).href; });
    document.querySelectorAll('[data-b2b-desk]').forEach(el => { el.hidden = !['zh-Hans','en'].includes(locale); });
    document.querySelectorAll('[data-news-slug]').forEach(el => {
      const slug = el.dataset.newsSlug;
      if (/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) el.href = new URL('./'+prefix+'/news/'+slug+'/', siteRoot).href;
    });
    document.getElementById('form-status').textContent = '';
  }
  document.getElementById('language').addEventListener('change', event => {
    locale = event.target.value;
    try { storage && storage.setItem(resolver.UI_LANGUAGE_KEY, locale); } catch (_) { /* Private mode: keep in-memory choice. */ }
    const url = new URL(location.href); url.searchParams.set('lang',locale); history.replaceState(null,'',url);
    applyLanguage();
  });
  const form = document.getElementById('contact-form');
  const status = document.getElementById('form-status');
  function send(channel) {
    status.classList.remove('error');
    if (!form.checkValidity()) {
      status.classList.add('error'); status.textContent = text('required');
      form.querySelector(':invalid').focus();
      return;
    }
    const name = document.getElementById('cf-name').value.trim();
    const email = document.getElementById('cf-email').value.trim();
    const message = document.getElementById('cf-message').value.trim();
    if (!name || !message) { status.classList.add('error'); status.textContent = text('required'); return; }
    const key = document.getElementById('cf-type').value;
    const subject = key ? text(key) : 'Nice Okinawa';
    const body = `${text('name')}: ${name}\n${text('email')}: ${email}\n${text('topic')}: ${subject}\n\n${message}`;
    if (channel === 'email') window.location.href = `mailto:info@nice.okinawa?subject=${encodeURIComponent(subject+' / '+name)}&body=${encodeURIComponent(body)}`;
    else window.open(`https://wa.me/817089523968?text=${encodeURIComponent(body)}`,'_blank','noopener');
    status.textContent = text('opened');
  }
  form.addEventListener('submit', e => { e.preventDefault(); send('email'); });
  document.getElementById('waBtn').addEventListener('click', () => send('whatsapp'));
  applyLanguage();
})();
