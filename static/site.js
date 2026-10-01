"use strict";

if (window.lucide) window.lucide.createIcons();

let catalogFreshness = null;
try { catalogFreshness = JSON.parse(document.getElementById("catalog-freshness-data")?.textContent || "null"); } catch (_) {}

function pluralRu(value, one, few, many) {
  if (value % 10 === 1 && value % 100 !== 11) return one;
  if ([2, 3, 4].includes(value % 10) && ![12, 13, 14].includes(value % 100)) return few;
  return many;
}
function relativeTimeLabel(stamp) {
  const then = Date.parse(stamp);
  if (!Number.isFinite(then)) return "";
  const minutes = Math.max(0, Math.floor((Date.now() - then) / 60000));
  const lang = document.documentElement.lang || "en";
  if (lang === "ru") {
    if (minutes < 1) return "только что";
    if (minutes < 60) return `${minutes} мин назад`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours < 24) return mins ? `${hours} ч ${mins} мин назад` : `${hours} ч назад`;
    const days = Math.floor(hours / 24);
    return `${days} ${pluralRu(days, "день", "дня", "дней")} назад`;
  }
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours < 24) return mins ? `${hours}h ${mins}m ago` : `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "1 day ago" : `${days} days ago`;
}
function localDateLabel(date) {
  const lang = document.documentElement.lang || "en";
  if (lang === "ru") {
    const months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
    return `${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
  }
  return new Intl.DateTimeFormat(lang, { day: "numeric", month: "short", year: "numeric" }).format(date);
}
function localTimeLabel(date) {
  const lang = document.documentElement.lang || "en";
  return new Intl.DateTimeFormat(lang, { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(date);
}
function updateFreshnessClock() {
  const now = new Date();
  document.querySelectorAll("[data-local-date]").forEach((item) => { item.textContent = localDateLabel(now); });
  document.querySelectorAll("[data-local-time]").forEach((item) => { item.textContent = localTimeLabel(now); });
  document.querySelectorAll("[data-update-local-time]").forEach((item) => {
    const value = item.getAttribute("datetime") || item.dataset.updatedAt || catalogFreshness?.updated_at_utc || "";
    const stamp = new Date(value);
    if (!Number.isNaN(stamp.getTime())) item.textContent = `${localDateLabel(stamp)}, ${localTimeLabel(stamp)}`;
  });
}
function badgeIsCurrent(releaseDate, approx, precision) {
  // NEW/UPD reflects the record's real recency, not when it entered AIpediya.
  if (!releaseDate || approx === true || approx === "true") return false;
  if (releaseDate.includes("T")) {
    const t = Date.parse(releaseDate);
    if (!Number.isFinite(t)) return false;
    const delta = Date.now() - t;
    return delta >= 0 && delta < 24 * 60 * 60 * 1000;
  }
  const p = String(precision || "").toLowerCase();
  if (p && p !== "day") return false;
  const parts = releaseDate.split("-");
  if (parts.length < 3) return false;
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const todayLocal = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  return releaseDate === todayLocal;
}
function updateBadgeRecency() {
  document.querySelectorAll(".catalog-update-badge").forEach((badge) => {
    badge.hidden = !badgeIsCurrent(badge.dataset.badgeReleaseDate, badge.dataset.badgeReleaseApprox === "true", badge.dataset.badgeReleasePrecision);
  });
  document.querySelectorAll(".freshness-entry").forEach((li) => {
    const action = li.querySelector(".freshness-action");
    // The popover is the immutable current-release snapshot: its NEW/UPD
    // labels describe this catalog update, independently of product dates.
    if (action) action.hidden = false;
  });
}
window.aipediaBadgeIsCurrent = badgeIsCurrent;
function updateRelativeTimes() {
  document.querySelectorAll("[data-relative-time]").forEach((item) => {
    item.textContent = relativeTimeLabel(item.dataset.updatedAt || "");
  });
}
updateFreshnessClock();
updateBadgeRecency();
updateRelativeTimes();
if (catalogFreshness) window.setInterval(() => { updateFreshnessClock(); updateBadgeRecency(); }, 1000);
if (catalogFreshness) window.setInterval(updateRelativeTimes, 60000);
window.aipediaUpdateBadgeRecency = updateBadgeRecency;

const freshnessShell = document.querySelector("[data-catalog-freshness]");
const freshnessButton = freshnessShell?.querySelector(".catalog-freshness");
function setFreshnessOpen(open) {
  if (!freshnessShell || !freshnessButton) return;
  freshnessShell.classList.toggle("is-open", open);
  freshnessButton.setAttribute("aria-expanded", String(open));
  document.body.classList.toggle("is-catalog-freshness-open", open);
  if (!open && document.activeElement === freshnessButton) freshnessButton.blur();
}
if (freshnessButton) {
  freshnessShell.addEventListener("pointerenter", (event) => {
    if (event.pointerType === "mouse") setFreshnessOpen(true);
  });
  freshnessShell.addEventListener("pointerleave", (event) => {
    if (event.pointerType === "mouse") setFreshnessOpen(false);
  });
  freshnessShell.addEventListener("focusin", () => setFreshnessOpen(true));
  freshnessShell.addEventListener("focusout", (event) => {
    if (!freshnessShell.contains(event.relatedTarget)) setFreshnessOpen(false);
  });
  freshnessButton.addEventListener("click", (event) => {
    event.stopPropagation();
    setFreshnessOpen(true);
  });
  document.addEventListener("click", (event) => {
    if (freshnessShell && !freshnessShell.contains(event.target)) setFreshnessOpen(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setFreshnessOpen(false);
  });
}

const filters = document.querySelector("#catalog-filters") || document.querySelector("#filters");
let filterSheetDirty = false;
if (filters) {
  // Some filters appear under two column headers (status). Keep every copy in
  // step so the submitted value is the one just chosen. Inside the Filter
  // sheet choices are collected and applied together (Apply or closing).
  const submitFilters = (event) => {
    const control = event && event.target;
    if (control && control.name && control.tagName === "SELECT") {
      document.querySelectorAll(`select[form='catalog-filters'][name='${CSS.escape(control.name)}']`).forEach((other) => {
        if (other !== control) other.value = control.value;
      });
    }
    if (control && control.closest && control.closest("dialog.sheet[open]")) {
      filterSheetDirty = true;
      return;
    }
    filters.requestSubmit();
  };
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

// Filter and Sort sheets (tablet / phone / narrow catalog). The Filter sheet
// shows the same controls as the column-header popovers: they are moved into
// the sheet while it is open and put back when it closes, so there is one set
// of form fields and the desktop header filters keep working.
const sheetRestore = [];
function fillFilterSheet(sheet) {
  const slot = sheet.querySelector("[data-filter-slot]");
  if (!slot) return;
  const seen = new Set();
  document.querySelectorAll(".model-table thead details.col-filter .filter-popover").forEach((popover) => {
    const heading = popover.closest("th")?.querySelector("a[data-sort]")?.textContent.trim() || "";
    const group = document.createElement("fieldset");
    group.className = "sheet-group";
    const legend = document.createElement("legend");
    legend.textContent = heading;
    group.append(legend);
    [...popover.children].forEach((node) => {
      const field = node.querySelector("select, input");
      const name = field ? field.name : "";
      if (name && seen.has(name)) return;
      if (name) seen.add(name);
      sheetRestore.push([node, popover, node.nextSibling]);
      group.append(node);
    });
    if (group.children.length > 1) slot.append(group);
  });
}
function emptyFilterSheet(sheet) {
  while (sheetRestore.length) {
    const [node, parent, next] = sheetRestore.pop();
    parent.insertBefore(node, next && next.parentNode === parent ? next : null);
  }
  const slot = sheet.querySelector("[data-filter-slot]");
  if (slot) slot.replaceChildren();
}
let sheetTrigger = null;
document.querySelectorAll("[data-sheet-open]").forEach((button) => {
  const sheet = document.querySelector(`dialog[data-sheet="${button.dataset.sheetOpen}"]`);
  if (!sheet || typeof sheet.showModal !== "function") {
    button.hidden = true;
    return;
  }
  button.addEventListener("click", () => {
    document.querySelectorAll("details.col-filter[open]").forEach((item) => { item.open = false; });
    sheetTrigger = button;
    if (sheet.dataset.sheet === "filters") {
      filterSheetDirty = false;
      fillFilterSheet(sheet);
    }
    sheet.showModal();
    const current = sheet.querySelector("[aria-current]");
    if (current) current.scrollIntoView({ block: "nearest" });
  });
});
document.querySelectorAll("dialog.sheet").forEach((sheet) => {
  // Typing in a text filter inside the sheet counts as a pending change too.
  sheet.addEventListener("input", (event) => {
    if (event.target.matches("input[form='catalog-filters']:not([type=checkbox])")) filterSheetDirty = true;
  });
  sheet.querySelectorAll("[data-sheet-close]").forEach((button) => {
    button.addEventListener("click", () => sheet.close());
  });
  // A tap on the dimmed backdrop (outside the sheet box) closes it.
  sheet.addEventListener("click", (event) => {
    if (event.target !== sheet) return;
    const box = sheet.getBoundingClientRect();
    const inside = event.clientX >= box.left && event.clientX <= box.right && event.clientY >= box.top && event.clientY <= box.bottom;
    if (!inside) sheet.close();
  });
  sheet.addEventListener("close", () => {
    if (sheet.dataset.sheet === "filters") {
      const apply = filterSheetDirty;
      filterSheetDirty = false;
      emptyFilterSheet(sheet);
      // Closing never throws away a choice: pending changes are applied.
      if (apply && filters) {
        filters.requestSubmit();
        return;
      }
    }
    if (sheetTrigger && typeof sheetTrigger.focus === "function") sheetTrigger.focus();
  });
});

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

// The panel changes the address without a reload, so the language menu is
// re-pointed at the page now shown (same rule as the server's switch_url:
// locale prefix + neutral path + query without lang/kind/partial).
const langLinks = [...document.querySelectorAll("a[data-set-lang]")];
function syncLanguageLinks() {
  if (!langLinks.length) return;
  const own = document.documentElement.lang || "en";
  const ownPrefix = own === "en" ? "" : `/${own.toLowerCase()}`;
  let neutral = location.pathname;
  if (ownPrefix && (neutral === ownPrefix || neutral.startsWith(`${ownPrefix}/`))) {
    neutral = neutral.slice(ownPrefix.length) || "/";
  }
  const params = new URLSearchParams(location.search);
  ["lang", "kind", "partial"].forEach((key) => params.delete(key));
  const query = params.toString();
  langLinks.forEach((link) => {
    const code = link.dataset.setLang;
    const prefix = code === "en" ? "" : `/${code.toLowerCase()}`;
    link.setAttribute("href", prefix + neutral + (query ? `?${query}` : ""));
  });
  // The remembered-language shortcut sits outside the menu and must follow
  // History API changes to the listing or open card as well.
  const offer = document.querySelector("a.lang-offer");
  if (offer) {
    const target = langLinks.find((link) => link.dataset.setLang === offer.hreflang);
    if (target) offer.setAttribute("href", target.getAttribute("href"));
  }
}

function refreshIcons() {
  if (window.lucide) window.lucide.createIcons();
}

// Phones scroll the page itself (no app shell). The detail view sits under
// the header there, so the header is brought into view while it is open and
// the list position is restored when it closes.
const APP_SHELL = "(min-width: 721px) and (min-height: 540px), (min-width: 1280px)";
let listScroll = null;

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
  const pageScrolls = !window.matchMedia(APP_SHELL).matches;
  if (open && pageScrolls && listScroll === null && window.scrollY > 0) {
    listScroll = window.scrollY;
    window.scrollTo(0, 0);
  } else if (!open && listScroll !== null) {
    const y = listScroll;
    listScroll = null;
    window.scrollTo(0, y);
  }
  syncHeaderHeight();
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

function panelUrlFromLink(link, href) {
  const url = new URL(href || link.href, location.origin);
  url.searchParams.set("partial", "panel");
  return url;
}

async function openPanelFromLink(link, push, href) {
  if (!panel) return;
  lastTrigger = link;
  const slug = link.dataset.slug;
  const requestId = ++panelRequest;
  setPanelOpen(true);
  highlightRow(slug);
  panel.setAttribute("aria-busy", "true");
  try {
    const response = await fetch(panelUrlFromLink(link, href).toString(), { headers: { "X-Requested-With": "AIpedia" } });
    if (!response.ok) throw new Error("panel");
    const html = await response.text();
    if (requestId !== panelRequest) return;
    panel.innerHTML = html;
    bindPanel(panel);
    const title = response.headers.get("X-Aipedia-Title");
    if (title) {
      try { document.title = decodeURIComponent(title); } catch (_) {}
    }
    if (push) {
      const listingUrl = history.state?.listingUrl ||
        (ENTITY_PATH.test(location.pathname) ? null : location.pathname + location.search);
      history.pushState({ panel: slug, listingUrl }, "", link.href);
      syncLanguageLinks();
    }
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
  const listingUrl = history.state?.listingUrl;
  const entity = location.pathname.match(ENTITY_PATH);
  if (listingUrl) {
    const listing = new URL(listingUrl, location.origin);
    if (listing.origin === location.origin) {
      closeUrl.pathname = listing.pathname;
      closeUrl.search = listing.search;
    }
  } else if (entity) {
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
  syncLanguageLinks();
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
  syncLanguageLinks();
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
    if (target.closest("dialog")) return;
    closePanel(true);
  });
  window.addEventListener("popstate", () => {
    syncLanguageLinks();
    const match = location.pathname.match(ENTITY_PATH);
    if (match) {
      const slug = match[3];
      const existing = document.querySelector(`a.model-name[data-slug="${CSS.escape(slug)}"]`);
      const link = existing || document.createElement("a");
      if (!existing) {
        link.href = location.href;
        link.dataset.slug = slug;
      }
      // Back/forward restores exactly the address in history (including ?tab=).
      openPanelFromLink(link, false, location.href);
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
    if (!nextUrl || loading) return false;
    loading = true;
    try {
      const response = await fetch(nextUrl, { headers: { "X-Requested-With": "AIpedia" } });
      if (!response.ok) throw new Error("Catalog page failed to load");
      // A reply for an older listing (the sort/filter changed meanwhile, or the
      // page came back from the history cache) must never add rows here.
      if (infiniteScroll.dataset.nextUrl !== nextUrl) return false;
      const wrapper = document.createElement("tbody");
      wrapper.innerHTML = await response.text();
      modelRows.append(...wrapper.children);
      const shown = document.querySelector("#shown-count");
      if (shown) shown.textContent = String(modelRows.querySelectorAll(".model-name").length);
      infiniteScroll.dataset.nextUrl = response.headers.get("X-Aipedia-Next") || "";
      if (window.lucide) window.lucide.createIcons();
      return true;
    } catch (_) {
      showRetry();
    } finally {
      loading = false;
    }
  };
  // The table scrolls inside its card when the catalog is an app shell
  // (tablet and desktop) and the page itself scrolls on phones. Watch both:
  // the viewport always (ancestor clipping is respected), the table scroller
  // for early prefetch only while it really scrolls. After each chunk the
  // sentinel is re-checked, so a chunk that leaves it visible loads on.
  const observers = [];
  const recheck = () => {
    observers.forEach((observer) => {
      observer.unobserve(infiniteScroll);
      observer.observe(infiniteScroll);
    });
  };
  const onIntersect = (entries, observer) => {
    const scroller = observer.root;
    if (scroller && scroller.scrollHeight <= scroller.clientHeight + 1) return;
    if (entries.some((entry) => entry.isIntersecting)) loadNext().then((loaded) => { if (loaded) recheck(); });
  };
  observers.push(new IntersectionObserver(onIntersect, { rootMargin: "240px 0px" }));
  if (tableScroll) observers.push(new IntersectionObserver(onIntersect, { root: tableScroll, rootMargin: "240px 0px" }));
  observers.forEach((observer) => observer.observe(infiniteScroll));
}

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  // An open Filter/Sort sheet handles Escape itself (native dialog cancel).
  if (document.querySelector("dialog.sheet[open]")) return;
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
