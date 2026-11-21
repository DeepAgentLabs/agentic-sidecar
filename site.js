// Agentic Sidecar product page.
// Everything else (nav, reveal on scroll, carousel, counters, copy buttons, simulation)
// comes from the shared DeepAgentLabs scripts. This file only runs the tabbed code example.

(() => {
  const box = document.querySelector("[data-sc-tabs]");
  if (!box) return;
  const tabs = [...box.querySelectorAll('[role="tab"]')];

  const select = (index, focus) => {
    const current = (index + tabs.length) % tabs.length;
    tabs.forEach((tab, i) => {
      const on = i === current;
      tab.setAttribute("aria-selected", String(on));
      tab.tabIndex = on ? 0 : -1;
      document.getElementById(tab.getAttribute("aria-controls")).hidden = !on;
    });
    if (focus) tabs[current].focus();
  };

  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(i));
    tab.addEventListener("keydown", (e) => {
      const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (e.key === "Home") { e.preventDefault(); select(0, true); }
      else if (e.key === "End") { e.preventDefault(); select(tabs.length - 1, true); }
      else if (step) { e.preventDefault(); select(i + step, true); }
    });
  });
})();
