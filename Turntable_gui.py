import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
import os
import subprocess

SCRIPT_FOLDER = os.path.join(os.path.dirname(__file__), "scripts")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Blender Batch Runner")
        self.geometry("500x650")

        # Folders
        self.input_folder = ctk.StringVar()
        self.output_folder = ctk.StringVar()

        ctk.CTkLabel(self, text="Input Folder:", font=("Arial", 14)).pack(pady=(10,0))
        ctk.CTkEntry(self, textvariable=self.input_folder, width=400).pack(pady=5)
        ctk.CTkButton(self, text="Browse", command=self.pick_input).pack(pady=(0,10))

        ctk.CTkLabel(self, text="Output Folder:", font=("Arial", 14)).pack(pady=(10,0))
        ctk.CTkEntry(self, textvariable=self.output_folder, width=400).pack(pady=5)
        ctk.CTkButton(self, text="Browse", command=self.pick_output).pack(pady=(0,20))

        # Material color
        self.mat_color_var = ctk.StringVar(value="0.0, 0.0, 1.0")  # default blue
        ctk.CTkButton(self, text="Pick Material Color", command=self.pick_color).pack(pady=5)
        ctk.CTkLabel(self, textvariable=self.mat_color_var).pack(pady=(0,10))

        # Camera height
        self.cam_height_var = ctk.DoubleVar(value=0.6)  # default 60%
        ctk.CTkLabel(self, text="Camera Height (% of Model)", font=("Arial", 14)).pack()
        cam_frame = ctk.CTkFrame(self)
        cam_frame.pack(pady=5)
        for pct in [0.2, 0.4, 0.6, 0.8]:
            btn = ctk.CTkButton(cam_frame, text=f"{int(pct*100)}%", 
                                command=lambda p=pct: self.cam_height_var.set(p))
            btn.pack(side="left", padx=5)

        # Script selection
        ctk.CTkLabel(self, text="Available Blender Scripts:", font=("Arial", 16, "bold")).pack(pady=10)
        self.script_frame = ctk.CTkScrollableFrame(self, width=420, height=250)
        self.script_frame.pack(pady=5)
        self.load_script_buttons()

        ctk.CTkButton(self, text="Refresh Script List", command=self.load_script_buttons).pack(pady=10)

    def pick_input(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)

    def pick_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def pick_color(self):
        color_code = colorchooser.askcolor(title="Choose Material Color")[0]
        if color_code:
            r, g, b = [x/255 for x in color_code]
            self.mat_color_var.set(f"{r:.2f}, {g:.2f}, {b:.2f}")

    def load_script_buttons(self):
        for widget in self.script_frame.winfo_children():
            widget.destroy()

        scripts = [f for f in os.listdir(SCRIPT_FOLDER) if f.lower().endswith(".py")]

        if not scripts:
            ctk.CTkLabel(self.script_frame, text="No scripts found in /scripts").pack(pady=20)
            return

        for script in scripts:
            ctk.CTkLabel(self.script_frame, text=script, font=("Arial", 14)).pack(pady=(5,2))
            ctk.CTkButton(self.script_frame, text="Run in Blender", 
                           command=lambda s=script: self.run_in_blender(s)).pack(pady=(0,5))

    def run_in_blender(self, script_name):
        input_dir = self.input_folder.get()
        output_dir = self.output_folder.get()

        if not input_dir or not output_dir:
            messagebox.showerror("Missing Folder", "Please select both Input and Output folders!")
            return

        script_path = os.path.join(SCRIPT_FOLDER, script_name)
        blender_exe = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
        if not os.path.exists(blender_exe):
            messagebox.showerror("Blender Not Found", f"Blender executable not found at: {blender_exe}")
            return

        # Parse RGB
        try:
            r, g, b = [float(x.strip()) for x in self.mat_color_var.get().split(",")]
        except Exception:
            messagebox.showerror("Invalid Color", "Material color is invalid!")
            return

        cam_height = self.cam_height_var.get()

        cmd = [
            blender_exe, "-b", "-P", script_path,
            input_dir, output_dir,
            str(r), str(g), str(b),
            str(cam_height)
        ]

        try:
            subprocess.run(cmd, check=True)
            messagebox.showinfo("Success", f"{script_name} completed in Blender!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Render Error", str(e))

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = App()
    app.mainloop()
