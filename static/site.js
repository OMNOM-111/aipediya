"use strict";

if (window.lucide) window.lucide.createIcons();

const filters = document.querySelector("#catalog-filters") || document.querySelector("#filters");
if (filters) {
  const submitFilters = () => filters.requestSubmit();
  document.querySelectorAll("select[form='catalog-filters'], #catalog-filters select, input[type=checkbox][form='catalog-filters']").forEach((control) => {
    control.addEventListener("change", submitFilters);
  });
  document.querySelectorAll("[data-filter-control]").forEach((button) => {
    button.addEventListener("click", (event) => {
      const control = filters.elements.namedItem(button.dataset.filterControl);
      if (!control) return;
      event.preventDefault();
      const popover = control.closest("details.col-filter");
      if (popover) popover.open = true;
      control.focus();
      try { if (control.showPicker) control.showPicker(); } catch (_) {}
    });
  });
}

document.querySelectorAll("details.col-filter").forEach((item) => {
  item.addEventListener("toggle", () => {
    if (item.open) {
      document.querySelectorAll("details.col-filter[open]").forEach((other) => {
        if (other !== item) other.open = false;
      });
    }
    placeFilterPopover(item);
  });
});

function placeFilterPopover(details) {
  const pop = details.querySelector(".filter-popover");
  const summary = details.querySelector("summary");
  if (!pop || !summary) return;
  if (!details.open) {
    pop.style.position = "";
    pop.style.top = "";
    pop.style.left = "";
    pop.style.right = "";
    pop.style.zIndex = "";
    return;
  }
  const box = summary.getBoundingClientRect();
  const rtl = document.documentElement.dir === "rtl";
  pop.style.position = "fixed";
  pop.style.top = `${Math.round(box.bottom + 4)}px`;
  pop.style.zIndex = "50";
  if (rtl) {
    pop.style.left = `${Math.max(8, Math.round(box.left))}px`;
    pop.style.right = "auto";
  } else {
    pop.style.right = `${Math.max(8, Math.round(window.innerWidth - box.right))}px`;
    pop.style.left = "auto";
  }
}

const themeButton = document.querySelector("#theme");
function setTheme(dark) {
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  if (themeButton) themeButton.setAttribute("aria-pressed", String(dark));
}
let savedTheme;
try { savedTheme = localStorage.getItem("aipedia-theme"); } catch (_) {}
setTheme(savedTheme ? savedTheme === "dark" : true);
if (themeButton) themeButton.addEventListener("click", () => {
  const dark = document.documentElement.dataset.theme !== "dark";
  setTheme(dark);
  try { localStorage.setItem("aipedia-theme", dark ? "dark" : "light"); } catch (_) {}
});

const search = document.querySelector("#catalog-search");
document.addEventListener("keydown", (event) => {
  const typing = event.target instanceof HTMLElement && event.target.closest("input, textarea, select, [contenteditable=true]");
  if (event.key === "/" && !event.ctrlKey && !event.metaKey && !event.altKey && !typing && search) {
    event.preventDefault();
    search.focus();
  }
});

const panel = document.querySelector("#model-panel");
const catalogPage = document.querySelector(".catalog-page");

function syncHeaderHeight() {
  const header = document.querySelector(".site-header");
  if (header) document.documentElement.style.setProperty("--aip-header-h", `${header.offsetHeight}px`);
}
syncHeaderHeight();
window.addEventListener("resize", syncHeaderHeight);

// Optional locale prefix (/ru, /zh-hans, /pt-br), entity kind, slug.
const ENTITY_PATH = /^(\/[a-z]{2,3}(?:-[a-z]{2,4})?)?\/(models|tools)\/([^/]+)$/;

let panelRequest = 0;
let lastTrigger = null;
let I18N = {};
try { I18N = JSON.parse(document.getElementById("aipedia-i18n").textContent); } catch (_) {}
const copiedText = I18N.copied || "Link copied";
const copyManual = I18N.copyManual || "Copy the link manually";
const panelError = I18N.panelError || "Could not open the card. Refresh the page.";

function refreshIcons() {
  if (window.lucide) window.lucide.createIcons();
}

function setPanelOpen(open) {
  if (!panel || !catalogPage) return;
  catalogPage.classList.toggle("is-panel-open", open);
  panel.classList.toggle("is-open", open);
  panel.hidden = !open;
  if (open) {
    panel.removeAttribute("hidden");
  } else {
    panel.setAttribute("hidden", "hidden");
  }
}

function highlightRow(slug) {
  document.querySelectorAll(".model-table tbody tr.is-selected").forEach((row) => row.classList.remove("is-selected"));
  if (!slug) return;
  const row = document.querySelector(`.model-table tbody tr[data-slug="${CSS.escape(slug)}"]`);
  if (row) row.classList.add("is-selected");
}

