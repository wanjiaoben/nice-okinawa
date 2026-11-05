(function (root) {
  'use strict';

  var UI_LANGUAGE_KEY = 'bjt_ui_lang';
  var DEFAULT_LANGUAGE = 'en';
  var CANONICAL_UI_LANGUAGES = [
    'zh-Hans', 'zh-Hant', 'ja', 'en', 'vi', 'id', 'ne', 'fr', 'de', 'es', 'it', 'ko', 'th'
  ];
  var aliases = {
    'zh-hans': 'zh-Hans', 'zh-cn': 'zh-Hans', 'zh-sg': 'zh-Hans', 'zh': 'zh-Hans', 'cn': 'zh-Hans',
    'zh-hant': 'zh-Hant', 'zh-tw': 'zh-Hant', 'zh-hk': 'zh-Hant', 'zh-mo': 'zh-Hant', 'tw': 'zh-Hant',
    'ja': 'ja', 'jp': 'ja', 'en': 'en', 'vi': 'vi', 'id': 'id', 'ne': 'ne', 'fr': 'fr',
    'de': 'de', 'es': 'es', 'it': 'it', 'ko': 'ko', 'th': 'th'
  };

  function normalizeUiLanguage(value) {
    var raw = String(value || '').trim().toLowerCase().replace(/_/g, '-');
    if (!raw) return DEFAULT_LANGUAGE;
    if (aliases[raw]) return aliases[raw];
    var base = raw.split('-')[0];
    if (base === 'zh') return /^zh-(tw|hant|hk|mo)(-|$)/.test(raw) ? 'zh-Hant' : 'zh-Hans';
    return aliases[base] || DEFAULT_LANGUAGE;
  }

  function readSavedLanguage(storage) {
    try {
      var value = storage && storage.getItem ? storage.getItem(UI_LANGUAGE_KEY) : '';
      return value ? normalizeUiLanguage(value) : '';
    } catch (_) { return ''; }
  }

  function readUrlLanguage(url) {
    try {
      var parsed = new URL(url || (root.location && root.location.href) || 'https://invalid.local/');
      var value = parsed.searchParams.get('lang') || parsed.searchParams.get('ui');
      return value ? normalizeUiLanguage(value) : '';
    } catch (_) { return ''; }
  }

  function resolveUiLanguage(options) {
    options = options || {};
    var storage = Object.prototype.hasOwnProperty.call(options, 'storage') ? options.storage : root.localStorage;
    var saved = readSavedLanguage(storage);
    if (saved) return saved;
    var url = Object.prototype.hasOwnProperty.call(options, 'url') ? options.url : undefined;
    var fromUrl = readUrlLanguage(url);
    if (fromUrl) return fromUrl;
    var languages = Object.prototype.hasOwnProperty.call(options, 'languages') ? options.languages : (root.navigator && root.navigator.languages);
    var first = Array.isArray(languages) ? languages[0] : '';
    return normalizeUiLanguage(first) || DEFAULT_LANGUAGE;
  }

  function browserLanguages() {
    return root.navigator && Array.isArray(root.navigator.languages) ? root.navigator.languages.slice() : [];
  }

  root.SinkolaboUiLanguage = Object.freeze({
    UI_LANGUAGE_KEY: UI_LANGUAGE_KEY,
    DEFAULT_LANGUAGE: DEFAULT_LANGUAGE,
    CANONICAL_UI_LANGUAGES: Object.freeze(CANONICAL_UI_LANGUAGES.slice()),
    normalizeUiLanguage: normalizeUiLanguage,
    browserLanguages: browserLanguages,
    resolveUiLanguage: resolveUiLanguage
  });
}(typeof globalThis !== 'undefined' ? globalThis : window));
