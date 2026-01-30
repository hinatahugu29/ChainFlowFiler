# Quick Start Guide

This guide introduces the basic operational concepts and key bindings of Chain Flow Filer.
While it can be operated with a mouse, its true value is unlocked when using keyboard shortcuts.

## Screen Layout

The screen is divided into three main areas:

1.  **Sidebar (Left)**: Access to Standard folders, Favorites, and Drives.
2.  **Flow Area (Center-Right)**: The main area for file operations. Hierarchies flow from left to right.
3.  **Address Bar (Top)**: Displays the current path and allows direct input.

## Basic Workflow

1.  **Navigate**: Use arrow keys `Up` / `Down` to select files, `Enter` or `Right` to enter folders.
2.  **Go Back**: Use `Backspace` or `Q` key to return to the parent folder.
3.  **Preview**: Select a file and press `Space` to show a preview.
4.  **Switch Pane**: Just move the mouse cursor to another pane to instantly switch the active operation target (Hover Auto-Focus).

## Cheat Sheet (Key Bindings)

### Navigation
| Key | Action | Description |
| :--- | :--- | :--- |
| `Space` | Quick Look | Preview file content |
| `Q` / `Backspace` | Go Up | Go to parent directory |
| `Ctrl + B` | Toggle Sidebar | Show/Hide the sidebar |

### File Operations
| Key | Action | Description |
| :--- | :--- | :--- |
| `Ctrl + C` | Copy | Copy selected items (works seamlessly on hover) |
| `Ctrl + X` | Cut | Cut selected items |
| `Ctrl + V` | Paste | Paste clipboard content into current folder |
| `F2` | Rename | Rename item |
| `Del` | Delete | Delete item |
| `Alt + Click` | Mark (Bucket) | Add item to "Collection Bucket" (see below) |

### Layout & View
| Key | Action | Description |
| :--- | :--- | :--- |
| `V` | Vertical Split | Add a new vertical lane for parallel workflows |
| `Shift + W` | Close View | Close only the currently active view (split pane) |
| `C` | Compact Mode | Simplify tree view to show more information |
| `Ctrl + T` | New Tab | Open a new tab |
| `Ctrl + W` | Close Tab | Close the current tab |
| `Shift + Scroll` | Resize Lane | [Sidebar] Adjust section height |

## Unique Concepts

### Collection Bucket
Useful for moving or copying files scattered across multiple folders at once.

1.  `Alt + Click` on a file to highlight it in red.
    *   The mark persists even if you navigate to other folders.
2.  Add more files from other folders using `Alt + Click`.
3.  Finally, drag *any* file to move/copy all marked files together.
4.  `Alt + C` clears all marks.

### Hover Auto-Focus
Enables high-speed operation without clicking.
Simply placing the mouse cursor over a pane (list) makes it active and ready to accept commands like `Ctrl+C`.
There is no need to click to shift focus explicitly.
