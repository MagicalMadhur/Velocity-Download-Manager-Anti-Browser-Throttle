# Privacy Policy for Velocity Download Manager & Extension

**Last Updated:** October 2026

Velocity Download Manager and its companion browser extension ("Velocity Download Manager Integration") are built with a strict **privacy-first** approach. We believe your download history, browsing activity, and personal files belong only to you.

---

### 1. Zero Data Collection
- **No Personal Information:** We do not collect names, email addresses, phone numbers, IP addresses, or device identifiers.
- **No Browsing History:** We do not track, log, or transmit any web pages you visit.
- **No Download Logging:** Your download links, file names, file sizes, and saved locations remain strictly on your local machine.

---

### 2. Local-Only Communication
The companion browser extension communicates solely with your local computer:
- Requests are dispatched only to `http://127.0.0.1:6800` (localhost loopback).
- No data is ever sent to external cloud servers, third-party analytics, or remote tracking services.

---

### 3. Permissions Explanation
- **Downloads (`downloads`):** Used strictly to intercept download requests in the browser and transfer them to the local Velocity desktop application for multi-threaded speed acceleration.
- **Cookies (`cookies`):** Used solely to transfer active session cookies for the requested download URL to the local Velocity desktop client so authenticated/private downloads do not fail with HTTP 403 errors. Cookies are processed locally in-memory and are never stored or transmitted externally.
- **Storage (`storage`):** Used only to save your local UI preferences (such as enabling or disabling download interception).
- **Host Permissions (`<all_urls>` & `127.0.0.1`):** Required to inject the video download button above HTML5 video players on supported media sites, and to communicate with the local desktop client.

---

### 4. Third-Party Services
Velocity does not embed third-party analytics, advertisements, tracking SDKs, or data brokers.

---

### 5. Open Source Transparency
Velocity is open-source. You can inspect the entire source code at:
[https://github.com/MagicalMadhur/Velocity-Download-Manager-Anti-Browser-Throttle](https://github.com/MagicalMadhur/Velocity-Download-Manager-Anti-Browser-Throttle)

---

### 6. Contact & Inquiries
For any privacy-related questions or bug reports, open an issue on our GitHub repository:
[https://github.com/MagicalMadhur/Velocity-Download-Manager-Anti-Browser-Throttle/issues](https://github.com/MagicalMadhur/Velocity-Download-Manager-Anti-Browser-Throttle/issues)
