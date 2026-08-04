(() => {
  const saved = localStorage.getItem("ratescope-theme");
  if (saved === "dark") document.documentElement.dataset.theme = "dark";
  if (!document.body.classList.contains("model-page")) document.querySelectorAll(".theme-toggle").forEach((button) => button.addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme !== "dark";
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("ratescope-theme", dark ? "dark" : "light");
  }));
  const menu = document.querySelector(".mobile-menu-toggle");
  const nav = document.querySelector("#primary-nav");
  menu?.addEventListener("click", () => {
    const open = !nav.classList.contains("open");
    nav.classList.toggle("open", open);
    menu.setAttribute("aria-expanded", String(open));
  });
  const animated = document.querySelectorAll("main > section, main > .panel, main > .visual-grid, main > .explanation-grid");
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) {
    animated.forEach((element) => element.classList.add("reveal-visible"));
  } else {
    animated.forEach((element) => element.classList.add("reveal-ready"));
    const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("reveal-visible");
      observer.unobserve(entry.target);
    }), { threshold: 0.08, rootMargin: "0px 0px -5%" });
    animated.forEach((element) => observer.observe(element));
  }
})();
