/* Vianočný vzhľad webu: jemné sneženie a logo s čiapkou.
   Zapne sa sám od 1. decembra do 6. januára (podľa dátumu v zariadení návštevníka).
   Na vyskúšanie mimo obdobia pridajte k adrese ?vianoce, napr. /sk/?vianoce */
(function () {
  var d = new Date(), m = d.getMonth() + 1, day = d.getDate();
  var on = m === 12 || (m === 1 && day <= 6) || /[?&]vianoce\b/.test(location.search);
  if (!on) return;
  document.documentElement.classList.add('xmas');
  document.addEventListener('DOMContentLoaded', function () {
    var imgs = document.querySelectorAll('img[data-xmas]');
    for (var i = 0; i < imgs.length; i++) imgs[i].src = imgs[i].getAttribute('data-xmas');
  });
})();
