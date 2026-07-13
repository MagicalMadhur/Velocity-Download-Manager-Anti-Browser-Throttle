document.addEventListener('DOMContentLoaded', () => {
    const enableToggle = document.getElementById('enableToggle');

    // Load initial state
    chrome.storage.local.get(['enabled'], (result) => {
        // default to true if undefined
        enableToggle.checked = result.enabled !== false; 
    });

    // Handle change
    enableToggle.addEventListener('change', (e) => {
        const isEnabled = e.target.checked;
        
        // Save to storage
        chrome.storage.local.set({ enabled: isEnabled });
        
        // Notify all tabs to update their state
        chrome.tabs.query({}, (tabs) => {
            for (let t of tabs) {
                chrome.tabs.sendMessage(t.id, { action: "toggle", enabled: isEnabled }).catch(() => {});
            }
        });
    });
});
