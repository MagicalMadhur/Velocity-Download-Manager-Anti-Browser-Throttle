function forwardDownloadToApp(item, suggest, cookies) {
    const targetUrl = item.finalUrl || item.url;
    const filename = item.filename || "";
    const referrer = item.referrer || "";

    const headers = {};
    if (cookies && cookies.length > 0) {
        headers["Cookie"] = cookies.map(c => `${c.name}=${c.value}`).join('; ');
    }
    if (referrer) {
        headers["Referer"] = referrer;
    }
    if (navigator && navigator.userAgent) {
        headers["User-Agent"] = navigator.userAgent;
    }

    fetch("http://127.0.0.1:6800/download", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            url: targetUrl,
            original_url: item.url,
            filename: filename,
            headers: headers
        })
    })
    .then(response => {
        if (response.ok) {
            console.log("Download forwarded to Velocity Download Manager!");
            chrome.downloads.cancel(item.id);
        } else {
            console.warn("Velocity server rejected download. Continuing in browser.");
            suggest();
        }
    })
    .catch(error => {
        // App is not open or unreachable: let browser download normally
        suggest();
    });
}

function updateBadge(enabled) {
    if (enabled) {
        chrome.action.setBadgeText({ text: "" });
    } else {
        chrome.action.setBadgeText({ text: "OFF" });
        chrome.action.setBadgeBackgroundColor({ color: "#e74c3c" });
    }
}

// Initialize badge state on extension load
chrome.storage.local.get({ interceptDownloads: true }, (data) => {
    updateBadge(data.interceptDownloads);
});

// Watch for setting changes to update badge immediately
chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && changes.interceptDownloads) {
        updateBadge(changes.interceptDownloads.newValue);
    }
});

chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
    // Check if download interception is enabled by user
    chrome.storage.local.get({ interceptDownloads: true }, (settings) => {
        if (!settings.interceptDownloads) {
            // User disabled interception: let browser download normally without any interruption
            suggest();
            return;
        }

        // Interception is ON: Forward to Velocity with cookies
        if (chrome.cookies && chrome.cookies.getAll) {
            try {
                chrome.cookies.getAll({ url: item.url }, (cookies) => {
                    forwardDownloadToApp(item, suggest, cookies || []);
                });
            } catch (e) {
                forwardDownloadToApp(item, suggest, []);
            }
        } else {
            forwardDownloadToApp(item, suggest, []);
        }
    });
    
    return true; // Indicates asynchronous response
});

// Listen for messages from content scripts (e.g. video page download button)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "download_video") {
        fetch("http://127.0.0.1:6800/download", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: request.url,
                title: request.title || "",
                type: "video_page"
            })
        })
        .then(response => {
            if (response.ok) {
                sendResponse({ success: true });
            } else {
                sendResponse({ success: false, error: "Status " + response.status });
            }
        })
        .catch(err => {
            sendResponse({ success: false, error: err.toString() });
        });
        return true; // Indicates asynchronous response
    }
});