function bindPanel(root) {
  const close = root.querySelector("[data-close-panel]");
  if (close) close.addEventListener("click", onCloseClick);
  const share = root.querySelector("[data-share]");
  if (share) share.addEventListener("click", onShare);
  const save = root.querySelector("[data-save]");
  if (save) {
    save.addEventListener("click", onSaveHint);
    save.addEventListener("focus", showSaveHint);
    save.addEventListener("mouseenter", showSaveHint);
    save.addEventListener("mouseleave", () => {
      if (document.activeElement !== save) hideSaveHint();
    });
    save.addEventListener("blur", hideSaveHint);
  }
  root.querySelectorAll("[data-tab]").forEach((tab) => {
    tab.addEventListener("click", onTabClick);
  });
  refreshIcons();
}

function panelUrlFromLink(link) {
  const url = new URL(link.href, location.origin);
  url.searchParams.set("partial", "panel");
  return url;
}

async function openPanelFromLink(link, push) {
  if (!panel) return;
  lastTrigger = link;
  const slug = link.dataset.slug;
  const requestId = ++panelRequest;
  setPanelOpen(true);
  highlightRow(slug);
  panel.setAttribute("aria-busy", "true");
  try {
    const response = await fetch(panelUrlFromLink(link).toString(), { headers: { "X-Requested-With": "AIpedia" } });
    if (!response.ok) throw new Error("panel");
    const html = await response.text();
    if (requestId !== panelRequest) return;
    panel.innerHTML = html;
    bindPanel(panel);
    const title = response.headers.get("X-Aipedia-Title");
    if (title) {
      try { document.title = decodeURIComponent(title); } catch (_) {}
    }
    if (push) history.pushState({ panel: slug }, "", link.href);
  } catch (_) {
    if (requestId !== panelRequest) return;
    panel.innerHTML = `<p class="panel-error">${panelError}</p>`;
  } finally {
    if (requestId === panelRequest) panel.removeAttribute("aria-busy");
  }
}

function closePanel(push) {
  panelRequest += 1;
  setPanelOpen(false);
  highlightRow("");
  if (panel) panel.innerHTML = "";
  const closeUrl = new URL(location.href);
  const entity = location.pathname.match(ENTITY_PATH);
  if (entity) {
    // /ru/tools/x -> /ru/tools/ ; /models/x -> / (locale prefix kept)
    closeUrl.pathname = (entity[1] || "") + (entity[2] === "tools" ? "/tools/" : "/");
    closeUrl.searchParams.delete("tab");
    closeUrl.searchParams.delete("model");
    closeUrl.searchParams.delete("tool");
  } else {
    closeUrl.searchParams.delete("model");
    closeUrl.searchParams.delete("tab");
  }
  const listingTitle = document.querySelector("#main[data-listing-title]");
  if (listingTitle && listingTitle.dataset.listingTitle) document.title = listingTitle.dataset.listingTitle;
  if (push !== false) history.pushState({ panel: null }, "", closeUrl.pathname + closeUrl.search);
  if (lastTrigger && typeof lastTrigger.focus === "function") lastTrigger.focus();
}

function onCloseClick(event) {
  event.preventDefault();
  closePanel(true);
}

function onTabClick(event) {
  const tab = event.currentTarget;
  if (!tab.dataset.tab) return;
  event.preventDefault();
  const name = tab.dataset.tab;
  panel.querySelectorAll("[data-tab]").forEach((item) => {
    const active = item.dataset.tab === name;
    item.classList.toggle("is-active", active);
    item.setAttribute("aria-selected", String(active));
  });
  panel.querySelectorAll(".tab-panel").forEach((section) => {
    section.hidden = section.id !== `tab-${name}`;
  });
  const url = new URL(location.href);
  if (name === "overview") url.searchParams.delete("tab");
  else url.searchParams.set("tab", name);
  history.replaceState(history.state, "", url.pathname + url.search);
}

async function onShare() {
  const fallback = panel.querySelector("#share-fallback");
  const input = panel.querySelector("#share-url");
  const status = panel.querySelector("#share-status");
  const url = location.href;
  if (input) input.value = url;
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(url);
      if (fallback) fallback.hidden = true;
      if (status) {
        status.hidden = false;
        status.textContent = copiedText;
      }
      return;
    } catch (_) {}
  }
  if (status) {
    status.hidden = false;
    status.textContent = copyManual;
  }
  if (fallback && input) {
    fallback.hidden = false;
    input.focus();
    input.select();
  }
}

function showSaveHint() {
  const hint = panel && panel.querySelector("#save-hint");
  if (hint) hint.hidden = false;
}

function onSaveHint(event) {
  event.preventDefault();
  showSaveHint();
}

function hideSaveHint() {
  const hint = panel.querySelector("#save-hint");
  if (hint) hint.hidden = true;
}

