"use strict";
if (window.lucide) window.lucide.createIcons();
const filters = document.querySelector("#filters");
if (filters) {
  filters.querySelectorAll("select, input[type=checkbox]").forEach((select) => {
    select.addEventListener("change", () => filters.requestSubmit());
  });
  document.querySelectorAll("[data-filter-control]").forEach((button) => {
    button.addEventListener("click", (event) => {
      const control = filters.elements.namedItem(button.dataset.filterControl);
      if (!control) return;
      event.preventDefault();
      control.focus();
      try { if (control.showPicker) control.showPicker(); } catch (_) {}
    });
  });
}
const themeButton = document.querySelector("#theme");
function setTheme(dark) {
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  if (themeButton) themeButton.setAttribute("aria-pressed", String(dark));
}
let savedTheme;
try { savedTheme = localStorage.getItem("aipedia-theme"); } catch (_) {}
setTheme(savedTheme ? savedTheme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);
if (themeButton) themeButton.addEventListener("click", () => {
  const dark = document.documentElement.dataset.theme !== "dark";
  setTheme(dark);
  try { localStorage.setItem("aipedia-theme", dark ? "dark" : "light"); } catch (_) {}
});

const infiniteScroll = document.querySelector("#infinite-scroll");
const modelRows = document.querySelector("#model-rows");
if (infiniteScroll && modelRows && "IntersectionObserver" in window) {
  let loading = false;
  const retryLabel = document.documentElement.lang === "ru" ? "Повторить" : "Retry";
  const showRetry = () => {
    infiniteScroll.replaceChildren();
    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = retryLabel;
    retry.addEventListener("click", () => {
      infiniteScroll.replaceChildren();
      loadNext();
    });
    infiniteScroll.append(retry);
  };
  const loadNext = async () => {
    const nextUrl = infiniteScroll.dataset.nextUrl;
    if (!nextUrl || loading) return;
    loading = true;
    try {
      const response = await fetch(nextUrl, {headers: {"X-Requested-With": "AIpedia"}});
      if (!response.ok) throw new Error("Catalog page failed to load");
      const wrapper = document.createElement("tbody");
      wrapper.innerHTML = await response.text();
      const newRows = [...wrapper.children];
      modelRows.append(...newRows);
      const shown = document.querySelector("#shown-count");
      if (shown) shown.textContent = String(modelRows.querySelectorAll(".model-name").length);
      infiniteScroll.dataset.nextUrl = response.headers.get("X-Aipedia-Next") || "";
      if (window.lucide) window.lucide.createIcons();
    } catch (_) {
      showRetry();
    } finally {
      loading = false;
    }
  };
  new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) loadNext();
  }, {rootMargin: "600px 0px"}).observe(infiniteScroll);
}

const adSlot = document.querySelector(".ad-slot");
const consent = document.querySelector("#ad-consent");
if (adSlot && consent) {
  const consentKey = "aipedia-ad-consent";
  const loadAds = () => {
    if (document.querySelector("script[data-aipedia-ads]")) return;
    const script = document.createElement("script");
    script.async = true;
    script.dataset.aipediaAds = "true";
    script.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";
    script.onload = () => { if (window.adsbygoogle) window.adsbygoogle.push({}); };
    document.head.append(script);
  };
  let choice;
  try { choice = localStorage.getItem(consentKey); } catch (_) {}
  if (choice === "granted") {
    consent.hidden = true;
    loadAds();
  }
  consent.querySelectorAll("[data-consent]").forEach((button) => {
    button.addEventListener("click", () => {
      const granted = button.dataset.consent === "grant";
      try { localStorage.setItem(consentKey, granted ? "granted" : "denied"); } catch (_) {}
      consent.hidden = true;
      if (granted) loadAds();
    });
  });
}
