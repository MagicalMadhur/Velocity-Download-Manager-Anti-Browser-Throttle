let videoButtonsEnabled = true;

chrome.storage.local.get({ showVideoButtons: true }, (data) => {
    videoButtonsEnabled = data.showVideoButtons;
    if (videoButtonsEnabled) {
        document.querySelectorAll('video').forEach(injectButton);
    }
});

chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && changes.showVideoButtons !== undefined) {
        videoButtonsEnabled = changes.showVideoButtons.newValue;
        if (!videoButtonsEnabled) {
            document.querySelectorAll('.vdm-btn-container').forEach(el => el.remove());
            document.querySelectorAll('video').forEach(v => delete v.dataset.vdmInjected);
        } else {
            document.querySelectorAll('video').forEach(injectButton);
        }
    }
});

function injectButton(videoElement) {
    if (!videoButtonsEnabled) return;
    if (videoElement.dataset.vdmInjected) return;
    videoElement.dataset.vdmInjected = "true";
    
    let container = document.createElement("div");
    container.className = "vdm-btn-container";
    container.style.position = "absolute";
    container.style.zIndex = "999999";
    container.style.display = "flex";
    container.style.gap = "1px";
    container.style.opacity = "0.7";
    container.style.transition = "opacity 0.2s";
    
    let dlBtn = document.createElement("div");
    dlBtn.innerText = "📥 Download Video";
    dlBtn.style.backgroundColor = "#007bff";
    dlBtn.style.color = "white";
    dlBtn.style.padding = "6px 12px";
    dlBtn.style.borderTopLeftRadius = "4px";
    dlBtn.style.borderBottomLeftRadius = "4px";
    dlBtn.style.cursor = "pointer";
    dlBtn.style.fontFamily = "sans-serif";
    dlBtn.style.fontSize = "12px";
    dlBtn.style.fontWeight = "bold";
    dlBtn.style.boxShadow = "0 2px 5px rgba(0,0,0,0.3)";
    
    let closeBtn = document.createElement("div");
    closeBtn.innerText = "✖";
    closeBtn.style.backgroundColor = "#444";
    closeBtn.style.color = "white";
    closeBtn.style.padding = "6px 8px";
    closeBtn.style.borderTopRightRadius = "4px";
    closeBtn.style.borderBottomRightRadius = "4px";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.fontFamily = "sans-serif";
    closeBtn.style.fontSize = "12px";
    closeBtn.style.boxShadow = "0 2px 5px rgba(0,0,0,0.3)";
    
    container.appendChild(dlBtn);
    container.appendChild(closeBtn);
    
    let isClosed = false;
    
    function updatePos() {
        if (isClosed) return;
        
        if (!document.body.contains(videoElement)) {
            container.remove();
            return;
        }
        
        let rect = videoElement.getBoundingClientRect();
        
        // Ignore tiny videos (thumbnails, previews, ads)
        if (rect.width < 300 || rect.height < 150) {
            container.style.display = 'none';
            return;
        }
        
        container.style.display = 'flex';
        container.style.top = (rect.top + window.scrollY + 10) + "px";
        container.style.left = (rect.right + window.scrollX - 160) + "px";
    }
    
    container.onmouseover = () => container.style.opacity = "1";
    container.onmouseout = () => container.style.opacity = "0.7";
    
    closeBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        isClosed = true;
        container.remove();
    };
    
    dlBtn.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        dlBtn.innerText = "Connecting to Velocity...";
        dlBtn.style.backgroundColor = "#ffc107";
        dlBtn.style.color = "black";
        
        chrome.runtime.sendMessage({
            action: "download_video",
            url: window.location.href,
            title: document.title
        }, (response) => {
            if (chrome.runtime.lastError || !response || !response.success) {
                dlBtn.innerText = "App Not Running!";
                dlBtn.style.backgroundColor = "#dc3545";
                dlBtn.style.color = "white";
                setTimeout(() => { 
                    dlBtn.innerText = "📥 Download Video"; 
                    dlBtn.style.backgroundColor = "#007bff";
                }, 2500);
            } else {
                dlBtn.innerText = "Sent to Velocity!";
                dlBtn.style.backgroundColor = "#28a745";
                dlBtn.style.color = "white";
                setTimeout(() => { 
                    dlBtn.innerText = "📥 Download Video"; 
                    dlBtn.style.backgroundColor = "#007bff";
                }, 2000);
            }
        });
    };
    
    document.body.appendChild(container);
    
    window.addEventListener('scroll', updatePos);
    window.addEventListener('resize', updatePos);
    
    setTimeout(updatePos, 500);
    setInterval(updatePos, 2000); 
}

const observer = new MutationObserver((mutations) => {
    if (!videoButtonsEnabled) return;
    let videos = document.querySelectorAll('video');
    videos.forEach(injectButton);
});

observer.observe(document.body, { childList: true, subtree: true });
