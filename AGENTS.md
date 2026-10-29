# Repository Rules & Delivery Guidelines

## Output & Distribution Delivery Rules
Whenever updates, bug fixes, or builds are produced for this project, always adhere to the following delivery structure:

1. **Extracted Browser Extension**:
   - Always deliver the unpacked / extracted version of the browser extension in the folder named `brave extension` (and alias `brave exteniion`).
   - This folder contains `manifest.json`, `background.js`, `content.js` ready to load unpacked into Brave / Chrome (`brave://extensions` -> "Load unpacked").

2. **Final Application**:
   - Always deliver the newly updated `Velocity.exe` (together with its `_internal` runtime dependencies and `Velocity_Setup.exe`) in the folder named `final app`.
   - The `final app` directory allows immediate execution of `Velocity.exe` directly on the machine without installation, as well as access to the installer wizard.
