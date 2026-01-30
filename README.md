
# Chain Flow Filer v12.0 (Alpha)

**Unleash Your Workflow.**  
Chain Flow Filer is a keyboard-centric, high-performance file manager designed for power users who demand efficiency.

---

## 🚀 What is New in v12.0?

v12.0 focuses on layout stability, sidebar enhancements, and smoother focus management.

### 1. Refined Navigation Sidebar
*   **3-Section Layout**: Sidebar is now organized into `STANDARD`, `FAVORITES`, and `DRIVES`.
*   **Flexible Resizing**: All sections are resizeable. Use `Shift + Scroll` to adjust heights effortlessly.

### 2. Frictionless Operations
*   **Hover-to-Act**: Just hover over a list, and `Ctrl+C` / `Ctrl+V` will target the item under your mouse.
*   **Auto-Stretch Columns**: The "Name" column now automatically stretches to fill the available space. Just resize the pane (Ctrl+Scroll) to see long filenames.

---

## 🚀 What is New in v11.1?

v11.1 brought intuitive control to the multi-view interface.

### 1. Hover Auto-Focus & View Unstacking
*   **Hover Focus**: Just move your mouse over a split view, and it instantly becomes active (blue highlight). No clicking required.
*   **Unstacking (`Shift+W`)**: Remove *only* the active view (the bottom-most one in a stack) instead of wiping out the whole pane. Precise control for complex layouts.
*   **Smart Navigation (`Q` Key)**: The "Go Up" command now correctly targets the *focused* view, not just the top one.

### 2. Unified Drag & Drop (Refined)
You can now drag **multiple items from different folders** at once!
*   **Selected Items**: Items selected in multiple panes.
*   **Marked Items**: Items marked with `Alt + Click` (Red Highlight).
*   **How to use**: Just drag any selected item, and Chain Flow Filer will bundle *everything* (Selection + Marks) into a single drag operation. Great for gathering assets from various locations.

### 2. Enhanced Quick Look
*   **AHK Support**: AutoHotkey scripts (`.ahk`) are now previewable as text.
*   **Copy Content Button**: 
    *   **Text/Code**: Preview and click "Copy Content" to grab the code instantly.
    *   **Images**: Preview an image and click "Copy Content" to copy the image data to your clipboard. Paste directly into Slack, Discord, or Photoshop.

### 3. Advanced Context Menu
Right-click on any file to access new tools:
*   **Create Shortcut**: Instantly create a `.lnk` shortcut in the current folder.
*   **Properties**: Open the native Windows file properties dialog.
*   **Copy Path Special**:
    *   `Copy Name` / `Copy Full Path` / `Copy as "Path"` / `Copy Unix Path (/)`.

### 4. Refined Aesthetics
*   **Deep Blue Scrollbars**: A new, sophisticated deep-blue theme (`#153b93`) for scrollbars, improving visibility without distraction.

---

## 🎮 Key Controls (Cheat Sheet)

| Key | Action |
| :--- | :--- |
| **Space** | **Quick Look** (Preview file content) |
| **Alt + Click**| **Mark Item** (Add to "Collection Bucket") |
| **Alt + C** | **Clear Marks** (Empty the bucket) |
| **Ctrl + Drag**| **Batch Drag** (Move/Copy all selected & marked items) |
| **Q / Backspace**| Go Up (Parent Directory) |
| **V** | New Vertical Lane |
| **C** | Compact Mode Toggle |
| **Ctrl+C / V** | Batch Copy / Paste |
| **Ctrl+B** | Toggle Sidebar |

---

## 🛠 Installation & Usage

This application is distributed as a **Portable App**.

1.  **Unzip**: Extract the provided `ChainFlowFiler_v10_new` archive.
2.  **Run**: Double-click `ChainFlowFiler_v10_new.exe` inside the folder.
3.  **Portable**: All settings (`session.json`, `favorites.json`) are saved within the same folder. You can carry it on a USB stick.

---

## 💡 Tips
*   **Mark & Drag**: Use `Alt+Click` to mark files in Folder A, go to Folder B and mark files there. Then drag *any* file to Folder C. All marked files from A and B will be copied/moved to C.
*   **Quick Copy**: Press `Space` on an image, then click the "Copy" button (or just see the preview). Paste it anywhere.

---

## 📜 Version History
*   **v12.0**: Sidebar Refactoring (3-Sections, Spacer Layout), Hover-Action Fix, PyInstaller Build.
*   **v11.1**: Hover Auto-Focus, View Unstacking (Shift+W), Q-Key Fix, New Icon.
*   **v10.0**: Batch Drag, AHK Preview, Image Copy, Shortcut Creation, New Scrollbar Theme.
*   **v9.2**: Sidebar Toggle, Scroll fixes.
*   **v9.0**: Mouse Wheel Resizing.
*   **v8.0**: Custom UI Styling.

---

## 6. ビルド情報
```powershell
py -m PyInstaller --clean --onefile --noconsole --noconfirm --name "ChainFlowFiler_v12" --icon="app_icon.ico" --add-data "app_icon.ico;." main.py
```
