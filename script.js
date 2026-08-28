// Poster Showcase — random-poster interaction (progressive enhancement).
// The gallery is fully browsable without this script; it only powers the
// "Show me a random poster" button.
(function () {
  "use strict";

  var btn = document.getElementById("random-btn");
  if (!btn) return;

  var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));
  if (cards.length === 0) {
    btn.disabled = true;
    return;
  }

  var lastIndex = -1;
  var clearTimer = null;

  var prefersReducedMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function pickIndex() {
    if (cards.length === 1) return 0;
    var i;
    do {
      i = Math.floor(Math.random() * cards.length);
    } while (i === lastIndex);
    return i;
  }

  function showRandom() {
    var i = pickIndex();
    lastIndex = i;
    var card = cards[i];

    // Clear any previous highlight so the animation can retrigger.
    if (clearTimer) {
      clearTimeout(clearTimer);
      cards.forEach(function (c) { c.classList.remove("is-highlighted"); });
    }

    card.scrollIntoView({
      behavior: prefersReducedMotion ? "auto" : "smooth",
      block: "center"
    });

    // Move keyboard focus to the card's primary link (falls back to the card).
    var target = card.querySelector(".card-title a") ||
                 card.querySelector("a") || card;
    try { target.focus({ preventScroll: true }); } catch (e) { target.focus(); }

    card.classList.add("is-highlighted");
    clearTimer = setTimeout(function () {
      card.classList.remove("is-highlighted");
      clearTimer = null;
    }, 2000);
  }

  btn.addEventListener("click", showRandom);
})();
