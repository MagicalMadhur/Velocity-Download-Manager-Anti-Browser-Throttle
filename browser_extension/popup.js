document.addEventListener("DOMContentLoaded", () => {
  const toggleIntercept = document.getElementById("toggleIntercept");
  const toggleVideo = document.getElementById("toggleVideo");
  const interceptDesc = document.getElementById("interceptDesc");
  const statusBadge = document.getElementById("statusBadge");
  const statusText = document.getElementById("statusText");

  // Load current settings
  chrome.storage.local.get({
    interceptDownloads: true,
    showVideoButtons: true
  }, (items) => {
    toggleIntercept.checked = items.interceptDownloads;
    toggleVideo.checked = items.showVideoButtons;
    updateInterceptText(items.interceptDownloads);
  });

  // Toggle Intercept Downloads
  toggleIntercept.addEventListener("change", () => {
    const enabled = toggleIntercept.checked;
    chrome.storage.local.set({ interceptDownloads: enabled }, () => {
      updateInterceptText(enabled);
    });
  });

  // Toggle Video Buttons
  toggleVideo.addEventListener("change", () => {
    const enabled = toggleVideo.checked;
    chrome.storage.local.set({ showVideoButtons: enabled });
  });

  function updateInterceptText(enabled) {
    if (enabled) {
      interceptDesc.textContent = "Forward browser downloads to Velocity";
      interceptDesc.style.color = "#8e95a5";
    } else {
      interceptDesc.textContent = "Off • Downloads handled natively by browser";
      interceptDesc.style.color = "#f87171";
    }
  }

  // Ping Velocity local server to check if running
  fetch("http://127.0.0.1:6800/download", { method: "OPTIONS" })
    .then(() => {
      statusBadge.className = "status-badge";
      statusText.textContent = "App Running";
    })
    .catch(() => {
      statusBadge.className = "status-badge offline";
      statusText.textContent = "App Offline";
    });
});