if (panel) {
  bindPanel(panel);
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a.model-name");
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    openPanelFromLink(link, true);
  });
  // Clicking anywhere on a catalogue row opens its panel, as if the name link
  // were clicked. Interactive elements (links, buttons, form controls, filter
  // popovers) keep their own behaviour, and an active text selection never
  // triggers a navigation.
  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const row = target.closest("tr[data-slug]");
    if (!row) return;
    if (target.closest("a, button, input, select, textarea, label, details, summary, [role='button']")) return;
    const selection = window.getSelection();
    if (selection && !selection.isCollapsed && selection.toString().trim()) return;
    const link = row.querySelector("a.model-name");
    if (!link) return;
    event.preventDefault();
    openPanelFromLink(link, true);
  });
  // Close the open panel on a click outside it, but never on the header
  // (language/search/theme), a row link that opens another entry, or a column
  // filter popover — clicks inside the panel keep it open.
  document.addEventListener("click", (event) => {
    if (!panel.classList.contains("is-open")) return;
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (panel.contains(target)) return;
    if (target.closest("tr[data-slug]")) return;
    if (target.closest("a.model-name")) return;
    if (target.closest(".site-header")) return;
    if (target.closest("details.col-filter")) return;
    closePanel(true);
  });
  window.addEventListener("popstate", () => {
    const match = location.pathname.match(ENTITY_PATH);
    if (match) {
      const slug = match[3];
      const existing = document.querySelector(`a.model-name[data-slug="${CSS.escape(slug)}"]`);
      const link = existing || document.createElement("a");
      if (!existing) {
        link.href = location.href;
        link.dataset.slug = slug;
      }
      openPanelFromLink(link, false);
    } else {
      closePanel(false);
    }
  });
}

const infiniteScroll = document.querySelector("#infinite-scroll");
const modelRows = document.querySelector("#model-rows");
const tableScroll = document.querySelector(".catalog-card > .table-scroll");
if (infiniteScroll && modelRows && "IntersectionObserver" in window) {
  let loading = false;
  const retryLabel = I18N.retry || "Retry";
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
      const response = await fetch(nextUrl, { headers: { "X-Requested-With": "AIpedia" } });
      if (!response.ok) throw new Error("Catalog page failed to load");
      const wrapper = document.createElement("tbody");
      wrapper.innerHTML = await response.text();
      modelRows.append(...wrapper.children);
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
  const observerOptions = { rootMargin: "240px 0px" };
  if (tableScroll) observerOptions.root = tableScroll;
  new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) loadNext();
  }, observerOptions).observe(infiniteScroll);
}

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const openFilter = document.querySelector("details.col-filter[open]");
  if (openFilter) {
    openFilter.open = false;
    event.preventDefault();
    return;
  }
  const fallback = panel && panel.querySelector("#share-fallback");
  const shareStatus = panel && panel.querySelector("#share-status");
  if ((fallback && !fallback.hidden) || (shareStatus && !shareStatus.hidden)) {
    if (fallback) fallback.hidden = true;
    if (shareStatus) shareStatus.hidden = true;
    event.preventDefault();
    return;
  }
  const hint = panel && panel.querySelector("#save-hint");
  if (hint && !hint.hidden) {
    hint.hidden = true;
    event.preventDefault();
    return;
  }
  if (panel && panel.classList.contains("is-open")) {
    event.preventDefault();
    closePanel(true);
  }
});

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

// Language memory is client-side only: the address always decides the page
// language, and no server response is personalised by it. A manual choice in
// the switcher is remembered, and on a page in another language reached from outside the
// site a quiet link offers the remembered language (never a redirect).
const LANG_COOKIE = "aipedia_lang";
document.querySelectorAll("a[data-set-lang]").forEach((link) => {
  link.addEventListener("click", () => {
    document.cookie = `${LANG_COOKIE}=${encodeURIComponent(link.dataset.setLang)}; path=/; max-age=31536000; samesite=lax${location.protocol === "https:" ? "; secure" : ""}`;
  });
});
(function offerSavedLanguage() {
  const saved = (document.cookie.match(/(?:^|; )aipedia_lang=([^;]+)/) || [])[1];
  const pageLang = document.documentElement.lang;
  if (!saved || decodeURIComponent(saved) === pageLang) return;
  let external = true;
  try { external = !document.referrer || new URL(document.referrer).origin !== location.origin; } catch (_) {}
  if (!external) return;
  const target = document.querySelector(`a[data-set-lang="${CSS.escape(decodeURIComponent(saved))}"]`);
  const controls = document.querySelector(".header-controls");
  if (!target || !controls) return;
  const offer = document.createElement("a");
  offer.className = "lang-offer";
  offer.href = target.getAttribute("href");
  offer.lang = target.lang;
  offer.hreflang = target.hreflang;
  offer.textContent = `${target.textContent} →`;
  controls.prepend(offer);
})();
