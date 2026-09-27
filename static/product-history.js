"use strict";
(() => {
  function initProductHistory(root = document) {
    const dialog = root.querySelector("#ph-dialog");
    if (!dialog || dialog.dataset.initialized === "true") return;
    dialog.dataset.initialized = "true";
    const scrim = root.querySelector("#ph-scrim");
    const close = root.querySelector("#ph-close");
    const body = root.querySelector("#ph-dialog-body");
    const title = root.querySelector("#ph-dialog-title");
    const meta = root.querySelector("#ph-dialog-meta");
    let opener = null;
    const open = (trigger, heading, subheading, template) => {
      if (!template) return;
      opener = dialog.contains(trigger) && opener?.isConnected ? opener : trigger;
      title.textContent = heading;
      meta.textContent = subheading;
      body.replaceChildren(template.content.cloneNode(true));
      dialog.hidden = false;
      scrim.hidden = false;
      document.body.classList.add("ph-dialog-open");
      const page = root.querySelector("#ph-page-content");
      if (page) page.inert = true;
      if (window.lucide) window.lucide.createIcons({ nodes: [dialog] });
      close.focus();
    };
    const hide = () => {
      if (dialog.hidden) return;
      dialog.hidden = true;
      scrim.hidden = true;
      document.body.classList.remove("ph-dialog-open");
      const page = root.querySelector("#ph-page-content");
      if (page) page.inert = false;
      body.replaceChildren();
      if (opener?.isConnected) opener.focus();
      opener = null;
    };
    root.querySelectorAll(".ph-release-card[data-history-open]").forEach((card) => {
      const showDetails = () => {
        const template = root.querySelector(`#ph-detail-${CSS.escape(card.dataset.historyOpen)}`);
        const cardTitle = card.querySelector("h3")?.textContent || "";
        const cardDate = card.closest(".ph-milestone")?.querySelector("time")?.textContent || "";
        open(card, cardTitle, cardDate, template);
      };
      card.addEventListener("click", (event) => {
        if (event.target.closest("a,button")) return;
        showDetails();
      });
      card.addEventListener("keydown", (event) => {
        if (event.target !== card || (event.key !== "Enter" && event.key !== " ")) return;
        event.preventDefault();
        showDetails();
      });
    });
    root.querySelectorAll("[data-history-source]").forEach((link) => {
      link.addEventListener("click", (event) => {
        const slug = link.dataset.historySource;
        const template = root.querySelector(`template[data-history-source-template="${CSS.escape(slug)}"]`);
        if (!template) return;
        event.preventDefault();
        open(link, link.dataset.historySourceTitle || link.textContent.trim(),
          document.documentElement.lang === "ru" ? "Технические подтверждения" : "Technical evidence", template);
      });
    });
    close.addEventListener("click", hide);
    scrim.addEventListener("click", hide);
    dialog.addEventListener("keydown", (event) => {
      if (dialog.hidden) return;
      if (event.key === "Escape") { event.preventDefault(); hide(); return; }
      if (event.key !== "Tab") return;
      const focusable = [...dialog.querySelectorAll("a[href],button,summary,[tabindex]:not([tabindex='-1'])")]
        .filter((node) => node.getClientRects().length);
      if (!focusable.length) { event.preventDefault(); dialog.focus(); return; }
      const first = focusable[0], last = focusable.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
  }
  window.initAipediaProductHistory = initProductHistory;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => initProductHistory(document), { once: true });
  } else {
    initProductHistory(document);
  }
})();
