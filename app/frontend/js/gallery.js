/**
 * Just Another Wine App — image gallery / lightbox for wine detail pages.
 */

const Gallery = (() => {
  function render(containerEl, images) {
    if (!images || images.length === 0) {
      containerEl.innerHTML = `
        <div class="wine-thumb-placeholder" style="width:100%;height:280px;border-radius:12px;">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#6b6475" stroke-width="1.5">
            <path d="M8 2h8v4a4 4 0 0 1-1 2.5V14a4 4 0 0 0 1 2.5V22H8v-5.5A4 4 0 0 0 9 14V8.5A4 4 0 0 1 8 6V2z"/>
          </svg>
        </div>`;
      return;
    }

    const primary = images.find((i) => i.is_primary) || images[0];
    const others = images.filter((i) => i.id !== primary.id);

    containerEl.innerHTML = `
      <img src="${API.imageUrl(primary.id)}" alt="${escapeHtml(primary.label || "Wine bottle")}"
           style="width:100%;border-radius:12px;cursor:pointer;max-height:420px;object-fit:cover;"
           onclick="Gallery.open(${primary.id})" id="gallery-primary-img" />
      ${
        others.length > 0
          ? `<div style="display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;">
              ${others
                .map(
                  (img) => `
                <img src="${API.imageUrl(img.id, true)}" alt="${escapeHtml(img.label || "")}"
                     style="width:64px;height:64px;border-radius:6px;object-fit:cover;cursor:pointer;border:1px solid var(--color-border);"
                     onclick="Gallery.setPrimaryView(${img.id})" />`
                )
                .join("")}
            </div>`
          : ""
      }
    `;
  }

  function setPrimaryView(imgId) {
    const el = document.getElementById("gallery-primary-img");
    if (el) el.src = API.imageUrl(imgId);
  }

  function open(imgId) {
    window.open(API.imageUrl(imgId), "_blank");
  }

  return { render, setPrimaryView, open };
})();
