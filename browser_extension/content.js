let isExtensionEnabled = true;

chrome.storage.local.get(['enabled'], (result) => {
    if (result.enabled !== undefined) {
        isExtensionEnabled = result.enabled;
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "toggle") {
        isExtensionEnabled = request.enabled;
        if (!isExtensionEnabled) {
            document.querySelectorAll('.vdm-container').forEach(c => c.style.display = 'none');
        }
    }
});

function injectButton(videoElement) {
    if (videoElement.dataset.vdmInjected) return;
    videoElement.dataset.vdmInjected = "true";
    
    let container = document.createElement("div");
    container.classList.add("vdm-container");
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

        if (!isExtensionEnabled) {
            container.style.display = 'none';
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
        
        dlBtn.innerText = "Sending to VDM...";
        dlBtn.style.backgroundColor = "#ffc107";
        dlBtn.style.color = "black";
        
        fetch('http://127.0.0.1:6800/download', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                url: window.location.href, 
                type: 'video_page' 
            })
        }).then(res => {
            dlBtn.innerText = "Sent to VDM!";
            dlBtn.style.backgroundColor = "#28a745";
            dlBtn.style.color = "white";
            setTimeout(() => { 
                dlBtn.innerText = "📥 Download Video"; 
                dlBtn.style.backgroundColor = "#007bff";
            }, 2000);
        }).catch(err => {
            dlBtn.innerText = "App Not Running!";
            dlBtn.style.backgroundColor = "#dc3545";
            dlBtn.style.color = "white";
            setTimeout(() => { 
                dlBtn.innerText = "📥 Download Video"; 
                dlBtn.style.backgroundColor = "#007bff";
            }, 2000);
        });
    };
    
    document.body.appendChild(container);
    
    window.addEventListener('scroll', updatePos);
    window.addEventListener('resize', updatePos);
    
    setTimeout(updatePos, 500);
    setInterval(updatePos, 2000); 
}

const observer = new MutationObserver((mutations) => {
    let videos = document.querySelectorAll('video');
    videos.forEach(injectButton);
});

observer.observe(document.body, { childList: true, subtree: true });
document.querySelectorAll('video').forEach(injectButton);
