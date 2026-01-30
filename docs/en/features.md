# Feature Details

Detailed explanation of Chain Flow Filer's unique features.

## 1. Navigation Sidebar (v12.0)

The sidebar is divided into three sections:

*   **STANDARD**: System standard folders like Desktop, Documents, Downloads.
*   **FAVORITES**: User-registered favorite folders.
*   **DRIVES**: List of connected drives.

### Resizing and Layout
You can drag the boundaries (splitters) of each section to adjust them.
Fine-tuning with the mouse wheel is also supported:
*   **Shift + Wheel**: Change section height.

When a section is collapsed, the empty space at the bottom is automatically adjusted (Spacer logic) to maintain a neat, top-aligned layout.

## 2. Quick Look

The preview feature, invoked with the `Space` key, offers more than just viewing.

*   **Code Preview**: Syntax highlighting for source codes like Python, JS, Markdown, AHK.
*   **Image Preview**: Supports common image formats.
*   **Copy Content**: Click the button at the top right of the preview window to copy the "content" displayed.
    *   For text files, it copies the full text.
    *   For image files, it copies the image data itself to the clipboard (paste directly into Slack, Photoshop, etc.).

## 3. PDF Conversion

In environments with MS Office (Word, Excel) or LibreOffice installed, you can right-click document files to **Convert to PDF**.
Combined with the marking feature, you can batch convert multiple documents at once.

## 4. Extended Context Menu

The right-click menu includes convenient features not found in standard Explorer.

*   **Create Shortcut**: Create a shortcut in the current folder.
*   **Copy Path Special**:
    *   `Copy Unix Path`: Copy with backslashes replaced by slashes (useful for coding).
    *   `Copy as "Path"`: Copy enclosed in double quotes.

## 5. Frictionless Operations

Refined operation feel in v12.0.

*   **Click-less**: Just hovering acts as recognition of the operation target.
*   **Active View Indicator**: A blue border appears on the left edge of the currently controllable list.
*   **Shift+W (Unstack)**: When the hierarchy gets too deep, use this to close only the rightmost (or bottom) view to organize.
