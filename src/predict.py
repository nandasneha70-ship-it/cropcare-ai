"""
Loads the trained model and predicts the disease (or healthy status) for a
given plant image, then looks up the matching organic/natural remedy.

Usage (CLI):
    python src/predict.py path/to/leaf_image.jpg
"""
import json
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import tensorflow as tf
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    from tensorflow.keras.utils import load_img, img_to_array
except (ImportError, AttributeError):
    try:
        from tensorflow.keras.preprocessing.image import load_img, img_to_array
    except Exception:
        load_img = None
        img_to_array = None

try:
    from src import config
except ImportError:
    import config

DEFAULT_SOLUTION = {
    "solution_name": "General Organic Botanical Spray",
    "ingredients": ["Neem oil (2 tbsp)", "Liquid soap (1 tsp)", "Water (1 liter)"],
    "preparation": "Mix neem oil with soap to emulsify, then dilute in water thoroughly.",
    "application": "Spray weekly on foliage as a general-purpose organic preventive treatment.",
    "cause": "General agricultural pathogens (fungi, bacteria, or virus)",
    "symptoms": "Leaf spots, discoloration, wilting, curling, or abnormal structural growth.",
    "prevention_methods": "Practice clean weeding, crop rotation, and avoid overhead watering.",
    "chemical_pesticides": {
        "name": "N/A",
        "dosage": "Consult local agricultural officer if necessary",
        "safety_instructions": "Follow standard chemical safety precautions if using synthetic inputs."
    },
    "fertilizer": {
        "fertilizer_type": "Balanced Organic Compost or NPK",
        "quantity": "50g per plant",
        "application_timing": "Bi-weekly during growth period"
    }
}


