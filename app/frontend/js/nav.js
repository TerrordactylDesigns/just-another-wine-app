/**
 * Just Another Wine App — shared sidebar navigation.
 * Injects the same sidebar markup on every page and marks the active link.
 */

function renderSidebar(activePage) {
  const links = [
    { section: "Overview", items: [{ href: "index.html", label: "Dashboard", page: "index" }] },
    {
      section: "Wines",
      items: [
        { href: "inventory.html", label: "Inventory", page: "inventory" },
        { href: "ready.html", label: "Ready to Drink", page: "ready" },
        { href: "aging.html", label: "Currently Aging", page: "aging" },
        { href: "wishlist.html", label: "Wishlist", page: "wishlist" },
      ],
    },
    {
      section: "Monitoring",
      items: [
        { href: "sensors.html", label: "Sensors", page: "sensors" },
        { href: "cameras.html", label: "Cameras", page: "cameras" },
        {
          href: "alerts.html",
          label: "Alerts",
          page: "alerts",
          badges: true,
        },
      ],
    },
  ];

  const html = `
    <div class="sidebar-brand">
      <svg class="glyph" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M8 2h8v4a4 4 0 0 1-1 2.5V14a4 4 0 0 0 1 2.5V22H8v-5.5A4 4 0 0 0 9 14V8.5A4 4 0 0 1 8 6V2z"/>
      </svg>
      Just Another Wine App
    </div>
    ${links
      .map(
        (section) => `
      <div class="nav-section">
        <div class="nav-label">${section.section}</div>
        ${section.items
          .map(
            (item) => `
          <a href="${item.href}" class="nav-link ${item.page === activePage ? "active" : ""}">
            <span>${item.label}</span>
            ${
              item.badges
                ? `<span><span class="nav-badge critical" id="nav-badge-critical" style="display:none;"></span>
                   <span class="nav-badge warning" id="nav-badge-warning" style="display:none;margin-left:4px;"></span></span>`
                : ""
            }
          </a>`
          )
          .join("")}
      </div>`
      )
      .join("")}
  `;

  document.getElementById("sidebar").innerHTML = html;
}
