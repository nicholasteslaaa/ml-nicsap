import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import random

# -----------------------------
# Data structures
# -----------------------------
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Shape:
    def __init__(self, points, color):
        self.points = points
        self.color = color

# -----------------------------
# Main App
# -----------------------------
class CanvasMaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Canvas Mask Export (YOLO)")

        self.canvas = tk.Canvas(root, bg="white", cursor="cross")
        self.canvas.pack()

        # State
        self.image = None
        self.tk_image = None
        self.shapes = []
        self.points = []
        self.drawing_mode = False
        self.selected_index = None
        self.yolo_text = []

        # UI
        self.build_controls()

        # Bindings
        self.canvas.bind("<Button-1>", self.on_click)

    # -----------------------------
    # UI
    # -----------------------------
    def build_controls(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)

        tk.Button(frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Draw", command=self.start_drawing).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Finish", command=self.finish_drawing).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Delete", command=self.delete_selected).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Export YOLO", command=self.export_yolo).pack(side=tk.LEFT, padx=3)

    # -----------------------------
    # Image loading
    # -----------------------------
    def load_image(self):
        path = filedialog.askopenfilename()
        if not path:
            return

        self.image = Image.open(path)

        # scale max width
        max_width = 800
        if self.image.width > max_width:
            scale = max_width / self.image.width
            self.image = self.image.resize(
                (int(self.image.width * scale), int(self.image.height * scale))
            )

        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.config(width=self.image.width, height=self.image.height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        self.shapes.clear()
        self.points.clear()
        self.yolo_text.clear()
        self.selected_index = None

    # -----------------------------
    # Drawing logic
    # -----------------------------
    def start_drawing(self):
        self.drawing_mode = True
        self.points.clear()
        self.selected_index = None

    def finish_drawing(self):
        if not self.drawing_mode:
            return

        if len(self.points) < 3:
            messagebox.showerror("Error", "Need at least 3 points")
            return

        color = f"#{random.randint(0, 0xFFFFFF):06x}"
        shape = Shape(self.points.copy(), color)
        self.shapes.append(shape)

        self.create_yolo_entry(shape)

        self.points.clear()
        self.drawing_mode = False
        self.redraw()

    # -----------------------------
    # Mouse click
    # -----------------------------
    def on_click(self, event):
        if not self.image:
            return

        x, y = event.x, event.y

        if self.drawing_mode:
            self.points.append(Point(x, y))
            self.redraw()
            return

        # selection mode
        self.selected_index = self.find_shape(x, y)
        self.redraw()

    # -----------------------------
    # Helpers
    # -----------------------------
    def find_shape(self, x, y):
        for i, shape in enumerate(self.shapes):
            if self.point_in_polygon(x, y, shape.points):
                return i
        return None

    def point_in_polygon(self, x, y, points):
        inside = False
        j = len(points) - 1
        for i in range(len(points)):
            xi, yi = points[i].x, points[i].y
            xj, yj = points[j].x, points[j].y
            intersect = ((yi > y) != (yj > y)) and \
                        (x < (xj - xi) * (y - yi) / (yj - yi + 1e-6) + xi)
            if intersect:
                inside = not inside
            j = i
        return inside

    # -----------------------------
    # Drawing canvas
    # -----------------------------
    def redraw(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        for idx, shape in enumerate(self.shapes):
            pts = []
            for p in shape.points:
                pts.extend([p.x, p.y])

            self.canvas.create_polygon(
                pts,
                fill=shape.color,
                outline="blue",
                width=3 if idx == self.selected_index else 2
            )

            for p in shape.points:
                self.canvas.create_oval(p.x-3, p.y-3, p.x+3, p.y+3, fill="red")

        if self.drawing_mode:
            for p in self.points:
                self.canvas.create_oval(p.x-3, p.y-3, p.x+3, p.y+3, fill="red")

    # -----------------------------
    # YOLO export
    # -----------------------------
    def create_yolo_entry(self, shape):
        w = self.image.width
        h = self.image.height
        cls = 0

        coords = []
        for p in shape.points:
            coords.append(f"{p.x / w:.6f} {p.y / h:.6f}")

        self.yolo_text.append(f"{cls} " + " ".join(coords))

    def export_yolo(self):
        text = "\n".join(self.yolo_text)
        messagebox.showinfo("YOLO Output", text)

    # -----------------------------
    # Delete
    # -----------------------------
    def delete_selected(self):
        if self.selected_index is None:
            messagebox.showwarning("Warning", "Select a shape first")
            return

        self.shapes.pop(self.selected_index)
        self.yolo_text.pop(self.selected_index)
        self.selected_index = None
        self.redraw()

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = CanvasMaskApp(root)
    root.mainloop()
