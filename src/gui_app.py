"""
Desktop GUI for the Plant Disease Detection System, built with Tkinter as
described in the paper:

  "To make the system usable for farmers and agricultural workers, a
   graphical user interface (GUI) was developed. The interface allows users
   to upload plant images and receive instant disease diagnoses... built
   using Python's Tkinter library."

Usage:
    python src/gui_app.py
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

try:
    from src import config
    from src.predict import PlantDiseasePredictor
except ImportError:
    import config
    from predict import PlantDiseasePredictor


class PlantDiseaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Plant Disease Detection System")
        self.root.geometry("520x680")
        self.root.configure(bg="#f2f7f2")

        self.predictor = None
        self.current_image_path = None

        self._build_widgets()
        self._load_model_safely()

    # ------------------------------------------------------------------ UI
    def _build_widgets(self):
        title = tk.Label(
            self.root, text="🌿 Plant Disease Detection",
            font=("Helvetica", 18, "bold"), bg="#f2f7f2", fg="#2e5339"
        )
        title.pack(pady=(15, 5))

        subtitle = tk.Label(
            self.root, text="Upload a leaf image to detect disease and get an organic remedy",
            font=("Helvetica", 10), bg="#f2f7f2", fg="#555555"
        )
        subtitle.pack(pady=(0, 10))

        self.open_button = tk.Button(
            self.root, text="Open Image", command=self.open_image,
            font=("Helvetica", 12), bg="#4c8c5a", fg="white",
            activebackground="#3d7048", padx=15, pady=6, relief="flat"
        )
        self.open_button.pack(pady=5)

        self.image_panel = tk.Label(self.root, bg="#e0e8e0", width=300, height=300)
        self.image_panel.pack(pady=10)

        self.result_label = tk.Label(
            self.root, text="No image analyzed yet", font=("Helvetica", 13, "bold"),
            bg="#f2f7f2", fg="#2e5339", wraplength=460, justify="left"
        )
        self.result_label.pack(pady=(10, 5))

        self.solution_frame = tk.Frame(self.root, bg="#ffffff", bd=1, relief="solid")
        self.solution_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.solution_text = tk.Label(
            self.solution_frame, text="", font=("Helvetica", 10), bg="#ffffff",
            fg="#333333", wraplength=440, justify="left", anchor="nw", padx=10, pady=10
        )
        self.solution_text.pack(fill="both", expand=True)

        self.status_label = tk.Label(
            self.root, text="", font=("Helvetica", 9, "italic"), bg="#f2f7f2", fg="#888888"
        )
        self.status_label.pack(side="bottom", pady=8)

    def _load_model_safely(self):
        try:
            self.predictor = PlantDiseasePredictor()
            self.status_label.config(text="Model loaded successfully.")
        except Exception as e:
            self.status_label.config(text="Model not found — train it first (see README).")
            messagebox.showwarning(
                "Model not found",
                f"Could not load the trained model:\n{e}\n\n"
                f"Run 'python src/train.py' first, or check that "
                f"'{config.MODEL_PATH}' exists."
            )

    # -------------------------------------------------------------- Actions
    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="Select a leaf image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        if not file_path:
            return

        self.current_image_path = file_path
        self._display_image(file_path)

        if self.predictor is None:
            self.result_label.config(text="Model not loaded — cannot analyze image.")
            return

        self._analyze_image(file_path)

    def _display_image(self, file_path):
        img = Image.open(file_path)
        img.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(img)
        self.image_panel.config(image=photo, width=300, height=300)
        self.image_panel.image = photo  # keep reference

    def _analyze_image(self, file_path):
        self.status_label.config(text="Analyzing...")
        self.root.update_idletasks()

        try:
            result = self.predictor.predict(file_path)
        except Exception as e:
            messagebox.showerror("Prediction error", str(e))
            self.status_label.config(text="Prediction failed.")
            return

        if result.get("is_invalid"):
            err = result.get("error_message") or result.get("error") or "Invalid image."
            messagebox.showwarning("Invalid Image", err)
            self.result_label.config(text=f"⚠️ {err}")
            self.solution_text.config(text="")
            self.status_label.config(text="Image rejected.")
            return

        label = result["label"].replace("___", " - ").replace("_", " ")
        confidence = result["confidence"] * 100
        self.result_label.config(text=f"Diagnosis: {label}\nConfidence: {confidence:.1f}%")

        sol = result["solution"]
        ingredients = ", ".join(sol["ingredients"]) if sol["ingredients"] else "None required"
        solution_text = (
            f"Solution Name: {sol['solution_name']}\n\n"
            f"Ingredients: {ingredients}\n\n"
            f"Preparation: {sol['preparation']}\n\n"
            f"Application: {sol['application']}"
        )
        self.solution_text.config(text=solution_text)
        self.status_label.config(text="Analysis complete.")


def main():
    root = tk.Tk()
    app = PlantDiseaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
