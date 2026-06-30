/**
 * Just Another Wine App — alert banner & nav badge polling.
 * Included on every page. Polls active alerts every 60s.
 */

const Alerts = (() => {
  let dismissed = new Set();

  async function poll() {
    try {
      const [critical, warning] = await Promise.all([
        API.get("/api/alerts?severity=critical&resolved=false"),
        API.get("/api/alerts?severity=warning&resolved=false"),
      ]);
      renderBanner(critical, warning);
      renderNavBadges(critical.length, warning.length);
    } catch (e) {
      // Silently skip — don't disrupt the page over a polling failure
      console.warn("Alert poll failed", e);
    }
  }

  function renderBanner(critical, warning) {
    const container = document.getElementById("global-alert-banner");
    if (!container) return;

    const visible = [
      ...critical.map((a) => ({ ...a, sev: "critical" })),
      ...warning.map((a) => ({ ...a, sev: "warning" })),
    ].filter((a) => !dismissed.has(a.id));

    if (visible.length === 0) {
      container.style.display = "none";
      container.innerHTML = "";
      return;
    }

    container.style.display = "flex";
    container.innerHTML = visible
      .map(
        (a) => `
        <div class="banner ${a.sev}" data-id="${a.id}">
          <span><strong>${escapeHtml(a.title)}</strong>${a.message ? " — " + escapeHtml(a.message) : ""}</span>
          <button class="dismiss" onclick="Alerts.dismiss(${a.id})" aria-label="Dismiss">&times;</button>
        </div>`
      )
      .join("");
  }

  function renderNavBadges(criticalCount, warningCount) {
    const critBadge = document.getElementById("nav-badge-critical");
    const warnBadge = document.getElementById("nav-badge-warning");
    if (critBadge) {
      critBadge.textContent = criticalCount;
      critBadge.style.display = criticalCount > 0 ? "inline-block" : "none";
    }
    if (warnBadge) {
      warnBadge.textContent = warningCount;
      warnBadge.style.display = warningCount > 0 ? "inline-block" : "none";
    }
  }

  function dismiss(id) {
    dismissed.add(id);
    poll();
  }

  function init() {
    poll();
    setInterval(poll, 60000);
  }

  return { init, dismiss, poll };
})();

document.addEventListener("DOMContentLoaded", Alerts.init);
