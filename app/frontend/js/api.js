/**
 * Just Another Wine App — shared API helper.
 * Detects Home Assistant ingress base path automatically so the app
 * works both standalone and embedded behind HA's ingress proxy.
 */

const API = (() => {
  // When served through HA ingress, the URL looks like:
  // /api/hassio_ingress/{token}/...
  // We detect this prefix from the current location so fetch() calls
  // stay correctly scoped regardless of how the app is being accessed.
  function basePath() {
    const path = window.location.pathname;
    const ingressMatch = path.match(/^(\/api\/hassio_ingress\/[^/]+)/);
    return ingressMatch ? ingressMatch[1] : "";
  }

  const BASE = basePath();

  async function request(method, url, body, isForm = false) {
    const opts = { method, headers: {} };
    if (body && !isForm) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    } else if (body && isForm) {
      opts.body = body; // FormData sets its own content-type
    }

    const res = await fetch(`${BASE}${url}`, opts);
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = await res.json();
        detail = data.detail || detail;
      } catch (_) {}
      throw new Error(detail);
    }
    if (res.status === 204) return null;
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) return res.json();
    return res;
  }

  return {
    base: BASE,
    get: (url) => request("GET", url),
    post: (url, body) => request("POST", url, body),
    postForm: (url, formData) => request("POST", url, formData, true),
    put: (url, body) => request("PUT", url, body),
    del: (url) => request("DELETE", url),
    imageUrl: (imgId, thumbnail = false) =>
      `${BASE}/api/images/${imgId}${thumbnail ? "?thumbnail=true" : ""}`,
  };
})();

/* ---------------------------------------------------------------------
   External wine link domain detection
   --------------------------------------------------------------------- */

const EXTERNAL_LINK_LABELS = [
  { match: "vivino.com", label: "View on Vivino" },
  { match: "wine-searcher.com", label: "View on Wine-Searcher" },
  { match: "cellartracker.com", label: "View on CellarTracker" },
  { match: "totalwine.com", label: "View on Total Wine" },
  { match: "wine.com", label: "View on Wine.com" },
];

function externalLinkLabel(url) {
  if (!url) return null;
  for (const entry of EXTERNAL_LINK_LABELS) {
    if (url.includes(entry.match)) return entry.label;
  }
  return "View External Page";
}

/* ---------------------------------------------------------------------
   Small shared helpers
   --------------------------------------------------------------------- */

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmtDate(dateStr) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function wineStatus(wine) {
  const year = new Date().getFullYear();
  if (wine.drink_from && year < wine.drink_from) return "aging";
  if (wine.drink_until && year > wine.drink_until) return "past_peak";
  if (wine.drink_from || wine.drink_until) return "ready";
  return "unknown";
}

function statusBadge(status) {
  const labels = { ready: "Ready", aging: "Aging", past_peak: "Past Peak", unknown: "" };
  if (!labels[status]) return "";
  return `<span class="badge ${status}">${labels[status]}</span>`;
}
