(function () {
  "use strict";

  // スクロール時の軽いフェードイン演出のみ（指示書13章: 必要最低限）。
  // JSが無効/失敗しても内容は最初から表示されているため、閲覧に支障はない。

  var targets = document.querySelectorAll(".fade-in");

  if (!("IntersectionObserver" in window) || targets.length === 0) {
    targets.forEach(function (el) {
      el.classList.add("is-visible");
    });
    return;
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
  );

  targets.forEach(function (el) {
    observer.observe(el);
  });
})();
