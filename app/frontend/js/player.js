/**
 * Just Another Wine App — camera player wrapper.
 * Uses hls.js where needed, native HLS on Safari, falls back to a
 * periodic snapshot refresh loop if the stream is unavailable.
 */

const Player = (() => {
  function attachHls(videoEl, hlsUrl) {
    if (videoEl.canPlayType("application/vnd.apple.mpegurl")) {
      videoEl.src = hlsUrl;
      videoEl.play().catch(() => {});
      return { type: "native" };
    }
    if (window.Hls && window.Hls.isSupported()) {
      const hls = new window.Hls();
      hls.loadSource(hlsUrl);
      hls.attachMedia(videoEl);
      hls.on(window.Hls.Events.MANIFEST_PARSED, () => videoEl.play().catch(() => {}));
      return { type: "hlsjs", instance: hls };
    }
    return { type: "unsupported" };
  }

  function startSnapshotLoop(imgEl, snapshotUrl, intervalMs = 5000) {
    function refresh() {
      imgEl.src = `${snapshotUrl}?t=${Date.now()}`;
    }
    refresh();
    return setInterval(refresh, intervalMs);
  }

  async function loadCamera(cameraId, videoEl, imgEl, statusEl) {
    try {
      const stream = await API.get(`/api/cameras/${cameraId}/stream`);
      if (stream.type === "hls") {
        videoEl.style.display = "block";
        imgEl.style.display = "none";
        attachHls(videoEl, `${API.base}${stream.url}`);
        if (statusEl) statusEl.textContent = "Live";
      } else if (stream.type === "snapshot") {
        videoEl.style.display = "none";
        imgEl.style.display = "block";
        startSnapshotLoop(imgEl, `${API.base}${stream.url}`);
        if (statusEl) statusEl.textContent = "Snapshot mode";
      } else {
        if (statusEl) statusEl.textContent = "Stream unavailable";
      }
    } catch (e) {
      videoEl.style.display = "none";
      imgEl.style.display = "block";
      imgEl.src = `${API.base}/api/cameras/${cameraId}/snapshot`;
      if (statusEl) statusEl.textContent = "Offline — showing last snapshot";
    }
  }

  return { attachHls, startSnapshotLoop, loadCamera };
})();
