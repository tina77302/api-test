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
})();
