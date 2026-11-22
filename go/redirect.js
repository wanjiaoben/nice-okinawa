(function () {
  'use strict';
  var body = document.body;
  var source = body.getAttribute('data-source') || '';
  var target = body.getAttribute('data-target') || 'https://bjt.nice.okinawa/mogi/trial/?lang=en';
  var moved = false;
  function go() {
    if (moved) return;
    moved = true;
    location.replace(target);
  }
  try {
    fetch('https://analytics.nice.okinawa/source-click', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ source: source }),
      keepalive: true,
      mode: 'cors'
    }).then(go, go);
    setTimeout(go, 300);
  } catch (error) {
    go();
  }
}());
