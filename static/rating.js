"use strict";
(() => {
  const popover = document.getElementById("rating-popover");
  if (!popover || !popover.showPopover) return;
  let trigger = null, hideTimer = null, pinned = false, closing = false, ignoreFocusUntil = 0, dismissedButton = null;
  function close() {
    clearTimeout(hideTimer);
    closing = true;
    if (popover.matches(":popover-open")) {
      ignoreFocusUntil = performance.now() + 100;
      popover.hidePopover();
    }
    trigger?.setAttribute("aria-expanded", "false");
    trigger?.removeAttribute("aria-controls");
    trigger = null; pinned = false; closing = false;
  }
  function show(button) {
    if (closing || dismissedButton === button) return;
    clearTimeout(hideTimer);
    if (trigger !== button) {
      close(); trigger = button;
      const template = button.parentElement.querySelector("template[data-rating-tip]");
      if (!template) { trigger = null; return; }
      popover.replaceChildren(template.content.cloneNode(true));
    }
    trigger.setAttribute("aria-expanded", "true"); trigger.setAttribute("aria-controls", "rating-popover");
    if (!popover.matches(":popover-open")) popover.showPopover();
    const rect = trigger.getBoundingClientRect();
    popover.style.left = `${Math.max(12, Math.min(rect.left, innerWidth - popover.offsetWidth - 12))}px`;
    popover.style.top = `${Math.max(12, Math.min(rect.bottom + 7, innerHeight - popover.offsetHeight - 12))}px`;
  }
  document.addEventListener("pointerover", event => {
    if (event.pointerType === "touch") return;
    const button = event.target.closest("[data-rating-audit]"); if (button) show(button);
  });
  document.addEventListener("focusin", event => {
    const button = event.target.closest("[data-rating-audit]");
    if (button && !closing && performance.now() >= ignoreFocusUntil) show(button);
  });
  document.addEventListener("pointerout", event => {
    if (dismissedButton?.contains(event.target) && !dismissedButton.contains(event.relatedTarget)) dismissedButton = null;
    if (!pinned && (event.target.closest("[data-rating-audit]") || popover.contains(event.target))) {
      hideTimer = setTimeout(() => { if (!popover.matches(":hover") && !trigger?.matches(":hover, :focus-visible")) close(); }, 200);
    }
  });
  document.addEventListener("focusout", event => {
    if (event.target === dismissedButton) dismissedButton = null;
    if (!pinned && event.target === trigger && !popover.contains(event.relatedTarget)) close();
  });
  document.addEventListener("click", event => {
    const button = event.target.closest("[data-rating-audit]");
    if (button) {
      event.preventDefault(); event.stopPropagation();
      if (pinned && trigger === button) { dismissedButton = button; close(); }
      else { dismissedButton = null; show(button); pinned = true; }
    }
  });
  popover.addEventListener("pointerenter", () => clearTimeout(hideTimer));
  popover.addEventListener("click", event => event.stopPropagation());
  popover.addEventListener("toggle", () => { if (!popover.matches(":popover-open")) { trigger?.setAttribute("aria-expanded", "false"); pinned = false; } });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && popover.matches(":popover-open")) {
      event.preventDefault(); event.stopImmediatePropagation(); dismissedButton = trigger; close();
    }
  }, true);
  window.addEventListener("resize", close);
  document.addEventListener("scroll", event => { if (!popover.contains(event.target)) close(); }, true);
})();
