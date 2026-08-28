// Random-poster viewer (random.html). Reads the poster list embedded by the
// build script, shows one poster, and swaps to another on "Next". The gallery
// itself does not depend on this file.
(function () {
  "use strict";

  var dataEl = document.getElementById("poster-data");
  var stage = document.getElementById("stage");
  var nextBtn = document.getElementById("next-btn");
  if (!dataEl || !stage) return;

  var posters;
  try {
    posters = JSON.parse(dataEl.textContent);
  } catch (e) {
    posters = [];
  }

  if (!posters.length) {
    stage.innerHTML =
      '<p class="viewer-empty">No posters yet. ' +
      '<a href="index.html">Back to the gallery</a>.</p>';
    if (nextBtn) nextBtn.disabled = true;
    return;
  }

  var prefersReducedMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;",
               '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function indexOfId(id) {
    for (var i = 0; i < posters.length; i++) {
      if (posters[i].id === id) return i;
    }
    return -1;
  }

  var currentIndex = -1;

  function render(i) {
    currentIndex = i;
    var p = posters[i];

    var meta = ['<div class="poster-meta">'];
    if (p.subteam) meta.push('<p class="card-badge">' + esc(p.subteam) + '</p>');
    meta.push('<h2>' + esc(p.title) + '</h2>');
    if (p.team) meta.push('<p class="team-name">' + esc(p.team) + '</p>');
    if (p.authors) meta.push('<p class="card-authors">' + esc(p.authors) + '</p>');
    if (p.description) meta.push('<p class="card-desc">' + esc(p.description) + '</p>');
    meta.push('<a class="pdf-link" href="' + p.pdf + '" target="_blank" ' +
      'rel="noopener" download>View / Download PDF ' +
      '<span aria-hidden="true">&#8599;</span></a>');
    meta.push('</div>');

    var fade = prefersReducedMotion ? "" : " poster-fade";
    var dims = (p.w && p.h) ? ' width="' + p.w + '" height="' + p.h + '"' : "";
    stage.innerHTML =
      '<div class="poster-stage' + fade + '">' +
        '<figure class="poster-figure" tabindex="-1" ' +
          'aria-label="Poster: ' + esc(p.title) + '">' +
          '<a href="' + p.pdf + '" target="_blank" rel="noopener" ' +
            'aria-label="Open PDF: ' + esc(p.title) + '">' +
            '<img src="' + p.img + '"' + dims + ' alt="' + esc(p.alt) +
              '" decoding="async">' +
          '</a>' +
        '</figure>' +
        meta.join("") +
      '</div>';

    if (history.replaceState) {
      history.replaceState(null, "", "#" + p.id);
    } else {
      location.hash = p.id;
    }

    // Scroll past the site header so the viewer region sits at the top, then
    // move keyboard focus to the poster (preventScroll so focus won't override).
    var viewer = document.getElementById("viewer");
    function bringViewerToTop() {
      if (viewer && viewer.scrollIntoView) {
        viewer.scrollIntoView({
          behavior: prefersReducedMotion ? "auto" : "smooth",
          block: "start"
        });
      }
    }
    bringViewerToTop();
    // The image reserves its space via width/height, but re-align once it has
    // actually loaded in case metrics shift.
    var img = stage.querySelector(".poster-figure img");
    if (img && !img.complete) {
      img.addEventListener("load", bringViewerToTop, { once: true });
      img.addEventListener("error", bringViewerToTop, { once: true });
    }
    var figure = stage.querySelector(".poster-figure");
    var target = figure || stage;
    try { target.focus({ preventScroll: true }); } catch (e) { target.focus(); }
  }

  function pickRandom() {
    if (posters.length === 1) return 0;
    var i;
    do {
      i = Math.floor(Math.random() * posters.length);
    } while (i === currentIndex);
    return i;
  }

  function showNext() { render(pickRandom()); }

  if (nextBtn) {
    nextBtn.addEventListener("click", showNext);
    if (posters.length === 1) nextBtn.disabled = true;
  }

  // Deep link: random.html#<id> shows that poster; otherwise pick at random.
  var fromHash = indexOfId((location.hash || "").replace(/^#/, ""));
  render(fromHash >= 0 ? fromHash : pickRandom());
})();