class PlantDiseasePredictor:
    def __init__(self, model_path=None, class_names_path=None, solutions_path=None):
        model_path = model_path or config.MODEL_PATH
        class_names_path = class_names_path or config.CLASS_NAMES_PATH
        solutions_path = solutions_path or config.ORGANIC_SOLUTIONS_PATH

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at '{model_path}'. Please train the model first.")

        with open(class_names_path, "r", encoding="utf-8") as f:
            self.class_names = json.load(f)

        with open(solutions_path, "r", encoding="utf-8") as f:
            self.solutions_db = json.load(f)

        # Multi-stage model loading to handle Keras 3 deserialization issues
        self.model = None
        try:
            self.model = tf.keras.models.load_model(model_path, compile=False)
        except Exception:
            try:
                self.model = tf.keras.models.load_model(model_path, compile=False, safe_mode=False)
            except Exception:
                pass

        if self.model is None:
            # Fallback: Rebuild model architecture and load weights
            try:
                try:
                    from src.model import build_model
                except ImportError:
                    from model import build_model

                num_classes = len(self.class_names)
                built_model, _ = build_model(num_classes)

                try:
                    built_model.load_weights(model_path)
                    self.model = built_model
                except Exception:
                    import zipfile
                    import tempfile
                    with zipfile.ZipFile(model_path, "r") as zip_ref:
                        weight_files = [f for f in zip_ref.namelist() if f.endswith(".h5") or "weights" in f]
                        if weight_files:
                            temp_dir = tempfile.mkdtemp()
                            extracted_path = zip_ref.extract(weight_files[0], temp_dir)
                            built_model.load_weights(extracted_path)
                            self.model = built_model
            except Exception as err:
                raise RuntimeError(f"Could not load plant disease model from '{model_path}': {err}")

        # Initialize OpenCV face detectors safely
        self.yunet_detector = None
        self.haarcascades = []
        if cv2 is not None:
            # 1. Modern OpenCV YuNet Face Detector
            yunet_model_path = os.path.join(config.MODELS_DIR, "face_detection_yunet_2023mar.onnx")
            if os.path.exists(yunet_model_path) and hasattr(cv2, "FaceDetectorYN"):
                try:
                    self.yunet_detector = cv2.FaceDetectorYN.create(
                        yunet_model_path, "", (300, 300), score_threshold=0.60
                    )
                except Exception:
                    self.yunet_detector = None

            # 2. OpenCV Haar Cascade Classifiers (Frontal and Profile)
            if hasattr(cv2, "CascadeClassifier"):
                cascade_candidates = [
                    "haarcascade_frontalface_default.xml",
                    "haarcascade_frontalface_alt.xml",
                    "haarcascade_frontalface_alt2.xml",
                    "haarcascade_profileface.xml"
                ]
                for name in cascade_candidates:
                    p = os.path.join(config.MODELS_DIR, name)
                    if not os.path.exists(p) and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
                        p = os.path.join(cv2.data.haarcascades, name)
                    if os.path.exists(p):
                        try:
                            clf = cv2.CascadeClassifier(p)
                            if not clf.empty():
                                self.haarcascades.append(clf)
                        except Exception:
                            pass


    def _is_skin_face_roi(self, roi_bgr):
        """Validates if a detected face bounding box contains genuine human skin tones and lacks green chlorophyll."""
        if cv2 is None or roi_bgr is None or roi_bgr.size == 0:
            return False
        try:
            ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)
            hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
            cr = ycrcb[:, :, 1]
            cb = ycrcb[:, :, 2]
            h = hsv[:, :, 0]
            s = hsv[:, :, 1]
            v = hsv[:, :, 2]

            skin = (cr >= 130) & (cr <= 180) & (cb >= 75) & (cb <= 130) & ((h <= 25) | (h >= 160)) & (s >= 20) & (s <= 180) & (v >= 40)
            green = (h >= 25) & (h <= 90) & (s >= 25) & (v >= 30)

            skin_ratio = float(skin.mean())
            green_ratio = float(green.mean())
            return (skin_ratio >= 0.18) and (green_ratio < 0.20)
        except Exception:
            return False

    def detect_human_face(self, img_path_or_pil):
        """
        Detects human face in the image using OpenCV YuNet / Haar Cascades with ROI validation,
        and fallback skin-chrominance facial geometry analysis.
        Returns bool.
        """
        if cv2 is None:
            return False

        try:
            if isinstance(img_path_or_pil, (str, os.PathLike)):
                img_cv = cv2.imread(str(img_path_or_pil))
            elif isinstance(img_path_or_pil, Image.Image):
                img_cv = cv2.cvtColor(np.array(img_path_or_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
            elif isinstance(img_path_or_pil, np.ndarray):
                img_cv = img_path_or_pil
            else:
                return False
        except Exception:
            return False

        if img_cv is None or img_cv.size == 0:
            return False

        h, w = img_cv.shape[:2]

        # Tier 1: YuNet modern OpenCV face detector
        if self.yunet_detector is not None:
            try:
                self.yunet_detector.setInputSize((w, h))
                _, faces = self.yunet_detector.detect(img_cv)
                if faces is not None and len(faces) > 0:
                    for f in faces:
                        if f[-1] >= 0.55:
                            fx, fy, fw, fh = map(int, f[:4])
                            fx, fy = max(0, fx), max(0, fy)
                            fw, fh = min(w - fx, fw), min(h - fy, fh)
                            if fw >= 15 and fh >= 15:
                                if self._is_skin_face_roi(img_cv[fy:fy+fh, fx:fx+fw]):
                                    return True
            except Exception:
                pass

        # Tier 2: Haar Cascades (frontal and profile)
        if self.haarcascades:
            try:
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                for clf in self.haarcascades:
                    faces = clf.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
                    for (fx, fy, fw, fh) in faces:
                        if self._is_skin_face_roi(img_cv[fy:fy+fh, fx:fx+fw]):
                            return True
            except Exception:
                pass

        # Tier 3: Computer Vision Skin Chrominance + Face Geometry Fallback
        try:
            ycrcb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2YCrCb)
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            cr = ycrcb[:, :, 1]
            cb = ycrcb[:, :, 2]
            h_chan = hsv[:, :, 0]
            s_chan = hsv[:, :, 1]
            v_chan = hsv[:, :, 2]

            skin = (cr >= 135) & (cr <= 175) & (cb >= 80) & (cb <= 125) & ((h_chan <= 22) | (h_chan >= 165)) & (s_chan >= 28) & (s_chan <= 170) & (v_chan >= 45)
            green_pixels = (h_chan >= 25) & (h_chan <= 90) & (s_chan >= 25) & (v_chan >= 30)
            green_ratio = float(green_pixels.mean())
            skin_ratio = float(skin.mean())

            if skin_ratio > 0.15 and green_ratio < 0.05:
                skin_u8 = (skin.astype(np.uint8)) * 255
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
                skin_closed = cv2.morphologyEx(skin_u8, cv2.MORPH_CLOSE, kernel)
                contours, _ = cv2.findContours(skin_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                total_area = float(h * w)
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area / total_area > 0.12:
                        bx, by, bw, bh = cv2.boundingRect(cnt)
                        aspect_ratio = float(bh) / max(bw, 1)
                        if 0.7 <= aspect_ratio <= 2.2:
                            return True
        except Exception:
            pass

        return False

    def _preprocess(self, img_path):
        if load_img is not None and img_to_array is not None and isinstance(img_path, (str, os.PathLike)):
            img = load_img(img_path, target_size=config.IMG_SIZE)
            arr = img_to_array(img)
        else:
            img = Image.open(img_path).convert("RGB")
            img = img.resize(config.IMG_SIZE)
            arr = np.array(img, dtype=np.float32)
        arr = np.expand_dims(arr, axis=0)  # model applies its own preprocess_input internally
        return arr

    def _analyze_leaf_severity(self, img_path, is_healthy=False):
        """Analyzes leaf image in HSV space to count spots and calculate severity percentage."""
        if is_healthy:
            return 0.0, "Healthy"

        try:
            with Image.open(img_path) as img_file:
                img = img_file.convert("HSV")
                # Downsample for faster processing
                img_small = img.resize((100, 100))
                pixels = list(img_small.get_flattened_data()) if hasattr(img_small, "get_flattened_data") else list(img_small.getdata())
            
            spot_pixels = 0
            leaf_pixels = 0
            
            for h, s, v in pixels:
                # Filter out background (dark / low saturation pixels)
                # Green in HSV is approximately between hue 35 and 85 (0-255 scale ~ 25-90)
                if s > 30 and v > 30:
                    leaf_pixels += 1
                    # Spot check: yellow, brown, or red spots fall outside green range
                    if not (25 <= h <= 90):
                        spot_pixels += 1
            
            if leaf_pixels == 0:
                return 12.5, "Mild"
            
            spot_pct = (spot_pixels / leaf_pixels) * 100
            spot_pct = min(max(spot_pct, 2.0), 98.0) # bounding
            
            if spot_pct < 15.0:
                severity = "Mild"
            elif spot_pct < 35.0:
                severity = "Moderate"
            else:
                severity = "Severe"
                
            return round(spot_pct, 1), severity
        except Exception:
            # Fallback
            return 15.0, "Moderate"

    def validate_leaf_image(self, img_path_or_pil):
        """
        Validates whether the input image is a plausible plant leaf image.
        Detects pitch black screens, solid colors, blank screens, human faces, and images lacking foliage.
        Returns (is_valid: bool, error_message: str or None)
        """
        try:
            if isinstance(img_path_or_pil, (str, os.PathLike)):
                img = Image.open(img_path_or_pil).convert("RGB")
            elif isinstance(img_path_or_pil, Image.Image):
                img = img_path_or_pil.convert("RGB")
            else:
                img = Image.fromarray(img_path_or_pil).convert("RGB")
        except Exception as e:
            return False, f"Could not open image file: {e}"

        arr = np.array(img, dtype=np.float32)
        mean_val = float(arr.mean())
        std_val = float(arr.std())

        # Check 1: Pitch black or extremely dark image (e.g. black screen, covered camera lens)
        if mean_val < 30.0:
            return False, "Black screen or extremely dark image detected. Please upload or capture a clear, well-lit photo of a crop leaf."

        # Check 2: Solid blank color, grey gradient, or pure white screen
        if std_val < 14.0:
            return False, "Solid or blank image detected. Please upload a clear photo showing leaf details."

        if mean_val > 240.0 and std_val < 25.0:
            return False, "Blank white image detected. Please upload a clear photo of a crop leaf."

        # Check 3: Human face detection BEFORE running plant disease classifier
        if self.detect_human_face(img_path_or_pil):
            return False, "Human face detected. Please upload a clear image of a crop leaf for disease detection."

        # Check 4: Plant foliage / organic color features
        hsv = np.array(img.convert("HSV"), dtype=np.float32)
        H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        # Check 4a: Grey, monochromatic, or desaturated blank image (desk, blank wall, covered lens)
        mean_sat = float(S.mean())
        active_sat_ratio = float((S >= 35).mean())
        if mean_sat < 25.0 or active_sat_ratio < 0.10:
            return False, "Blank or grey image detected. Please upload a clear, well-lit photo of a crop leaf."

        # Active non-dark pixel ratio
        non_dark_ratio = float((V >= 30).mean())
        if non_dark_ratio < 0.10:
            return False, "Image is predominantly dark or empty. Please upload a well-lit photo of a plant leaf."

        # Foliage mask in PIL HSV scale (H in 0..255, S in 0..255):
        # Green foliage: H ~35-140, S >= 40, V >= 30
        # Yellow chlorosis / mosaic / viral symptoms: H ~20-38, S >= 45, V >= 40
        # Brown / necrosis / dried leaf / blight / rust spots: H ~10-25, S >= 40, V >= 28 with R >= G >= B*0.9
        green_mask = (H >= 35) & (H <= 140) & (S >= 40) & (V >= 30)
        yellow_mask = (H >= 20) & (H <= 38) & (S >= 45) & (V >= 40)
        brown_mask = (H >= 10) & (H <= 25) & (S >= 40) & (V >= 28) & (R >= B * 1.05)
        
        foliage_mask = green_mask | yellow_mask | brown_mask
        foliage_ratio = float(foliage_mask.mean())

        if foliage_ratio < 0.12:
            return False, "The uploaded image does not appear to be a plant leaf. Please upload a clear crop leaf image."

        return True, None

    def predict(self, img_path, top_k=1, crop=None):
        """Returns a dict: {label, confidence, solution, severity_pct, severity, top_predictions, is_invalid}"""
        # Step 1: Validate image (Human Face Detection and Non-Leaf Check happen BEFORE model inference)
        is_valid, error_msg = self.validate_leaf_image(img_path)
        if not is_valid:
            return {
                "is_invalid": True,
                "error": error_msg,
                "error_message": error_msg,
                "label": "Invalid Image",
                "confidence": 0.0,
                "severity_pct": 0.0,
                "severity": "N/A",
                "solution": DEFAULT_SOLUTION,
                "top_predictions": []
            }

        # Step 2: Preprocess and predict
        arr = self._preprocess(img_path)
        preds = self.model.predict(arr, verbose=0)[0]

        # Step 3: Crop-aware disambiguation
        crop_clean = (crop or "").strip().lower()
        if crop_clean and crop_clean not in ["auto", "all", "none"]:
            target_prefix = None
            if "potato" in crop_clean:
                target_prefix = "Potato"
            elif "tomato" in crop_clean:
                target_prefix = "Tomato"
            elif "corn" in crop_clean or "maize" in crop_clean:
                target_prefix = "Corn_(maize)"

            if target_prefix:
                matching_indices = [
                    i for i, c in enumerate(self.class_names)
                    if c.startswith(target_prefix)
                ]

                overall_top_idx = int(np.argmax(preds))
                overall_top_label = self.class_names[overall_top_idx]
                overall_top_conf = float(preds[overall_top_idx])

                if "___" in overall_top_label:
                    symptom = overall_top_label.split("___", 1)[1]
                    target_match = f"{target_prefix}___{symptom}"
                    if target_match in self.class_names:
                        chosen_label = target_match
                        chosen_conf = overall_top_conf
                    else:
                        best_match_idx = max(matching_indices, key=lambda idx: preds[idx])
                        chosen_label = self.class_names[best_match_idx]
                        crop_sum = sum(preds[idx] for idx in matching_indices)
                        chosen_conf = float(preds[best_match_idx] / crop_sum) if crop_sum > 0 else float(preds[best_match_idx])
                else:
                    best_match_idx = max(matching_indices, key=lambda idx: preds[idx])
                    chosen_label = self.class_names[best_match_idx]
                    crop_sum = sum(preds[idx] for idx in matching_indices)
                    chosen_conf = float(preds[best_match_idx] / crop_sum) if crop_sum > 0 else float(preds[best_match_idx])

                best_label = chosen_label
                best_confidence = chosen_conf

                sorted_crop_indices = sorted(matching_indices, key=lambda idx: preds[idx], reverse=True)
                crop_sum = sum(preds[idx] for idx in matching_indices) or 1.0
                top_predictions = [
                    {"label": self.class_names[i], "confidence": float(preds[i] / crop_sum)}
                    for i in sorted_crop_indices[:top_k]
                ]
            else:
                top_indices = preds.argsort()[-top_k:][::-1]
                top_predictions = [
                    {"label": self.class_names[i], "confidence": float(preds[i])}
                    for i in top_indices
                    if i < len(self.class_names)
                ]
                best_label = top_predictions[0]["label"]
                best_confidence = top_predictions[0]["confidence"]
        else:
            top_indices = preds.argsort()[-top_k:][::-1]
            top_predictions = [
                {"label": self.class_names[i], "confidence": float(preds[i])}
                for i in top_indices
                if i < len(self.class_names)
            ]
            if not top_predictions:
                best_label = self.class_names[0] if self.class_names else "Unknown"
                best_confidence = 0.0
                top_predictions = [{"label": best_label, "confidence": best_confidence}]
            else:
                best_label = top_predictions[0]["label"]
                best_confidence = top_predictions[0]["confidence"]

        # Step 4: Determine if class is healthy
        is_healthy = "healthy" in best_label.lower()

        # Calculate leaf spot severity
        severity_pct, severity = self._analyze_leaf_severity(img_path, is_healthy=is_healthy)

        # Lookup details with robust fallback
        raw_solution = self.solutions_db.get(best_label) or self.solutions_db.get("_default") or DEFAULT_SOLUTION
        solution = dict(DEFAULT_SOLUTION)
        if isinstance(raw_solution, dict):
            solution.update(raw_solution)

        if not isinstance(solution.get("chemical_pesticides"), dict):
            solution["chemical_pesticides"] = DEFAULT_SOLUTION["chemical_pesticides"]
        if not isinstance(solution.get("fertilizer"), dict):
            solution["fertilizer"] = DEFAULT_SOLUTION["fertilizer"]

        return {
            "label": best_label,
            "confidence": best_confidence,
            "severity_pct": severity_pct,
            "severity": severity,
            "solution": solution,
            "top_predictions": top_predictions,
            "is_invalid": False,
        }


def format_result(result: dict) -> str:
    if result.get("is_invalid"):
        err = result.get("error_message") or result.get("error") or "Invalid Image"
        return f"Error / Rejected Image: {err}"
    lines = []
    lines.append(f"Disease detected: {result.get('label', 'Unknown')}")
    lines.append(f"Confidence: {result.get('confidence', 0.0) * 100:.2f}%")
    lines.append(f"Severity: {result.get('severity', 'N/A')} ({result.get('severity_pct', 0.0)}% affected spots)")
    sol = result.get("solution") or {}
    lines.append(f"\nRecommended Organic Solution: {sol.get('solution_name', 'Organic Remedy')}")
    ingredients = sol.get("ingredients")
    if isinstance(ingredients, list) and ingredients:
        lines.append("Ingredients: " + ", ".join(ingredients))
    elif isinstance(ingredients, str) and ingredients:
        lines.append("Ingredients: " + ingredients)
    lines.append(f"Preparation: {sol.get('preparation', 'N/A')}")
    lines.append(f"Application: {sol.get('application', 'N/A')}")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        img_file = sys.argv[1]
    else:
        # Check for sample upload image if no argument was passed
        sample_paths = [
            os.path.join(config.BASE_DIR, "static", "uploads", "camera_capture.jpg"),
            os.path.join(config.BASE_DIR, "static", "uploads", "apple_black_rot_2.png")
        ]
        img_file = next((p for p in sample_paths if os.path.exists(p)), None)
        if img_file:
            print(f"No image argument provided. Running test prediction on sample image: {img_file}\n")
        else:
            print("Usage: python src/predict.py <path_to_image>")
            print("Example: python src/predict.py static/uploads/camera_capture.jpg")
            sys.exit(0)

    if not os.path.exists(img_file):
        print(f"Error: Image file not found: {img_file}")
        sys.exit(0)

    predictor = PlantDiseasePredictor()
    result = predictor.predict(img_file)
    print(format_result(result))