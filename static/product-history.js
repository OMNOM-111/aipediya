"use strict";
(() => {
  const dialog = document.getElementById("ph-dialog");
  if (!dialog) return;
  const scrim = document.getElementById("ph-scrim");
  const close = document.getElementById("ph-close");
  const body = document.getElementById("ph-dialog-body");
  const title = document.getElementById("ph-dialog-title");
  const meta = document.getElementById("ph-dialog-meta");
  let opener = null;
  const hide = () => {
    if (dialog.hidden) return;
    dialog.hidden = true;
    scrim.hidden = true;
    document.body.classList.remove("ph-dialog-open");
    body.replaceChildren();
    if (opener?.isConnected) opener.focus();
    opener = null;
  };
  document.querySelectorAll("[data-history-open]").forEach((card) => card.addEventListener("click", () => {
    const template = document.getElementById(`ph-detail-${card.dataset.historyOpen}`);
    if (!template) return;
    opener = card;
    title.textContent = card.querySelector("strong")?.textContent || "";
    meta.textContent = card.closest(".ph-milestone")?.querySelector("time")?.textContent || "";
    body.replaceChildren(template.content.cloneNode(true));
    dialog.hidden = false;
    scrim.hidden = false;
    document.body.classList.add("ph-dialog-open");
    if (window.lucide) window.lucide.createIcons({ nodes: [dialog] });
    close.focus();
  }));
  close.addEventListener("click", hide);
  scrim.addEventListener("click", hide);
  document.addEventListener("keydown", (event) => {
    if (dialog.hidden) return;
    if (event.key === "Escape") { event.preventDefault(); hide(); return; }
    if (event.key !== "Tab") return;
    const focusable = [...dialog.querySelectorAll("a[href],button,summary,[tabindex]:not([tabindex='-1'])")].filter((node) => node.getClientRects().length);
    if (!focusable.length) { event.preventDefault(); dialog.focus(); return; }
    const first = focusable[0], last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
})();
