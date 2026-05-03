import os
import threading
from PIL import Image, ImageOps
import tkinter as tk
from tkinter import filedialog, messagebox

# Drag & Drop
from tkinterdnd2 import DND_FILES, TkinterDnD

# System Tray
import pystray
from pystray import MenuItem as item
from PIL import Image as PILImage

SUPPORTED_FORMATS = (".png", ".jpg", ".jpeg", ".bmp")

# ========================
# CORE CONVERTER
# ========================
def convert_to_ico(input_path):
    try:
        if not input_path.lower().endswith(SUPPORTED_FORMATS):
            return f"Skipped (unsupported): {os.path.basename(input_path)}"

        img = Image.open(input_path)

        # Fix: Crop to a perfect square from the center instead of squashing
        size = min(img.size)
        img = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS)

        base = os.path.splitext(input_path)[0]
        output = base + ".ico"

        img.save(output, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        return f"✔ Converted: {os.path.basename(output)}"

    except Exception as e:
        return f"✖ Error: {os.path.basename(input_path)} -> {str(e)}"


# ========================
# MAIN APP
# ========================
class ICOApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ICO Converter Pro")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.files = []
        self.tray_icon = None

        self.setup_ui()
        
        # Intercept the window close button (X) to minimize to tray instead
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

    def setup_ui(self):
        # Header
        self.label = tk.Label(self.root, text="Drag & Drop Images Here", font=("Arial", 14, "bold"))
        self.label.pack(pady=(15, 5))

        # Drop Target
        self.drop_area = tk.Label(self.root, text="Drop Files Here\n(.png, .jpg, .bmp)", 
                                  bg="#2c3e50", fg="white", width=50, height=5, font=("Arial", 10))
        self.drop_area.pack(pady=10)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind("<<Drop>>", self.handle_drop)

        # Buttons
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(pady=10)

        tk.Button(self.btn_frame, text="Browse Files", command=self.browse, width=12).grid(row=0, column=0, padx=10)
        tk.Button(self.btn_frame, text="Convert All", command=self.convert_all, width=12, bg="#27ae60", fg="white").grid(row=0, column=1, padx=10)
        tk.Button(self.btn_frame, text="Clear List", command=self.clear_files, width=12).grid(row=0, column=2, padx=10)

        # Log Output
        self.log = tk.Text(self.root, height=10, width=55, bg="#f4f6f7", font=("Consolas", 9))
        self.log.pack(pady=10)

    # ========================
    # FILE HANDLING
    # ========================
    def browse(self):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")]
        )
        self.add_files(files)

    def handle_drop(self, event):
        # Clean up path formatting from tkinterdnd2
        files = self.root.tk.splitlist(event.data)
        self.add_files(files)

    def add_files(self, files):
        added_count = 0
        for f in files:
            if f not in self.files and f.lower().endswith(SUPPORTED_FORMATS):
                self.files.append(f)
                self.log.insert(tk.END, f"Added: {os.path.basename(f)}\n")
                added_count += 1
                
        if added_count > 0:
            self.log.see(tk.END)

    def clear_files(self):
        self.files.clear()
        self.log.delete(1.0, tk.END)
        self.log.insert(tk.END, "List cleared.\n")

    # ========================
    # CONVERSION
    # ========================
    def convert_all(self):
        if not self.files:
            messagebox.showwarning("No files", "Please add some images first.")
            return

        self.log.insert(tk.END, "\n--- Starting Conversion ---\n")
        self.root.update() # Force UI update before heavy processing

        for f in self.files:
            result = convert_to_ico(f)
            self.log.insert(tk.END, result + "\n")
            self.root.update() # Keep UI responsive during loop

        self.log.insert(tk.END, "--- Conversion Complete ---\n\n")
        self.log.see(tk.END)

    # ========================
    # TRAY SYSTEM
    # ========================
    def hide_to_tray(self):
        """Hides the main window and spawns the tray icon in a background thread."""
        self.root.withdraw()
        self.create_tray_icon()

    def show_window(self, icon, item):
        """Restores the window from the tray."""
        icon.stop()
        # Thread-safe way to tell Tkinter to show the window
        self.root.after(0, self.root.deiconify)

    def exit_app(self, icon, item):
        """Properly shuts down the tray icon and the Tkinter mainloop."""
        icon.stop()
        # Thread-safe way to tell Tkinter to destroy the main window
        self.root.after(0, self.root.destroy)

    def create_tray_icon(self):
        # Create a simple green square for the tray icon
        image = PILImage.new("RGB", (64, 64), (39, 174, 96))

        menu = (
            item("Open", self.show_window, default=True),
            item("Exit", self.exit_app),
        )

        self.tray_icon = pystray.Icon("ico_converter", image, "ICO Converter Pro", menu)
        
        # Run pystray in a daemon thread so it doesn't block Tkinter
        threading.Thread(target=self.tray_icon.run, daemon=True).start()


# ========================
# MAIN
# ========================
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ICOApp(root)
    root.mainloop()