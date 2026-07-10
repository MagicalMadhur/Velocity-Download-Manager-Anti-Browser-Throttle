chrome.downloads.onDeterminingFilename.addListener((item, suggest) => {
    // Intercept the download
    const downloadUrl = item.url;
    const filename = item.filename;

    // Send to our local Python app
    fetch("http://127.0.0.1:6800/download", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            url: downloadUrl,
            filename: filename
        })
    })
    .then(response => {
        if (response.ok) {
            console.log("Sent to VIBE Download Manager!");
            // Cancel the browser's built-in download
            chrome.downloads.cancel(item.id);
        } else {
            console.error("VIBE Download Manager server responded with an error.");
            suggest(); // let the browser continue
        }
    })
    .catch(error => {
        console.error("VIBE Download Manager is not running.", error);
        // Let the browser handle the download if our app is closed
        suggest();
    });
    
    return true; // Indicates asynchronous response
});
