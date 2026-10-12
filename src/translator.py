# -*- coding: utf-8 -*-
"""
Translation and Localization Service for Smart Crop AI.
Handles complete localization for crop prediction results, UI messages, and farmer advice
in English (en), Kannada (kn), and Hindi (hi).
"""
import os
import json
import urllib.request
import urllib.parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ORGANIC_SOLUTIONS_PATH = os.path.join(DATA_DIR, "organic_solutions.json")
CROP_TRANSLATIONS_PATH = os.path.join(DATA_DIR, "crop_translations.json")


class TranslationService:
    _instance = None
    _dynamic_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationService, cls).__new__(cls)
            cls._instance._load_databases()
        return cls._instance

    def _load_databases(self):
        # Load English organic solutions
        self.solutions_en = {}
        if os.path.exists(ORGANIC_SOLUTIONS_PATH):
            with open(ORGANIC_SOLUTIONS_PATH, "r", encoding="utf-8") as f:
                self.solutions_en = json.load(f)

        # Load Multilingual translations
        self.translations = {"crops": {}, "severities": {}, "labels": {}, "kn": {}, "hi": {}}
        if os.path.exists(CROP_TRANSLATIONS_PATH):
            with open(CROP_TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
                self.translations = json.load(f)

    def get_crop_name(self, raw_label, lang="en"):
        crop_key = raw_label.split("___")[0] if "___" in raw_label else raw_label
        crop_data = self.translations.get("crops", {}).get(crop_key, {})
        if lang in crop_data:
            return crop_data[lang]
        clean_name = crop_key.replace("_", " ")
        return clean_name

    def get_disease_name(self, raw_label, lang="en"):
        if lang == "en":
            parts = raw_label.split("___")
            crop = parts[0].replace("_", " ")
            disease = parts[1].replace("_", " ") if len(parts) > 1 else ""
            if "healthy" in disease.lower():
                return f"{crop} - Healthy Crop"
            return f"{crop} - {disease}"

        lang_data = self.translations.get(lang, {}).get(raw_label, {})
        if "disease_name" in lang_data:
            return lang_data["disease_name"]

        # Fallback to crop + disease translation
        crop_name = self.get_crop_name(raw_label, lang)
        disease_part = raw_label.split("___")[1].replace("_", " ") if "___" in raw_label else ""
        if "healthy" in disease_part.lower():
            if lang == "kn":
                return f"{crop_name} - ಆರೋಗ್ಯಕರ ಬೆಳೆ"
            elif lang == "hi":
                return f"{crop_name} - स्वस्थ फसल"
        return f"{crop_name} - {disease_part}"

    def get_severity_display(self, severity, severity_pct, is_healthy=False, lang="en"):
        sev_dict = self.translations.get("severities", {})
        if is_healthy:
            label = sev_dict.get("Healthy", {}).get(lang, "Healthy")
            return f"{label} (0% {self.get_label('spots_affected', lang)})"

        label = sev_dict.get(severity, {}).get(lang, severity)
        return f"{label} ({severity_pct}% {self.get_label('spots_affected', lang)})"

    def get_label(self, key, lang="en"):
        labels = self.translations.get("labels", {})
        if key in labels:
            return labels[key].get(lang, labels[key].get("en", key))
        return key

    def translate_dynamic(self, text, target_lang="en"):
        """Dynamic translation with fallback and in-memory cache."""
        if not text or target_lang == "en":
            return text

        cache_key = f"{target_lang}::{text}"
        if cache_key in self._dynamic_cache:
            return self._dynamic_cache[cache_key]

        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q=" + urllib.parse.quote(text)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                translated = "".join([segment[0] for segment in data[0] if segment and segment[0]])
                if translated:
                    self._dynamic_cache[cache_key] = translated
                    return translated
        except Exception:
            pass

        return text

    def localize_result(self, result, lang="en"):
        """
        Translates a prediction result dictionary completely into the target language.
        Returns a rich localized result object.
        """
        raw_label = result.get("label", "Tomato___healthy")
        confidence = float(result.get("confidence", 0.0))
        severity = result.get("severity", "Moderate")
        severity_pct = float(result.get("severity_pct", 0.0))
        is_healthy = "healthy" in raw_label.lower()

        # Base English solution
        en_solution = self.solutions_en.get(raw_label) or self.solutions_en.get("_default", {})
        if result.get("solution"):
            en_solution = dict(en_solution)
            en_solution.update(result["solution"])

        if lang == "en":
            localized_sol = dict(en_solution)
            display_label = self.get_disease_name(raw_label, "en")
            crop_name = self.get_crop_name(raw_label, "en")
            severity_display = self.get_severity_display(severity, severity_pct, is_healthy, "en")
        else:
            lang_dict = self.translations.get(lang, {}).get(raw_label)
            is_pretranslated = bool(lang_dict)
            if not lang_dict:
                lang_dict = self.translations.get(lang, {}).get("_default", {})

            # Prepare localized solution
            sol_name = lang_dict.get("solution_name") or en_solution.get("solution_name")
            cause = lang_dict.get("cause") or en_solution.get("cause")
            symptoms = lang_dict.get("symptoms") or en_solution.get("symptoms")
            ingredients = lang_dict.get("ingredients") or en_solution.get("ingredients", [])
            preparation = lang_dict.get("preparation") or en_solution.get("preparation")
            application = lang_dict.get("application") or en_solution.get("application")
            prevention = lang_dict.get("prevention_methods") or en_solution.get("prevention_methods")
            chem = dict(lang_dict.get("chemical_pesticides") or en_solution.get("chemical_pesticides", {}))
            fert = dict(lang_dict.get("fertilizer") or en_solution.get("fertilizer", {}) or {})

            # If this label was not pre-translated, dynamically translate all English text
            if not is_pretranslated and lang in ["kn", "hi"]:
                sol_name = self.translate_dynamic(sol_name, lang)
                cause = self.translate_dynamic(cause, lang)
                symptoms = self.translate_dynamic(symptoms, lang)
                preparation = self.translate_dynamic(preparation, lang)
                application = self.translate_dynamic(application, lang)
                prevention = self.translate_dynamic(prevention, lang)
                if isinstance(ingredients, list):
                    ingredients = [self.translate_dynamic(ing, lang) for ing in ingredients]
                if chem:
                    for ck in ["name", "dosage", "safety_instructions"]:
                        if chem.get(ck) and chem[ck] not in ["N/A", "None", "ಯಾವುದೂ ಇಲ್ಲ", "ಅಗತ್ಯವಿಲ್ಲ"]:
                            chem[ck] = self.translate_dynamic(chem[ck], lang)
                if fert:
                    for fk in ["fertilizer_type", "quantity", "application_timing"]:
                        if fert.get(fk) and fert[fk] not in ["N/A", "None"]:
                            fert[fk] = self.translate_dynamic(fert[fk], lang)

            localized_sol = {
                "solution_name": sol_name,
                "cause": cause,
                "symptoms": symptoms,
                "ingredients": ingredients,
                "preparation": preparation,
                "application": application,
                "prevention_methods": prevention,
                "chemical_pesticides": chem,
                "fertilizer": fert
            }

            display_label = self.get_disease_name(raw_label, lang)
            crop_name = self.get_crop_name(raw_label, lang)
            severity_display = self.get_severity_display(severity, severity_pct, is_healthy, lang)

        is_low_confidence = confidence < 0.65
        low_conf_warning = self.get_label("low_conf_warning", lang) if is_low_confidence else ""

        labels = {k: v.get(lang, v.get("en", "")) for k, v in self.translations.get("labels", {}).items()}
        if "login_save" not in labels:
            if lang == "kn":
                labels["login_save"] = "🔐 ಇತಿಹಾಸ ಉಳಿಸಲು ಲಾಗಿನ್ ಮಾಡಿ"
            elif lang == "hi":
                labels["login_save"] = "🔐 इतिहास सहेजने के लिए लॉगिन करें"
            else:
                labels["login_save"] = "🔐 Login to Save History"

        return {
            "label": raw_label,
            "display_label": display_label,
            "crop_name": crop_name,
            "confidence": confidence,
            "confidence_pct": round(confidence * 100, 1),
            "is_low_confidence": is_low_confidence,
            "low_confidence_warning": low_conf_warning,
            "severity": severity,
            "severity_display": severity_display,
            "severity_pct": severity_pct,
            "is_healthy": is_healthy,
            "solution": localized_sol,
            "lang": lang,
            "labels": labels
        }

    def get_multilingual_bundle(self, result):
        """Returns a dict containing pre-rendered results for all supported languages."""
        return {
            "en": self.localize_result(result, "en"),
            "kn": self.localize_result(result, "kn"),
            "hi": self.localize_result(result, "hi")
        }


# Global singleton instance
translator = TranslationService()
