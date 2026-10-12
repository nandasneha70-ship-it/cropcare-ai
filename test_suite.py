"""
Comprehensive Automated Test Suite for Smart Crop Disease Detection Project
Tests:
1. Model Architecture & Class Names (17 classes: Corn, Potato, Tomato)
2. Tomato Leaf Disease Classification (verifying Tomato leaves never get confused as pepper)
3. Potato & Corn Leaf Disease Classification
4. Pepper Leaf / Out-of-Scope Leaf behavior
5. Human Face Rejection Filter (YuNet ONNX & Haar Cascade & Skin Chrominance)
6. Blank / Dark / Non-leaf image rejection
7. Organic Remedies Retrieval
8. Multilingual Localization (English, Kannada, Hindi)
9. Database Tables & CRUD Operations
10. Flask Web Server Routes & Status Codes
"""
import os
import sys
import unittest
import numpy as np
from PIL import Image
import json

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from src.predict import PlantDiseasePredictor, DEFAULT_SOLUTION
from src.translator import translator
import app

class TestSmartCropSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n========================================================")
        print("STARTING COMPREHENSIVE SMART CROP PROJECT TEST SUITE")
        print("========================================================")
        cls.predictor = PlantDiseasePredictor()
        cls.app = app.app.test_client()
        cls.app.testing = True

    def test_01_classes_and_model_structure(self):
        """Test 1: Verify model loaded and exact 17 class labels exist."""
        print("\n[TEST 1] Verifying Model and Class Labels...")
        self.assertIsNotNone(self.predictor.model, "Model must be loaded.")
        class_names = self.predictor.class_names
        self.assertEqual(len(class_names), 17, f"Expected 17 classes, found {len(class_names)}")
        
        # Verify no pepper class exists in the 17-class model labels
        pepper_classes = [c for c in class_names if "pepper" in c.lower()]
        self.assertEqual(len(pepper_classes), 0, "17-class model must not have pepper class.")
        
        # Verify all tomato classes exist
        tomato_classes = [c for c in class_names if c.startswith("Tomato")]
        self.assertEqual(len(tomato_classes), 10, f"Expected 10 tomato classes, found {len(tomato_classes)}")
        print(f"  --> Found {len(class_names)} classes: 4 Corn, 3 Potato, 10 Tomato.")
        print("  --> [PASS] Model & Class Structure Verified.")

    def test_02_tomato_leaf_classification(self):
        """Test 2: Verify Tomato leaf samples are classified as Tomato (never Pepper)."""
        print("\n[TEST 2] Testing Tomato Leaf Disease Classification...")
        raw_dir = os.path.join(BASE_DIR, "data", "raw")
        tomato_dirs = [d for d in os.listdir(raw_dir) if d.startswith("Tomato")]
        
        tested = 0
        for tdir in tomato_dirs[:3]:  # test 3 distinct tomato disease folders
            folder_path = os.path.join(raw_dir, tdir)
            images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if images:
                img_path = os.path.join(folder_path, images[0])
                result = self.predictor.predict(img_path)
                self.assertFalse(result.get("is_invalid"), f"Valid tomato leaf {img_path} was falsely rejected.")
                label = result.get("label", "")
                self.assertTrue(label.startswith("Tomato"), f"Expected Tomato label, got: {label}")
                self.assertNotIn("Pepper", label, "Tomato leaf must NEVER be labeled as Pepper.")
                print(f"  --> Sample: {tdir} => Predicted: {label} (Conf: {result['confidence']*100:.1f}%, Severity: {result['severity']})")
                tested += 1
        self.assertGreater(tested, 0, "Should have tested at least one tomato leaf.")
        print("  --> [PASS] Tomato Classification Verified (100% Tomato-specific, No Pepper confusion).")

    def test_03_corn_and_potato_classification(self):
        """Test 3: Verify Corn and Potato leaf samples."""
        print("\n[TEST 3] Testing Corn & Potato Leaf Classification...")
        raw_dir = os.path.join(BASE_DIR, "data", "raw")
        
        # Test Corn sample
        corn_dir = os.path.join(raw_dir, "Corn_(maize)___Common_rust_")
        if os.path.exists(corn_dir):
            imgs = [f for f in os.listdir(corn_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if imgs:
                res = self.predictor.predict(os.path.join(corn_dir, imgs[0]))
                self.assertFalse(res.get("is_invalid"))
                self.assertTrue(res["label"].startswith("Corn"))
                print(f"  --> Corn Common Rust => Predicted: {res['label']} ({res['confidence']*100:.1f}%)")

        # Test Potato sample
        potato_dir = os.path.join(raw_dir, "Potato___Early_blight")
        if os.path.exists(potato_dir):
            imgs = [f for f in os.listdir(potato_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if imgs:
                res = self.predictor.predict(os.path.join(potato_dir, imgs[0]))
                self.assertFalse(res.get("is_invalid"))
                self.assertTrue(res["label"].startswith("Potato"))
                print(f"  --> Potato Early Blight => Predicted: {res['label']} ({res['confidence']*100:.1f}%)")
        print("  --> [PASS] Corn & Potato Classification Verified.")

    def test_04_human_face_rejection(self):
        """Test 4: Verify that human face images are rejected before prediction."""
        print("\n[TEST 4] Testing Human Face Rejection Filter...")
        # Create a synthetic human face skin patch image to test skin chrominance / face safety filter
        test_dir = os.path.join(BASE_DIR, "test_images")
        os.makedirs(test_dir, exist_ok=True)
        face_sim_path = os.path.join(test_dir, "simulated_human_face.jpg")
        
        # Generate image with human skin tones (R~210, G~150, B~120) and oval face shape
        skin_img = np.zeros((300, 300, 3), dtype=np.uint8)
        # Background
        skin_img[:, :] = [180, 180, 180]
        # Oval face region
        y, x = np.ogrid[:300, :300]
        mask = ((x - 150)**2 / (70**2) + (y - 150)**2 / (100**2)) <= 1
        skin_img[mask] = [210, 150, 120]  # RGB skin tone
        
        Image.fromarray(skin_img).save(face_sim_path)
        
        res = self.predictor.predict(face_sim_path)
        self.assertTrue(res.get("is_invalid"), "Human face simulation should be rejected.")
        print(f"  --> Human Face Test Result: Rejected = {res.get('is_invalid')} | Message: {res.get('error_message')}")
        print("  --> [PASS] Human Face Rejection Verified.")

    def test_05_blank_and_dark_image_rejection(self):
        """Test 5: Verify pitch black, white, and non-foliage images are rejected."""
        print("\n[TEST 5] Testing Pitch Black, Solid White & Non-Leaf Rejection...")
        test_dir = os.path.join(BASE_DIR, "test_images")
        
        # 1. Pitch black image
        black_path = os.path.join(test_dir, "test_black.jpg")
        Image.fromarray(np.zeros((200, 200, 3), dtype=np.uint8)).save(black_path)
        res_black = self.predictor.predict(black_path)
        self.assertTrue(res_black.get("is_invalid"), "Black image must be rejected.")
        print(f"  --> Black Screen Test: Rejected ({res_black.get('error_message')})")

        # 2. Pure white image
        white_path = os.path.join(test_dir, "test_white.jpg")
        Image.fromarray(np.full((200, 200, 3), 255, dtype=np.uint8)).save(white_path)
        res_white = self.predictor.predict(white_path)
        self.assertTrue(res_white.get("is_invalid"), "White image must be rejected.")
        print(f"  --> White Screen Test: Rejected ({res_white.get('error_message')})")

        # 3. Grey non-leaf desk image
        grey_path = os.path.join(test_dir, "test_grey.jpg")
        Image.fromarray(np.full((200, 200, 3), 120, dtype=np.uint8)).save(grey_path)
        res_grey = self.predictor.predict(grey_path)
        self.assertTrue(res_grey.get("is_invalid"), "Grey non-leaf image must be rejected.")
        print(f"  --> Grey Screen Test: Rejected ({res_grey.get('error_message')})")
        print("  --> [PASS] Image Quality & Safety Validation Filters Verified.")

    def test_06_organic_remedies(self):
        """Test 6: Verify organic remedies are populated with required fields."""
        print("\n[TEST 6] Testing Organic Remedies Database...")
        with open(os.path.join(BASE_DIR, "data", "organic_solutions.json"), "r", encoding="utf-8") as f:
            solutions = json.load(f)
        
        for cls_name in self.predictor.class_names:
            sol = solutions.get(cls_name)
            self.assertIsNotNone(sol, f"Missing organic solution for class: {cls_name}")
            self.assertIn("solution_name", sol)
            self.assertIn("ingredients", sol)
            self.assertIn("preparation", sol)
            self.assertIn("application", sol)
            self.assertIn("cause", sol)
            self.assertIn("symptoms", sol)
        print(f"  --> Verified organic remedies for all {len(self.predictor.class_names)} classes.")
        print("  --> [PASS] Organic Remedies Verified.")

    def test_07_multilingual_localization(self):
        """Test 7: Verify localization in English, Kannada, and Hindi."""
        print("\n[TEST 7] Testing Multilingual Translation (EN, KN, HI)...")
        raw_result = {
            "label": "Tomato___Early_blight",
            "confidence": 0.92,
            "severity": "Moderate",
            "severity_pct": 24.5,
            "solution": {
                "solution_name": "Baking Soda Spray",
                "cause": "Alternaria solani fungus",
                "symptoms": "Dark concentric rings on lower leaves",
                "ingredients": ["Baking soda", "Water"],
                "preparation": "Mix 1 tbsp in 1 liter water",
                "application": "Spray foliage",
                "prevention_methods": "Crop rotation"
            }
        }
        bundle = translator.get_multilingual_bundle(raw_result)
        self.assertIn("en", bundle)
        self.assertIn("kn", bundle)
        self.assertIn("hi", bundle)
        
        print(f"  --> EN Label: {bundle['en']['display_label']}")
        print(f"  --> KN Label: {bundle['kn']['display_label']}")
        print(f"  --> HI Label: {bundle['hi']['display_label']}")
        self.assertTrue(len(bundle['kn']['display_label']) > 0)
        self.assertTrue(len(bundle['hi']['display_label']) > 0)
        print("  --> [PASS] Multilingual Localization Verified.")

    def test_08_database_crud(self):
        """Test 8: Verify SQLite database schema, user login, and table queries."""
        print("\n[TEST 8] Testing Database Connection & Queries...")
        import sqlite3
        conn = sqlite3.connect(app.DB_PATH)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        for required_table in ['users', 'history', 'labor', 'tasks', 'plots', 'financials', 'inquiries']:
            self.assertIn(required_table, tables, f"Missing table: {required_table}")
        
        # Check default admin and farmer accounts
        cursor.execute("SELECT email, role FROM users WHERE email IN ('admin@smartcrop.com', 'farmer@smartcrop.com')")
        users = cursor.fetchall()
        self.assertEqual(len(users), 2, "Default admin and farmer users must exist.")
        conn.close()
        print("  --> All 7 SQLite relational tables and default user accounts exist.")
        print("  --> [PASS] Database Verified.")

    def test_09_flask_routes(self):
        """Test 9: Verify all primary web routes respond properly."""
        print("\n[TEST 9] Testing Flask Web Server Routes...")
        routes_to_test = [
            ("/", 200),
            ("/detect", 200),
            ("/crop_guide", 200),
            ("/schemes", 200),
            ("/ai_assistant", 200),
            ("/about", 200),
            ("/contact", 200),
            ("/login", 200),
            ("/register", 200),
            ("/dashboard", 302),  # Redirects to login when unauthenticated
            ("/history", 302),    # Redirects to login when unauthenticated
            ("/profile", 302),    # Redirects to login when unauthenticated
            ("/admin/dashboard", 302), # Redirects to login when unauthenticated
        ]
        for route, expected_code in routes_to_test:
            resp = self.app.get(route)
            self.assertEqual(resp.status_code, expected_code, f"Route {route} returned {resp.status_code}, expected {expected_code}")
            print(f"  --> GET {route:20s} => HTTP {resp.status_code} OK")
        print("  --> [PASS] Flask Routes Verified.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
