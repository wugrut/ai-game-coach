"""
Interactive screen region selector for AI Game Coach.
Lets the user click-and-drag to define the capture area.
"""

import tkinter as tk
from typing import Optional, Tuple, Callable


class RegionSelector:
    """
    Full-screen transparent overlay for selecting a screen capture region.
    Click and drag to define the capture rectangle.
    Press Escape to cancel.
    """

    def __init__(self, on_selected: Optional[Callable] = None):
        """
        Args:
            on_selected: Callback with (left, top, right, bottom) when selection is made.
        """
        self._on_selected = on_selected
        self._result: Optional[Tuple[int, int, int, int]] = None

        # Drag state
        self._start_x = 0
        self._start_y = 0
        self._rect_id = None
        self._coords_id = None

    def show(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Show the region selector overlay (blocking).
        Returns (left, top, right, bottom) or None if cancelled.
        """
        self._root = tk.Tk()
        self._root.title("Select Capture Region")
        self._root.attributes("-fullscreen", True)
        self._root.attributes("-alpha", 0.3)
        self._root.attributes("-topmost", True)
        self._root.configure(bg="black")

        # Create a canvas covering the entire screen
        self._canvas = tk.Canvas(
            self._root,
            bg="black",
            highlightthickness=0,
            cursor="crosshair",
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Instructions label
        self._canvas.create_text(
            self._root.winfo_screenwidth() // 2,
            40,
            text="Click and drag to select the capture region  •  Press ESC to cancel",
            fill="#00d4ff",
            font=("Segoe UI", 16, "bold"),
        )

        # Bind events
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._root.bind("<Escape>", self._on_escape)

        self._root.mainloop()
        return self._result

    def _on_press(self, event):
        """Start the selection rectangle."""
        self._start_x = event.x
        self._start_y = event.y
        if self._rect_id:
            self._canvas.delete(self._rect_id)
        if self._coords_id:
            self._canvas.delete(self._coords_id)

    def _on_drag(self, event):
        """Update the selection rectangle as the user drags."""
        if self._rect_id:
            self._canvas.delete(self._rect_id)
        if self._coords_id:
            self._canvas.delete(self._coords_id)

        x1, y1 = self._start_x, self._start_y
        x2, y2 = event.x, event.y

        self._rect_id = self._canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#00d4ff",
            width=2,
            dash=(5, 3),
        )

        # Show dimensions
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        mid_x = (x1 + x2) // 2
        mid_y = (y1 + y2) // 2

        self._coords_id = self._canvas.create_text(
            mid_x, mid_y,
            text=f"{w} × {h}",
            fill="#00ff88",
            font=("Segoe UI", 14, "bold"),
        )

    def _on_release(self, event):
        """Finalize the selection."""
        x1 = min(self._start_x, event.x)
        y1 = min(self._start_y, event.y)
        x2 = max(self._start_x, event.x)
        y2 = max(self._start_y, event.y)

        # Minimum selection size (10×10 pixels)
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            return

        self._result = (x1, y1, x2, y2)
        self._root.destroy()

        if self._on_selected:
            self._on_selected(self._result)

    def _on_escape(self, event):
        """Cancel the selection."""
        self._result = None
        self._root.destroy()
