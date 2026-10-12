// ==========================================
// Smart Crop AI - Farmer Assistant & Dashboard Logic
// ==========================================

// Global state variables - Synchronized with localStorage and cookie
let currentLanguage = localStorage.getItem('farmer_lang') || 'en';
let mapInitialized = false;
let farmMap = null;
let drawnItems = null;

// Multi-language translation database for UI elements, labels, buttons, loading, and alerts
const translationDB = {
    en: {
        "nav-home": "Home",
        "nav-detect": "Detect Disease",
        "nav-schemes": "Govt Schemes",
        "nav-dashboard": "Dashboard",
        "nav-history": "History",
        "nav-logout": "Logout",
        "nav-login": "Login / Sign Up",
        "nav-crop-guide": "Crop Guide",
        "nav-assistant": "AI Farming Assistant",
        "nav-profile": "Profile",
        "nav-about": "About",
        "nav-contact": "Contact",
        "nav-admin": "Admin Panel",
        "dash-welcome": "Hello",
        "dash-subtitle": "Welcome to your Smart Crop Dashboard.",
        "dash-btn-scan": "🌱 New Disease Scan",
        "stat-scans": "Total Scans Performed",
        "stat-status": "Account Status",
        "stat-active": "Active (Farmer)",
        "stat-db": "Primary Database",
        "stat-db-val": "Organic Solution DB",
        "tab-overview": "📊 Overview",
        "tab-scheduler": "📅 Farm Scheduler",
        "tab-finance": "💰 Financials",
        "tab-soil": "🧪 Soil Health",
        "tab-gps": "🗺️ GPS Mapping",
        "tab-market": "📈 Market Prices",
        "btn-capture": "📷 Capture via Camera",
        "btn-analyze": "🌱 Analyze Image",
        "btn-pdf": "📄 Download PDF Report",
        "chat-placeholder": "Ask a farming question...",
        "chat-title": "AI Farmer Assistant",
        "btn-speak": "🔊 Listen",
        "btn-pause": "Pause",
        "btn-resume": "Resume",
        "btn-stop": "Stop",
        "price-title": "Crop Market Price Forecasting (INR / Quintal)",
        "yield-title": "Soil Nutrient & Yield Predictor",
        "yield-btn": "Predict Tonnage Yield",
        "detect-title": "Plant Disease Detection",
        "detect-subtitle": "Upload a high-quality photo of your plant's leaf showing signs of disease to identify the pathology and organic cure.",
        "detect-upload-text": "Drag and drop or click to upload leaf photo",
        "detect-upload-subtext": "Supports PNG, JPG, JPEG up to 10MB",
        "detect-select-btn": "Select Leaf Photo",
        "assistant-title": "AI Farming Assistant",
        "assistant-subtitle": "Ask any farming or disease related question below.",
        "assistant-input-placeholder": "Ask a farming question...",
        "quick-questions-title": "💡 Quick Questions",
        "loading-analyzing": "🌱 Analyzing Leaf Image...",
        "error-no-image": "Please select an image first.",
        "crop-filter-all": "All Crops",
        "crop-filter-vegetables": "Vegetables",
        "crop-filter-fruits": "Fruits",
        "crop-filter-grains": "Grains",
        "crop-filter-cash": "Commercial Crops",
        "crop-guide-title": "Crop Pathology & Organic Treatment Guide",
        "crop-search-placeholder": "Search crops or diseases...",
        "profile-title": "Farmer Profile Settings",
        "profile-photo-label": "Profile Photo",
        "profile-phone": "Phone Number",
        "profile-save-btn": "Save Changes",
        "btn-login-history": "🔐 Login to Save History",
        "crop-select-label": "Select Crop Type (Optional)"
    },
    kn: {
        "nav-home": "ಮುಖಪುಟ",
        "nav-detect": "ರೋಗ ಪತ್ತೆಹಚ್ಚಿ",
        "nav-schemes": "ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು",
        "nav-dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "nav-history": "ಇತಿಹಾಸ",
        "nav-logout": "ಲಾಗ್ ಔಟ್",
        "nav-login": "ಲಾಗಿನ್ / ಸೈನ್ ಅಪ್",
        "nav-crop-guide": "ಬೆಳೆ ಮಾರ್ಗದರ್ಶಿ",
        "nav-assistant": "ಎಐ ಕೃಷಿ ಸಹಾಯಕ",
        "nav-profile": "ಪ್ರೊಫೈಲ್",
        "nav-about": "ನಮ್ಮ ಬಗ್ಗೆ",
        "nav-contact": "ಸಂಪರ್ಕಿಸಿ",
        "nav-admin": "ನಿರ್ವಾಹಕ ಫಲಕ",
        "dash-welcome": "ನಮಸ್ಕಾರ",
        "dash-subtitle": "ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಕ್ರಾಪ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ಗೆ ಸ್ವಾಗತ.",
        "dash-btn-scan": "🌱 ಹೊಸ ರೋಗ ಸ್ಕ್ಯಾನ್",
        "stat-scans": "ಒಟ್ಟು ಮಾಡಿದ ಸ್ಕ್ಯಾನ್‌ಗಳು",
        "stat-status": "ಖಾತೆಯ ಸ್ಥಿತಿ",
        "stat-active": "ಸಕ್ರಿಯ (ರೈತ)",
        "stat-db": "ಪ್ರಾಥಮಿಕ ಡೇಟಾಬೇಸ್",
        "stat-db-val": "ಸಾವಯವ ಪರಿಹಾರಗಳು",
        "tab-overview": "📊 ಅವಲೋಕನ",
        "tab-scheduler": "📅 ವೇಳಾಪಟ್ಟಿ",
        "tab-finance": "💰 ಹಣಕಾಸು",
        "tab-soil": "🧪 ಮಣ್ಣಿನ ಆರೋಗ್ಯ",
        "tab-gps": "🗺️ ಜಿಪಿಎಸ್ ಮ್ಯಾಪಿಂಗ್",
        "tab-market": "📈 ಮಾರುಕಟ್ಟೆ ಬೆಲೆ",
        "btn-capture": "📷 ಕ್ಯಾಮರಾ ಮೂಲಕ ಶೂಟ್ ಮಾಡಿ",
        "btn-analyze": "🌱 ಚಿತ್ರ ವಿಶ್ಲೇಷಿಸಿ",
        "btn-pdf": "📄 ಪಿಡಿಎಫ್ ವರದಿ ಡೌನ್‌ಲೋಡ್",
        "chat-placeholder": "ಕೃಷಿ ಬಗ್ಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ...",
        "chat-title": "ಕೃಷಿ ಸಹಾಯ ಚಾಟ್‌ಬಾಟ್",
        "btn-speak": "🔊 ಕೇಳಿ",
        "btn-pause": "ವಿರಾಮ",
        "btn-resume": "ಮುಂದುವರಿಸಿ",
        "btn-stop": "ನಿಲ್ಲಿಸಿ",
        "price-title": "ಬೆಳೆ ಮಾರುಕಟ್ಟೆ ಬೆಲೆ ಮುನ್ಸೂಚನೆ (ರೂ / ಕ್ವಿಂಟಲ್)",
        "yield-title": "ಮಣ್ಣಿನ ಪೋಷಕಾಂಶ ಮತ್ತು ಇಳುವರಿ ಮುನ್ಸೂಚನೆ",
        "yield-btn": "ಇಳುವರಿ ಟನ್ ಲೆಕ್ಕಾಚಾರ ಮಾಡಿ",
        "detect-title": "ಬೆಳೆ ರೋಗ ಪತ್ತೆಹಚ್ಚುವಿಕೆ",
        "detect-subtitle": "ರೋಗದ ಲಕ್ಷಣಗಳು ಕಾಣುತ್ತಿರುವ ಎಲೆಯ ಸ್ಪಷ್ಟ ಫೋಟೋವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ, ರೋಗದ ಕಾರಣ ಮತ್ತು ಸಾವಯವ ಪರಿಹಾರವನ್ನು ತಕ್ಷಣ ತಿಳಿಯಿರಿ.",
        "detect-upload-text": "ಎಲೆಯ ಫೋಟೋವನ್ನು ಇಲ್ಲಿಗೆ ಎಳೆಯಿರಿ ಅಥವಾ ಕ್ಲಿಕ್ ಮಾಡಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "detect-upload-subtext": "PNG, JPG, JPEG ಫಾರ್ಮ್ಯಾಟ್‌ಗಳು ಲಭ್ಯ (10MB ವರೆಗೆ)",
        "detect-select-btn": "ಎಲೆಯ ಫೋಟೋ ಆಯ್ಕೆಮಾಡಿ",
        "assistant-title": "ಎಐ ಕೃಷಿ ಸಹಾಯಕ",
        "assistant-subtitle": "ಕೃಷಿ, ಬೆಳೆ ರೋಗಗಳು ಅಥವಾ ಸಾವಯವ ಪರಿಹಾರಗಳ ಬಗ್ಗೆ ಯಾವುದೇ ಪ್ರಶ್ನೆ ಕೇಳಿ.",
        "assistant-input-placeholder": "ಕೃಷಿ ಅಥವಾ ರೋಗದ ಬಗ್ಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ...",
        "quick-questions-title": "💡 ತ್ವರಿತ ಪ್ರಶ್ನೆಗಳು",
        "loading-analyzing": "🌱 ಬೆಳೆಯ ಎಲೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...",
        "error-no-image": "ದಯವಿಟ್ಟು ಮೊದಲು ಎಲೆಯ ಚಿತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
        "crop-filter-all": "ಎಲ್ಲಾ ಬೆಳೆಗಳು",
        "crop-filter-vegetables": "ತರಕಾರಿಗಳು",
        "crop-filter-fruits": "ಹಣ್ಣುಗಳು",
        "crop-filter-grains": "ಧಾನ್ಯಗಳು",
        "crop-filter-cash": "ವಾಣಿಜ್ಯ ಬೆಳೆಗಳು",
        "crop-guide-title": "ಬೆಳೆ ರೋಗಶಾಸ್ತ್ರ ಮತ್ತು ಸಾವಯವ ಚಿಕಿತ್ಸಾ ಮಾರ್ಗದರ್ಶಿ",
        "crop-search-placeholder": "ಬೆಳೆಗಳು ಅಥವಾ ರೋಗಗಳನ್ನು ಹುಡುಕಿ...",
        "profile-title": "ರೈತರ ಪ್ರೊಫೈಲ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
        "profile-photo-label": "ಪ್ರೊಫೈಲ್ ಫೋಟೋ",
        "profile-phone": "ದೂರವಾಣಿ ಸಂಖ್ಯೆ",
        "profile-save-btn": "ಬದಲಾವಣೆಗಳನ್ನು ಉಳಿಸಿ",
        "btn-login-history": "🔐 ಇತಿಹಾಸ ಉಳಿಸಲು ಲಾಗಿನ್ ಮಾಡಿ",
        "crop-select-label": "ಬೆಳೆಯ ವಿಧವನ್ನು ಆಯ್ಕೆಮಾಡಿ (ಐಚ್ಛಿಕ)"
    },
    hi: {
        "nav-home": "होम",
        "nav-detect": "रोग पहचान",
        "nav-schemes": "सरकारी योजनाएं",
        "nav-dashboard": "डैशबोर्ड",
        "nav-history": "इतिहास",
        "nav-logout": "लॉग आउट",
        "nav-login": "लॉगिन / साइन अप",
        "nav-crop-guide": "फसल गाइड",
        "nav-assistant": "एआई कृषि सहायक",
        "nav-profile": "प्रोफ़ाइल",
        "nav-about": "हमारे बारे में",
        "nav-contact": "संपर्क",
        "nav-admin": "एडमिन पैनल",
        "dash-welcome": "नमस्ते",
        "dash-subtitle": "आपके स्मार्ट क्रॉप डैशबोर्ड में आपका स्वागत है।",
        "dash-btn-scan": "🌱 नया रोग स्कैन",
        "stat-scans": "कुल किए गए स्कैन",
        "stat-status": "खाता स्थिति",
        "stat-active": "सक्रिय (किसान)",
        "stat-db": "प्राथमिक डेटाबेस",
        "stat-db-val": "जैविक समाधान डेटाबेस",
        "tab-overview": "📊 अवलोकन",
        "tab-scheduler": "📅 कृषि अनुसूची",
        "tab-finance": "💰 वित्तीय स्थिति",
        "tab-soil": "🧪 मिट्टी का स्वास्थ्य",
        "tab-gps": "🗺️ जीपीएस मैपिंग",
        "tab-market": "📈 बाजार मूल्य",
        "btn-capture": "📷 कैमरा से कैप्चर करें",
        "btn-analyze": "🌱 चित्र विश्लेषण करें",
        "btn-pdf": "📄 पीडीएफ रिपोर्ट डाउनलोड करें",
        "chat-placeholder": "कृषि संबंधित प्रश्न पूछें...",
        "chat-title": "एआई किसान सहायक",
        "btn-speak": "🔊 सुनें",
        "btn-pause": "रोकें",
        "btn-resume": "जारी रखें",
        "btn-stop": "बंद करें",
        "price-title": "फसल बाजार मूल्य पूर्वानुमान (रुपये / क्विंटल)",
        "yield-title": "मिट्टी पोषक तत्व और उपज भविष्यवक्ता",
        "yield-btn": "अनुमानित उपज की गणना करें",
        "detect-title": "पौधों के रोग की पहचान",
        "detect-subtitle": "रोग का निदान और जैविक उपचार जानने के लिए पौधे की पत्ती की स्पष्ट फोटो अपलोड करें।",
        "detect-upload-text": "पत्ती की फोटो यहाँ खींचें या अपलोड करने के लिए क्लिक करें",
        "detect-upload-subtext": "PNG, JPG, JPEG समर्थित (10MB तक)",
        "detect-select-btn": "पत्ती की फोटो चुनें",
        "assistant-title": "एआई किसान सहायक",
        "assistant-subtitle": "कृषि, फसल रोग या जैविक उपचार से जुड़ा कोई भी प्रश्न पूछें।",
        "assistant-input-placeholder": "कृषि संबंधित प्रश्न पूछें...",
        "quick-questions-title": "💡 त्वरित प्रश्न",
        "loading-analyzing": "🌱 पत्ती का विश्लेषण हो रहा है...",
        "error-no-image": "कृपया पहले पत्ती की फोटो चुनें।",
        "crop-filter-all": "सभी फसलें",
        "crop-filter-vegetables": "सब्जियां",
        "crop-filter-fruits": "फल",
        "crop-filter-grains": "अनाज",
        "crop-filter-cash": "व्यावसायिक फसलें",
        "crop-guide-title": "फसल रोग विज्ञान और जैविक उपचार गाइड",
        "crop-search-placeholder": "फसल या रोग खोजें...",
        "profile-title": "किसान प्रोफ़ाइल सेटिंग्स",
        "profile-photo-label": "प्रोफ़ाइल फोटो",
        "profile-phone": "फ़ोन नंबर",
        "profile-save-btn": "परिवर्तन सहेजें",
        "btn-login-history": "🔐 इतिहास सहेजने के लिए लॉगिन करें",
        "crop-select-label": "फसल का प्रकार चुनें (वैकल्पिक)"
    }
};

// Apply translations based on state language to all matching DOM elements
function applyTranslation() {
    const dict = translationDB[currentLanguage] || translationDB['en'];
    document.querySelectorAll('[data-lang-key]').forEach(el => {
        const key = el.getAttribute('data-lang-key');
        if (dict[key]) {
            if (el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'search')) {
                el.placeholder = dict[key];
            } else {
                el.innerHTML = dict[key];
            }
        }
    });

    // Sync all language dropdown selectors on the page
    document.querySelectorAll('.lang-selector, #langSelect').forEach(select => {
        select.value = currentLanguage;
    });

    // Sync hidden language inputs
    const formLang = document.getElementById('formLangInput');
    if (formLang) formLang.value = currentLanguage;
}

// Global Set Language handler with complete persistence across client & server
function setLanguage(lang) {
    if (!lang) return;
    currentLanguage = lang;
    localStorage.setItem('farmer_lang', lang);
    document.cookie = "farmer_lang=" + lang + "; path=/; max-age=31536000";

    // Cancel any active speech and reset playback controls when language changes
    stopSpeech();

    // Asynchronously notify backend session
    fetch('/set_lang', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({lang: lang})
    }).catch(e => console.log('Lang sync error', e));

    // Update UI elements
    applyTranslation();

    // Dynamically update complete crop analysis report if on result.html
    updateResultPageLanguage(lang);

    // Dynamically update AI Assistant console if on ai_assistant.html
    updateConsoleAssistant(lang);
}

// Dynamically localizes all 45+ crop analysis output elements on result.html
function updateResultPageLanguage(lang) {
    const dataEl = document.getElementById('multilingualData');
    if (!dataEl) return;

    let bundle;
    try {
        bundle = JSON.parse(dataEl.textContent);
    } catch (e) {
        console.error("Failed to parse multilingualData", e);
        return;
    }

    const data = bundle[lang] || bundle['en'];
    if (!data) return;

    const sol = data.solution || {};
    const labels = data.labels || {};

    // 1. Report Heading & Subtitle
    const reportHeading = document.getElementById('reportHeading');
    if (reportHeading && labels.report_heading) reportHeading.textContent = labels.report_heading;

    const reportSubtitle = document.getElementById('reportSubtitle');
    if (reportSubtitle && labels.report_subtitle) reportSubtitle.textContent = labels.report_subtitle;

    // 2. Left Side: Diagnosis Card
    const diagTitle = document.getElementById('diagTitle');
    if (diagTitle && labels.classification_output) diagTitle.textContent = labels.classification_output;

    const diseaseLabel = document.getElementById('diseaseLabel');
    if (diseaseLabel && data.display_label) diseaseLabel.textContent = data.display_label;

    const severityBadge = document.getElementById('severityBadge');
    if (severityBadge && data.severity_display) {
        severityBadge.textContent = data.severity_display;
        severityBadge.className = 'severity-badge ' + (data.is_healthy ? 'mild' : (data.severity === 'Mild' ? 'mild' : (data.severity === 'Moderate' ? 'moderate' : 'severe')));
    }

    const confLabel = document.getElementById('confLabel');
    if (confLabel && labels.confidence) confLabel.textContent = labels.confidence + ":";

    const confValue = document.getElementById('confValue');
    if (confValue && data.confidence_pct !== undefined) confValue.textContent = data.confidence_pct + "%";

    const lowConfAlert = document.getElementById('lowConfAlert');
    if (lowConfAlert) {
        if (data.is_low_confidence && data.low_confidence_warning) {
            lowConfAlert.textContent = data.low_confidence_warning;
            lowConfAlert.style.display = 'block';
        } else {
            lowConfAlert.style.display = 'none';
        }
    }

    const btnSpeak = document.getElementById('btnSpeak');
    if (btnSpeak && labels.listen) btnSpeak.textContent = labels.listen;

    // 3. Right Side: Diagnosis Content
    const diagSummaryTitle = document.getElementById('diagSummaryTitle');
    if (diagSummaryTitle && labels.comprehensive_diagnosis) diagSummaryTitle.textContent = labels.comprehensive_diagnosis;

    // Disease Pathology & Cause
    const pathologyHeading = document.getElementById('pathologyHeading');
    if (pathologyHeading && labels.pathology_heading) pathologyHeading.textContent = labels.pathology_heading;

    const causeLabel = document.getElementById('causeLabel');
    if (causeLabel && labels.possible_cause) causeLabel.textContent = labels.possible_cause + ":";

    const causeVal = document.getElementById('causeVal');
    if (causeVal && sol.cause !== undefined) causeVal.textContent = sol.cause;

    const symptomsLabel = document.getElementById('symptomsLabel');
    if (symptomsLabel && labels.observable_symptoms) symptomsLabel.textContent = labels.observable_symptoms + ":";

    const symptomsVal = document.getElementById('symptomsVal');
    if (symptomsVal && sol.symptoms !== undefined) symptomsVal.textContent = sol.symptoms;

    // Recommended Organic Remedy
    const organicHeading = document.getElementById('organicHeading');
    if (organicHeading && labels.organic_remedy_heading) organicHeading.textContent = labels.organic_remedy_heading;

    const organicSolutionName = document.getElementById('organicSolutionName');
    if (organicSolutionName && sol.solution_name) organicSolutionName.textContent = sol.solution_name;

    const ingredientsBlock = document.getElementById('ingredientsBlock');
    const ingredientsLabel = document.getElementById('ingredientsLabel');
    const ingredientsList = document.getElementById('ingredientsList');

    if (ingredientsBlock && ingredientsList) {
        if (sol.ingredients && sol.ingredients.length > 0) {
            ingredientsBlock.style.display = 'block';
            if (ingredientsLabel && labels.ingredients) ingredientsLabel.textContent = labels.ingredients + ":";
            ingredientsList.innerHTML = '';
            sol.ingredients.forEach(ing => {
                const li = document.createElement('li');
                li.className = 'ingredient-tag';
                li.textContent = ing;
                ingredientsList.appendChild(li);
            });
        } else {
            ingredientsBlock.style.display = 'none';
        }
    }

    const prepLabel = document.getElementById('prepLabel');
    if (prepLabel && labels.preparation) prepLabel.textContent = labels.preparation + ":";

    const prepVal = document.getElementById('prepVal');
    if (prepVal && sol.preparation !== undefined) prepVal.textContent = sol.preparation;

    const appLabel = document.getElementById('appLabel');
    if (appLabel && labels.application) appLabel.textContent = labels.application + ":";

    const appVal = document.getElementById('appVal');
    if (appVal && sol.application !== undefined) appVal.textContent = sol.application;

    // Chemical Remedies
    const chemicalSection = document.getElementById('chemicalSection');
    const chem = sol.chemical_pesticides;
    const hasChem = chem && chem.name && chem.name !== 'N/A' && chem.name !== 'None' && chem.name !== 'ಯಾವುದೂ ಇಲ್ಲ' && chem.name !== 'ಅಗತ್ಯವಿಲ್ಲ' && chem.name !== 'आवश्यकता नहीं';

    if (chemicalSection) {
        if (hasChem) {
            chemicalSection.style.display = 'block';
            const chemHeading = document.getElementById('chemHeading');
            if (chemHeading && labels.chemical_heading) chemHeading.textContent = labels.chemical_heading;

            const chemProdLabel = document.getElementById('chemProdLabel');
            if (chemProdLabel && labels.product_name) chemProdLabel.textContent = labels.product_name + ":";

            const chemProdVal = document.getElementById('chemProdVal');
            if (chemProdVal) chemProdVal.textContent = chem.name;

            const chemDosageLabel = document.getElementById('chemDosageLabel');
            if (chemDosageLabel && labels.recommended_dosage) chemDosageLabel.textContent = labels.recommended_dosage + ":";

            const chemDosageVal = document.getElementById('chemDosageVal');
            if (chemDosageVal) chemDosageVal.textContent = chem.dosage;

            const chemSafetyLabel = document.getElementById('chemSafetyLabel');
            if (chemSafetyLabel && labels.safety_instructions) chemSafetyLabel.textContent = labels.safety_instructions + ":";

            const chemSafetyVal = document.getElementById('chemSafetyVal');
            if (chemSafetyVal) chemSafetyVal.textContent = chem.safety_instructions;
        } else {
            chemicalSection.style.display = 'none';
        }
    }

    // Fertilizer & Soil Nutrition Guide
    const fertilizerSection = document.getElementById('fertilizerSection');
    const fert = sol.fertilizer;
    const hasFert = fert && fert.fertilizer_type && fert.fertilizer_type !== 'N/A' && fert.fertilizer_type !== 'None';

    if (fertilizerSection) {
        if (hasFert) {
            fertilizerSection.style.display = 'block';
            const fertHeading = document.getElementById('fertHeading');
            if (fertHeading && labels.fertilizer_heading) fertHeading.textContent = labels.fertilizer_heading;

            const fertRecLabel = document.getElementById('fertRecLabel');
            if (fertRecLabel && labels.fertilizer_rec) fertRecLabel.textContent = labels.fertilizer_rec + ":";

            const fertTypeVal = document.getElementById('fertTypeVal');
            if (fertTypeVal) fertTypeVal.textContent = fert.fertilizer_type;

            const fertQtyLabel = document.getElementById('fertQtyLabel');
            if (fertQtyLabel && labels.quantity) fertQtyLabel.textContent = labels.quantity + ":";

            const fertQtyVal = document.getElementById('fertQtyVal');
            if (fertQtyVal) fertQtyVal.textContent = fert.quantity;

            const fertTimeLabel = document.getElementById('fertTimeLabel');
            if (fertTimeLabel && labels.application_schedule) fertTimeLabel.textContent = labels.application_schedule + ":";

            const fertTimeVal = document.getElementById('fertTimeVal');
            if (fertTimeVal) fertTimeVal.textContent = fert.application_timing;
        } else {
            fertilizerSection.style.display = 'none';
        }
    }

    // Prevention Methods
    const prevHeading = document.getElementById('prevHeading');
    if (prevHeading && labels.prevention_heading) prevHeading.textContent = labels.prevention_heading;

    const prevVal = document.getElementById('prevVal');
    if (prevVal && sol.prevention_methods !== undefined) prevVal.textContent = sol.prevention_methods;

    // Action Buttons
    const btnScanAnother = document.getElementById('btnScanAnother');
    if (btnScanAnother && labels.scan_another) btnScanAnother.textContent = labels.scan_another;

    const btnPdfReport = document.getElementById('btnPdfReport');
    if (btnPdfReport && labels.download_pdf) btnPdfReport.textContent = labels.download_pdf;

    const btnDashboardLink = document.getElementById('btnDashboardLink');
    if (btnDashboardLink && labels.dashboard_btn) btnDashboardLink.textContent = labels.dashboard_btn;

    const btnLoginHistory = document.getElementById('btnLoginSaveHistory');
    if (btnLoginHistory && labels.login_save) btnLoginHistory.textContent = labels.login_save;

    // Refresh TTS playback UI language
    updateSpeechUI();
}

// Localizes the AI Assistant Console on ai_assistant.html
function updateConsoleAssistant(lang) {
    const welcomeMsg = document.getElementById('consoleWelcomeMsg');
    if (welcomeMsg) {
        if (lang === 'kn') {
            welcomeMsg.textContent = "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಆತ್ಮೀಯ ಎಐ ಕೃಷಿ ಸಹಾಯಕ. 🌱 ಬೆಳೆ ರೋಗಗಳು, ಸಾವಯವ ಔಷಧಗಳು, ನೀರಾವರಿ ಹಾಗೂ ಮಣ್ಣಿನ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ಸಹಾಯ ಮಾಡಲು ನಾನು ಇಲ್ಲಿದ್ದೇನೆ. ಎಡಭಾಗದ ತ್ವರಿತ ಪ್ರಶ್ನೆಗಳನ್ನು ಬಳಸಿ ಅಥವಾ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಕೆಳಗೆ ಟೈಪ್ ಮಾಡಿ!";
        } else if (lang === 'hi') {
            welcomeMsg.textContent = "नमस्ते! मैं आपका मित्रवत एआई किसान सहायक हूँ। 🌱 फसल रोगों, जैविक उपचारों, सिंचाई और मिट्टी के स्वास्थ्य में सहायता के लिए यहाँ हूँ। बाईं ओर दिए गए त्वरित प्रश्नों का उपयोग करें या अपना प्रश्न नीचे लिखें!";
        } else {
            welcomeMsg.textContent = "Hello! I am your friendly AI Farming Assistant. 🌱 I am here to help you understand crop diseases, organic remedies, watering, and soil health. Feel free to use the quick questions on the left or type your own question below!";
        }
    }

    const qList = document.getElementById('quickQuestionsList');
    if (qList) {
        if (lang === 'kn') {
            qList.innerHTML = `
                <div class="suggested-card" onclick="askConsoleSuggested('ನನ್ನ ಬೆಳೆಯ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಏನು ಮಾಡಬೇಕು?')">
                    ❓ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಏನು ಮಾಡಬೇಕು?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('ಶಿಲೀಂಧ್ರ ರೋಗಗಳನ್ನು ತಡೆಯುವುದು ಹೇಗೆ?')">
                    🛡️ ಶಿಲೀಂಧ್ರ ರೋಗಗಳನ್ನು ತಡೆಯುವುದು ಹೇಗೆ?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('ಟೊಮ್ಯಾಟೊ ಅಂಗಮಾರಿ ರೋಗದ ಲಕ್ಷಣಗಳೇನು?')">
                    🍅 ಟೊಮ್ಯಾಟೊ ಅಂಗಮಾರಿ ರೋಗದ ಲಕ್ಷಣಗಳೇನು?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('ಬೆಳೆಗೆ ಎಷ್ಟು ದಿನಗಳಿಗೊಮ್ಮೆ ನೀರು ಕೊಡಬೇಕು?')">
                    💧 ಬೆಳೆಗೆ ಎಷ್ಟು ದಿನಗಳಿಗೊಮ್ಮೆ ನೀರು ಕೊಡಬೇಕು?
                </div>
            `;
        } else if (lang === 'hi') {
            qList.innerHTML = `
                <div class="suggested-card" onclick="askConsoleSuggested('मेरी फसल की पत्तियां पीली क्यों पड़ रही हैं?')">
                    ❓ पत्तियां पीली क्यों पड़ रही हैं?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('फंगल रोगों से कैसे बचें?')">
                    🛡️ फंगल रोगों से कैसे बचें?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('टमाटर के झुलसा रोग के लक्षण क्या हैं?')">
                    🍅 टमाटर झुलसा रोग के लक्षण क्या हैं?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('फसल को कितने दिनों में पानी देना चाहिए?')">
                    💧 फसल को कितने दिनों में पानी देना चाहिए?
                </div>
            `;
        } else {
            qList.innerHTML = `
                <div class="suggested-card" onclick="askConsoleSuggested('Why are my crop leaves turning yellow?')">
                    ❓ Why are my crop leaves turning yellow?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('How can I prevent fungal diseases?')">
                    🛡️ How can I prevent fungal diseases?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('What are the symptoms of tomato blight?')">
                    🍅 What are the symptoms of tomato blight?
                </div>
                <div class="suggested-card" onclick="askConsoleSuggested('How often should I water my crop?')">
                    💧 How often should I water my crop?
                </div>
            `;
        }
    }

    const btnAskScan = document.getElementById('btnAskScan');
    if (btnAskScan) {
        if (lang === 'kn') btnAskScan.textContent = "🍀 ಈ ರೋಗಕ್ಕೆ ಪರಿಹಾರವೇನು?";
        else if (lang === 'hi') btnAskScan.textContent = "🍀 इस बीमारी का इलाज?";
        else btnAskScan.textContent = "🍀 How to Control This?";
    }

    const activeScanLabel = document.getElementById('activeScanLabel');
    if (activeScanLabel) {
        if (lang === 'kn') activeScanLabel.textContent = "ಪತ್ತೆಯಾದ ರೋಗ:";
        else if (lang === 'hi') activeScanLabel.textContent = "सक्रिय स्कैन:";
        else activeScanLabel.textContent = "Active Scan:";
    }
}

function askScanQuestion() {
    if (currentLanguage === 'kn') {
        askConsoleSuggested("ಈ ರೋಗವನ್ನು ಹೇಗೆ ನಿಯಂತ್ರಿಸುವುದು?");
    } else if (currentLanguage === 'hi') {
        askConsoleSuggested("इस बीमारी को कैसे नियंत्रित करें?");
    } else {
        askConsoleSuggested("How can I control this disease?");
    }
}

// Formats bot responses for bold markdown and clean line breaks
function formatBotMessage(text) {
    if (!text) return "";
    let safe = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    // Replace **bold** with <strong>bold</strong>
    safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    return safe;
}

// ==========================================
// Text-to-Speech (TTS) & Language Helpers
// ==========================================

// Preload available synthesis voices across all browsers (Chrome, Edge, Safari, Firefox)
let systemVoices = [];
function preloadVoices() {
    if ('speechSynthesis' in window) {
        systemVoices = window.speechSynthesis.getVoices() || [];
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = () => {
                systemVoices = window.speechSynthesis.getVoices() || [];
            };
        }
    }
}
preloadVoices();

// Returns the current selected language using the application's existing state/DOM/storage
function getCurrentSelectedLanguage() {
    let lang = null;

    // 1. Existing language selector dropdown on page
    const langSelect = document.getElementById('langSelect') || document.querySelector('.lang-selector');
    if (langSelect && langSelect.value && ['en', 'kn', 'hi'].includes(langSelect.value)) {
        lang = langSelect.value;
    }

    // 2. Existing application state variable
    if (!lang && typeof currentLanguage === 'string' && ['en', 'kn', 'hi'].includes(currentLanguage)) {
        lang = currentLanguage;
    }

    // 3. Application session cookie 'farmer_lang'
    if (!lang) {
        const cookieMatch = document.cookie.match(/(?:^|;\s*)farmer_lang=([^;]+)/);
        if (cookieMatch && ['en', 'kn', 'hi'].includes(cookieMatch[1])) {
            lang = cookieMatch[1];
        }
    }

    // 4. LocalStorage preference 'farmer_lang'
    if (!lang) {
        try {
            const stored = localStorage.getItem('farmer_lang');
            if (stored && ['en', 'kn', 'hi'].includes(stored)) {
                lang = stored;
            }
        } catch (e) {}
    }

    // 5. Existing hidden form input or meta tag
    if (!lang) {
        const metaTag = document.querySelector('meta[name="current-lang"]');
        if (metaTag && metaTag.content && ['en', 'kn', 'hi'].includes(metaTag.content)) {
            lang = metaTag.content;
        }
    }

    if (!lang) {
        const formInput = document.getElementById('formLangInput');
        if (formInput && formInput.value && ['en', 'kn', 'hi'].includes(formInput.value)) {
            lang = formInput.value;
        }
    }

    const finalLang = lang || 'en';
    if (typeof currentLanguage !== 'undefined' && currentLanguage !== finalLang) {
        currentLanguage = finalLang;
    }
    return finalLang;
}

// Function to display a user-friendly notice when a requested language voice is missing in browser
function showTTSVoiceNotice(message) {
    let notice = document.getElementById('ttsVoiceNotice');
    if (!notice) {
        notice = document.createElement('div');
        notice.id = 'ttsVoiceNotice';
        notice.style.cssText = 'margin-top: 12px; padding: 10px 16px; background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 8px; font-size: 13.5px; font-weight: 500; text-align: center; max-width: 480px; margin-left: auto; margin-right: auto; box-shadow: 0 2px 6px rgba(0,0,0,0.08); transition: opacity 0.3s ease;';
        const btnSpeak = document.getElementById('btnSpeak');
        if (btnSpeak && btnSpeak.parentNode) {
            btnSpeak.parentNode.appendChild(notice);
        } else {
            const diagContent = document.getElementById('diagnosisContent');
            if (diagContent) {
                diagContent.prepend(notice);
            } else {
                document.body.appendChild(notice);
            }
        }
    }
    notice.textContent = "⚠️ " + message;
    notice.style.display = 'block';
    notice.style.opacity = '1';

    clearTimeout(window._ttsNoticeTimer);
    window._ttsNoticeTimer = setTimeout(() => {
        if (notice) {
            notice.style.opacity = '0';
            setTimeout(() => { notice.style.display = 'none'; }, 300);
        }
    }, 7000);
}

// Locate the most suitable speech synthesis voice matching the requested language
function findVoiceForLanguage(targetLang, shortLang) {
    if (!('speechSynthesis' in window)) return null;
    let voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) {
        voices = systemVoices;
    }
    if (!voices || voices.length === 0) return null;

    const normTarget = (targetLang || '').toLowerCase().replace('_', '-');
    const normShort = (shortLang || targetLang.split(/[-_]/)[0]).toLowerCase();

    // 1. Exact match on BCP 47 locale (e.g., 'kn-in', 'hi-in', 'en-in')
    let matched = voices.find(v => v.lang && v.lang.toLowerCase().replace('_', '-') === normTarget);
    if (matched) return matched;

    // 2. Prefix match on language code (e.g. starts with 'kn', 'hi', 'en')
    matched = voices.find(v => {
        if (!v.lang) return false;
        const vLang = v.lang.toLowerCase().replace('_', '-');
        return vLang === normShort || vLang.startsWith(normShort + '-') || vLang.startsWith(normShort + '_');
    });
    if (matched) return matched;

    // 3. Name-based match for language keywords
    const keywordsByLang = {
        'kn': ['kannada', 'kn-in', 'kn_in', 'ಕನ್ನಡ'],
        'hi': ['hindi', 'hi-in', 'hi_in', 'हिन्दी'],
        'en': ['en-in', 'english (india)', 'indian english']
    };
    const keywords = keywordsByLang[normShort] || [];
    matched = voices.find(v => {
        const name = (v.name || '').toLowerCase();
        return keywords.some(kw => name.includes(kw));
    });
    if (matched) return matched;

    // 4. Fallback for English: any English voice
    if (normShort === 'en') {
        matched = voices.find(v => v.lang && v.lang.toLowerCase().startsWith('en'));
        if (matched) return matched;
    }

    return null;
}

// ======================================================
// SPEECH SYNTHESIS PLAYBACK CONTROLLER
// ======================================================

// Active speech synthesis state & queue management
let speechState = 'idle'; // 'idle' | 'speaking' | 'paused'
let speechQueue = [];
let currentChunkIndex = 0;
let currentSpeechLang = 'en-IN';
let currentSpeechVoice = null;
let activeSpeechUtterance = null;
let chromeKeepAliveTimer = null;

// Split text into coherent sentences/chunks to fix Chrome/Edge ~15s cutoff bug
function splitTextIntoSentences(text) {
    if (!text) return [];
    // Match sentences ending with ., !, ?, । or newline, or remainder of string
    const rawChunks = text.match(/[^.!?।\n]+[.!?।\n]+|[^.!?।\n]+$/g) || [text];
    const chunks = [];
    for (let chunk of rawChunks) {
        let trimmed = chunk.trim();
        if (!trimmed) continue;
        // If a single chunk is unusually long (>180 chars), split further by commas, semicolons, colons
        if (trimmed.length > 180) {
            const subChunks = trimmed.match(/[^,;:]+[,;:]+|[^,;:]+$/g) || [trimmed];
            for (let sub of subChunks) {
                let subTrim = sub.trim();
                if (subTrim) chunks.push(subTrim);
            }
        } else {
            chunks.push(trimmed);
        }
    }
    return chunks;
}

// Update the playback UI controls on result.html based on state
function updateSpeechUI() {
    const btnSpeak = document.getElementById('btnSpeak');
    const ttsControls = document.getElementById('ttsControls');
    const btnPauseResume = document.getElementById('btnPauseResume');
    const pauseResumeIcon = document.getElementById('pauseResumeIcon');
    const pauseResumeText = document.getElementById('pauseResumeText');
    const stopSpeakText = document.getElementById('stopSpeakText');
    const btnStopSpeak = document.getElementById('btnStopSpeak');

    if (!btnSpeak && !ttsControls) return;

    const lang = (typeof currentLanguage === 'string' && ['en', 'kn', 'hi'].includes(currentLanguage))
        ? currentLanguage
        : 'en';

    const i18n = {
        en: { pause: "Pause", resume: "Resume", stop: "Stop", listen: "🔊 Listen" },
        kn: { pause: "ವಿರಾಮ", resume: "ಮುಂದುವರಿಸಿ", stop: "ನಿಲ್ಲಿಸಿ", listen: "🔊 ಕೇಳಿ" },
        hi: { pause: "रोकें", resume: "जारी रखें", stop: "बंद करें", listen: "🔊 सुनें" }
    };
    const labels = i18n[lang] || i18n.en;

    if (stopSpeakText) {
        stopSpeakText.textContent = labels.stop;
    }
    if (btnStopSpeak) {
        btnStopSpeak.setAttribute('aria-label', `${labels.stop} speech`);
        btnStopSpeak.title = labels.stop;
    }

    if (speechState === 'speaking') {
        if (btnSpeak) btnSpeak.style.display = 'none';
        if (ttsControls) ttsControls.style.display = 'inline-flex';
        if (pauseResumeIcon) pauseResumeIcon.textContent = '⏸';
        if (pauseResumeText) pauseResumeText.textContent = labels.pause;
        if (btnPauseResume) {
            btnPauseResume.setAttribute('aria-label', `${labels.pause} speech`);
            btnPauseResume.title = labels.pause;
            btnPauseResume.classList.add('is-speaking');
            btnPauseResume.classList.remove('is-paused');
        }
    } else if (speechState === 'paused') {
        if (btnSpeak) btnSpeak.style.display = 'none';
        if (ttsControls) ttsControls.style.display = 'inline-flex';
        if (pauseResumeIcon) pauseResumeIcon.textContent = '▶';
        if (pauseResumeText) pauseResumeText.textContent = labels.resume;
        if (btnPauseResume) {
            btnPauseResume.setAttribute('aria-label', `${labels.resume} speech`);
            btnPauseResume.title = labels.resume;
            btnPauseResume.classList.remove('is-speaking');
            btnPauseResume.classList.add('is-paused');
        }
    } else { // idle
        if (btnSpeak) {
            btnSpeak.style.display = 'inline-flex';
            if (translationDB && translationDB[lang] && translationDB[lang]["btn-speak"]) {
                btnSpeak.textContent = translationDB[lang]["btn-speak"];
            } else {
                btnSpeak.textContent = labels.listen;
            }
        }
        if (ttsControls) ttsControls.style.display = 'none';
        if (btnPauseResume) {
            btnPauseResume.classList.remove('is-speaking', 'is-paused');
        }
    }
}

// Play the chunk at currentChunkIndex
function playCurrentSpeechChunk() {
    if (speechState !== 'speaking') return;

    if (currentChunkIndex >= speechQueue.length) {
        // Natural end of queue
        stopSpeech();
        return;
    }

    const chunkText = speechQueue[currentChunkIndex];
    const utterance = new SpeechSynthesisUtterance(chunkText);
    utterance.lang = currentSpeechLang;
    if (currentSpeechVoice) {
        utterance.voice = currentSpeechVoice;
    }
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    activeSpeechUtterance = utterance;

    utterance.onend = () => {
        if (speechState === 'speaking') {
            currentChunkIndex++;
            playCurrentSpeechChunk();
        }
    };

    utterance.onerror = (e) => {
        if (speechState === 'idle') return;
        if (e.error === 'interrupted' || e.error === 'canceled') return;
        console.warn("Speech chunk warning:", e);
        if (speechState === 'speaking') {
            currentChunkIndex++;
            playCurrentSpeechChunk();
        }
    };

    // Chromium keep-alive ping for long utterances
    if (chromeKeepAliveTimer) {
        clearInterval(chromeKeepAliveTimer);
    }
    chromeKeepAliveTimer = setInterval(() => {
        if (!('speechSynthesis' in window) || speechState !== 'speaking') {
            clearInterval(chromeKeepAliveTimer);
            chromeKeepAliveTimer = null;
        } else if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
            window.speechSynthesis.pause();
            window.speechSynthesis.resume();
        }
    }, 10000);

    window.speechSynthesis.speak(utterance);
}

// Speech synthesis - Speak diagnosed results and chatbot messages aloud
function speakText(textId) {
    if (!('speechSynthesis' in window)) {
        alert("Speech synthesis not supported in this browser.");
        return;
    }

    // Always stop and reset prior speech before starting a new run
    stopSpeech();

    // 1. Get the current selected language from the selector or application state
    const langSelector = document.getElementById('langSelect') || document.querySelector('.lang-selector');
    const selectedLang = (langSelector && langSelector.value && ['en', 'kn', 'hi'].includes(langSelector.value))
        ? langSelector.value
        : (typeof currentLanguage === 'string' && ['en', 'kn', 'hi'].includes(currentLanguage) ? currentLanguage : 'en');

    // Language mapping:
    // en -> en-IN
    // kn -> kn-IN
    // hi -> hi-IN
    const languageMap = {
        en: "en-IN",
        kn: "kn-IN",
        hi: "hi-IN"
    };
    currentSpeechLang = languageMap[selectedLang] || "en-IN";

    // 2. Get the text currently displayed on the screen
    let text = "";
    const el = document.getElementById(textId);
    if (el) {
        text = el.innerText || el.textContent || "";
    } else if (typeof textId === 'string') {
        text = textId;
    }

    // When speaking the crop diagnosis content on result page, prepend disease name & severity
    if (textId === 'diagnosisContent') {
        const diseaseLabel = document.getElementById('diseaseLabel');
        const diagTitle = document.getElementById('diagTitle');
        const severityBadge = document.getElementById('severityBadge');
        if (diseaseLabel && diseaseLabel.innerText && diseaseLabel.innerText.trim()) {
            const title = (diagTitle && diagTitle.innerText.trim()) ? diagTitle.innerText.trim() + ": " : "";
            const sev = (severityBadge && severityBadge.innerText.trim()) ? " (" + severityBadge.innerText.trim() + ")." : ".";
            text = title + diseaseLabel.innerText.trim() + sev + " " + text;
        }
    }

    // Clean emojis & formatting so TTS pronounces words cleanly in Kannada, Hindi, and English
    text = text
        .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
        .replace(/[*_#`~]/g, '')
        .replace(/\s+/g, ' ')
        .trim();

    if (!text) return;

    // 3. Select matching voice
    let voices = window.speechSynthesis.getVoices() || [];
    if (voices.length === 0 && systemVoices.length > 0) {
        voices = systemVoices;
    }

    const langCode = selectedLang.toLowerCase();
    currentSpeechVoice = findVoiceForLanguage(currentSpeechLang, selectedLang);

    // DO NOT select an English voice when Kannada or Hindi is selected
    if (currentSpeechVoice && (langCode === 'kn' || langCode === 'hi')) {
        const isVoiceEnglish = currentSpeechVoice.lang && currentSpeechVoice.lang.toLowerCase().startsWith('en');
        if (isVoiceEnglish) {
            currentSpeechVoice = null;
        }
    }

    // If Kannada or Hindi voice is NOT available in the browser:
    // Do NOT silently use an English voice. Detect this clearly and show user-friendly notice.
    if (!currentSpeechVoice && (langCode === 'kn' || langCode === 'hi')) {
        const langNames = {
            'kn': 'Kannada',
            'hi': 'Hindi'
        };
        const langName = langNames[langCode] || selectedLang.toUpperCase();
        showTTSVoiceNotice(`A ${langName} speech voice is unavailable in this browser.`);
        return;
    }

    // 4. Split into sentence chunks to prevent Chrome/Edge cutoff bug
    speechQueue = splitTextIntoSentences(text);
    if (speechQueue.length === 0) return;

    currentChunkIndex = 0;
    speechState = 'speaking';
    updateSpeechUI();

    playCurrentSpeechChunk();
}

// Toggle Pause / Resume
function togglePauseResumeSpeech() {
    if (!('speechSynthesis' in window)) return;

    if (speechState === 'speaking') {
        speechState = 'paused';
        window.speechSynthesis.pause();
        updateSpeechUI();
    } else if (speechState === 'paused') {
        speechState = 'speaking';
        updateSpeechUI();
        if (window.speechSynthesis.paused) {
            window.speechSynthesis.resume();
        }
        // Fallback for Chromium if resume hangs or chunk completed before pause took effect
        setTimeout(() => {
            if (speechState === 'speaking' && !window.speechSynthesis.speaking) {
                playCurrentSpeechChunk();
            }
        }, 150);
    }
}

// Stop speech and reset to idle
function stopSpeech() {
    speechState = 'idle';
    if (chromeKeepAliveTimer) {
        clearInterval(chromeKeepAliveTimer);
        chromeKeepAliveTimer = null;
    }
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
    speechQueue = [];
    currentChunkIndex = 0;
    activeSpeechUtterance = null;
    updateSpeechUI();
}

// Navigation & window cleanup listeners
window.addEventListener('beforeunload', () => stopSpeech());
window.addEventListener('pagehide', () => stopSpeech());

// Speech recognition - Voice inputs for floating chatbot
function startVoiceInput() {
    if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        const languageMap = {
            en: "en-IN",
            kn: "kn-IN",
            hi: "hi-IN"
        };
        const selectedLang = getCurrentSelectedLanguage();
        recognition.lang = languageMap[selectedLang] || 'en-IN';
        
        const chatInput = document.getElementById('chatInput');
        if (!chatInput) return;
        
        chatInput.placeholder = "Listening...";
        recognition.start();
        
        recognition.onresult = function(event) {
            const voiceText = event.results[0][0].transcript;
            chatInput.value = voiceText;
            chatInput.placeholder = translationDB[selectedLang] ? translationDB[selectedLang]["chat-placeholder"] : "Ask a farming question...";
            sendChat();
        };
        
        recognition.onerror = function() {
            chatInput.placeholder = translationDB[selectedLang] ? translationDB[selectedLang]["chat-placeholder"] : "Ask a farming question...";
        };
    } else {
        alert("Speech recognition is not supported in this browser.");
    }
}

// Switch Dashboard Navigation Tabs
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    const activeBtn = document.querySelector(`[onclick="switchTab('${tabId}')"]`);
    if (activeBtn) activeBtn.classList.add('active');
    
    const activeContent = document.getElementById(tabId);
    if (activeContent) activeContent.classList.add('active');
    
    if (tabId === 'gps_mapping' && !mapInitialized) {
        initializeMap();
    }
}

// Floating Chatbot functionality
function toggleChat() {
    const chatWin = document.getElementById('chatWindow');
    if (chatWin) {
        chatWin.classList.toggle('show');
        const msgs = document.getElementById('chatMessages');
        if (msgs && msgs.children.length === 0) {
            let greeting = "Hello, I am your Smart Farming Assistant! 🌱 How can I help you manage your crop health today?";
            if (currentLanguage === 'kn') {
                greeting = "ನಮಸ್ಕಾರ, ನಾನು ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಸಹಾಯಕ! 🌱 ಇಂದು ನಿಮ್ಮ ಬೆಳೆ ಆರೋಗ್ಯವನ್ನು ನಿರ್ವಹಿಸಲು ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?";
            } else if (currentLanguage === 'hi') {
                greeting = "नमस्ते, मैं आपका स्मार्ट कृषि सहायक हूँ! 🌱 आज मैं आपकी फसल के स्वास्थ्य को प्रबंधित करने में कैसे मदद कर सकता हूँ?";
            }
            appendMessage(greeting, 'bot');
        }
    }
}

function appendMessage(text, type) {
    const msgs = document.getElementById('chatMessages');
    if (!msgs) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${type}`;
    if (type === 'bot') {
        msgDiv.innerHTML = formatBotMessage(text);
    } else {
        msgDiv.textContent = text;
    }
    msgs.appendChild(msgDiv);
    msgs.scrollTop = msgs.scrollHeight;
}

let consoleChatHistory = [];
let widgetChatHistory = [];

function getActiveScanContext() {
    if (typeof window.activeScan === 'string' && window.activeScan.trim()) {
        return window.activeScan.trim();
    }
    const inputScan = document.getElementById('activeScanValue');
    if (inputScan && inputScan.value && inputScan.value.trim()) {
        return inputScan.value.trim();
    }
    const diseaseEl = document.getElementById('activeScanDisease');
    if (diseaseEl && diseaseEl.textContent.trim()) {
        const confEl = document.getElementById('activeScanConfidence') || diseaseEl.nextElementSibling;
        const confText = confEl ? confEl.textContent.trim() : '';
        return confText ? `${diseaseEl.textContent.trim()} ${confText}` : diseaseEl.textContent.trim();
    }
    return "Tomato - Late blight 43%";
}

function sendChat() {
    const input = document.getElementById('chatInput');
    if (!input) return;
    const query = input.value.trim();
    if (query === "") return;
    
    appendMessage(query, 'user');
    input.value = "";
    
    const activeScan = getActiveScanContext();
    const historyPayload = widgetChatHistory.slice(-5);

    setTimeout(() => {
        fetch('/chat_api', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: query,
                lang: currentLanguage,
                activeScan: activeScan,
                active_scan: activeScan,
                chat_history: historyPayload,
                chatHistory: historyPayload
            })
        })
        .then(res => res.json())
        .then(data => {
            appendMessage(data.response, 'bot');
            widgetChatHistory.push({role: "user", content: query});
            widgetChatHistory.push({role: "assistant", content: data.response});
            if (widgetChatHistory.length > 20) {
                widgetChatHistory = widgetChatHistory.slice(-20);
            }
            if (data.lang && data.lang !== currentLanguage) {
                setLanguage(data.lang);
            }
            if (localStorage.getItem('bot_auto_speech') === 'true') {
                speakText(data.response);
            }
        })
        .catch(err => {
            let botReply = getLocalBotReply(query);
            appendMessage(botReply, 'bot');
            widgetChatHistory.push({role: "user", content: query});
            widgetChatHistory.push({role: "assistant", content: botReply});
        });
    }, 300);
}

// Full page AI assistant Chat Console
function sendConsoleChat() {
    const input = document.getElementById('consoleChatInput');
    if (!input) return;
    const query = input.value.trim();
    if (query === "") return;

    appendConsoleMessage(query, 'user');
    input.value = "";

    const activeScan = getActiveScanContext();
    const historyPayload = consoleChatHistory.slice(-5);

    setTimeout(() => {
        fetch('/chat_api', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: query,
                lang: currentLanguage,
                activeScan: activeScan,
                active_scan: activeScan,
                chat_history: historyPayload,
                chatHistory: historyPayload
            })
        })
        .then(res => res.json())
        .then(data => {
            appendConsoleMessage(data.response, 'bot');
            consoleChatHistory.push({role: "user", content: query});
            consoleChatHistory.push({role: "assistant", content: data.response});
            if (consoleChatHistory.length > 20) {
                consoleChatHistory = consoleChatHistory.slice(-20);
            }
            if (data.lang && data.lang !== currentLanguage) {
                setLanguage(data.lang);
            }
            if (localStorage.getItem('bot_auto_speech') === 'true') {
                speakText(data.response);
            }
        })
        .catch(err => {
            let botReply = getLocalBotReply(query);
            appendConsoleMessage(botReply, 'bot');
            consoleChatHistory.push({role: "user", content: query});
            consoleChatHistory.push({role: "assistant", content: botReply});
        });
    }, 300);
}

function appendConsoleMessage(text, type) {
    const msgs = document.getElementById('consoleChatMessages');
    if (!msgs) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${type}`;
    if (type === 'bot') {
        msgDiv.innerHTML = formatBotMessage(text);
    } else {
        msgDiv.textContent = text;
    }
    msgs.appendChild(msgDiv);
    msgs.scrollTop = msgs.scrollHeight;
}

function askConsoleSuggested(question) {
    const input = document.getElementById('consoleChatInput');
    if (input) {
        input.value = question;
        sendConsoleChat();
    }
}

// Fallback offline responses in friendly personality
function getLocalBotReply(q) {
    q = q.toLowerCase();
    
    if (currentLanguage === 'kn') {
        if (q.includes('ಹಳದಿ') || q.includes('ಎಲೆ')) {
            return "ಚಿಂತಿಸಬೇಡಿ 🌱 ಎಲೆಗಳು ಹಳದಿಯಾಗಲು ನೀರು ಹೆಚ್ಚಾಗಿರುವುದು ಅಥವಾ ಸಾರಜನಕದ ಕೊರತೆ ಕಾರಣವಾಗಿರಬಹುದು. ಮಣ್ಣು ಒಣಗುವವರೆಗೆ ನೀರು ಕೊಡುವುದನ್ನು ನಿಲ್ಲಿಸಿ ಮತ್ತು ಸ್ವಲ್ಪ ಕಾಂಪೋಸ್ಟ್ ಗೊಬ್ಬರ ಹಾಕಿ.";
        }
        if (q.includes('ಕಲೆ') || q.includes('ರೋಗ')) {
            return "ಎಲೆಗಳ ಮೇಲಿನ ಕಪ್ಪು ಕಲೆಗಳು ಶಿಲೀಂಧ್ರ ರೋಗವಾಗಿರಬಹುದು. ಕೆಳಗಿನ ರೋಗಪೀಡಿತ ಎಲೆಗಳನ್ನು ಕಿತ್ತುಹಾಕಿ ಮತ್ತು ಬೇವಿನ ಎಣ್ಣೆ ದ್ರಾವಣವನ್ನು ಸಿಂಪಡಿಸಿ.";
        }
        return "ನಾನು ನಿಮ್ಮ ಕೃಷಿ ಸಹಾಯಕ್ಕೆ ಸದಾ ಸಿದ್ಧನಾಗಿದ್ದೇನೆ 🌱 ರೋಗದ ನಿಖರ ಪತ್ತೆಗೆ 'Detect Disease' ನಲ್ಲಿ ಎಲೆಯ ಚಿತ್ರವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.";
    }
    
    if (currentLanguage === 'hi') {
        if (q.includes('पीली') || q.includes('पत्ती')) {
            return "चिंता न करें 🌱 पत्तियों का पीला पड़ना अधिक पानी या नाइट्रोजन की कमी हो सकता है। ऊपरी मिट्टी सूखने तक पानी न दें और जैविक खाद डालें।";
        }
        return "मैं आपकी सहायता के लिए तैयार हूँ 🌱 कृपया 'रोग पहचान' में पत्ती की फोटो अपलोड करें ताकि हम सटीक समाधान निकाल सकें।";
    }
    
    return "Don't worry, we can look into this step by step. 🌱 To identify the exact issue, please upload a clear leaf photo in 'Detect Disease'!";
}

// Geolocation to load Weather-based Disease Risk
function loadWeatherAlerts() {
    const weatherCard = document.getElementById('weatherCard');
    if (!weatherCard) return;

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            
            fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=relativehumidity_2m`)
            .then(res => res.json())
            .then(data => {
                const temp = data.current_weather.temperature;
                const wind = data.current_weather.windspeed;
                const time = new Date().getHours();
                const humidity = data.hourly ? data.hourly.relativehumidity_2m[time] || 65 : 65;
                
                let risk = "Low Risk";
                let color = "#047857";
                let prediction = "Weather conditions are optimal. Late Blight spread risk is low. Maintain regular monitoring.";
                
                if (humidity > 70 && temp >= 17 && temp <= 27) {
                    risk = "High Risk";
                    color = "#b91c1c";
                    prediction = "WARNING: Warm, highly humid conditions detected. Fungal spore germination rates are maximum. Protect Tomato and Potato crops immediately.";
                } else if (humidity > 55 || (temp > 15 && temp < 30)) {
                    risk = "Moderate Risk";
                    color = "#b25e00";
                    prediction = "MODERATE ALERT: Spore spreading is moderate. Avoid overhead sprinkler irrigation to reduce moisture accumulation on leaves.";
                }
                
                weatherCard.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3>⛅ Weather-Based Disease Risk Profile</h3>
                        <span class="badge" style="background:${color}; color:#fff; padding:6px 14px; font-weight:700;">${risk}</span>
                    </div>
                    <div class="grid-3" style="margin-top:20px;">
                        <div class="stat-card" style="border-left-color:#3b82f6;">
                            <span class="label">Temperature</span>
                            <span class="value" style="font-size:26px;">${temp}°C</span>
                        </div>
                        <div class="stat-card" style="border-left-color:#10b981;">
                            <span class="label">Humidity</span>
                            <span class="value" style="font-size:26px;">${humidity}%</span>
                        </div>
                        <div class="stat-card" style="border-left-color:#f59e0b;">
                            <span class="label">Wind Speed</span>
                            <span class="value" style="font-size:26px;">${wind} km/h</span>
                        </div>
                    </div>
                    <p style="margin-top:20px; font-weight:500; color:var(--primary-light); background:#f0f7f3; padding:15px; border-radius:10px; border-left:4px solid ${color};">
                        📢 <strong>Forecast Spread Analysis:</strong> ${prediction}
                    </p>
                `;
            })
            .catch(err => {
                showFallbackWeather();
            });
        }, () => {
            showFallbackWeather();
        });
    } else {
        showFallbackWeather();
    }
}

function showFallbackWeather() {
    const weatherCard = document.getElementById('weatherCard');
    if (!weatherCard) return;
    weatherCard.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3>⛅ Weather-Based Disease Risk Profile</h3>
            <span class="badge badge-disease">Moderate Risk</span>
        </div>
        <p style="color:var(--text-muted); margin-top:15px;">Enable browser location access to view real-time regional weather disease warnings.</p>
        <div class="grid-3" style="margin-top:15px;">
            <div class="stat-card" style="border-left-color:#3b82f6;"><span class="label">Simulated Temp</span><span class="value" style="font-size:24px;">26.4°C</span></div>
            <div class="stat-card" style="border-left-color:#10b981;"><span class="label">Simulated Humidity</span><span class="value" style="font-size:24px;">62.0%</span></div>
            <div class="stat-card" style="border-left-color:#f59e0b;"><span class="label">Spread Factor</span><span class="value" style="font-size:24px;">Stable</span></div>
        </div>
    `;
}

// Leaflet GPS Drawing
function initializeMap() {
    if (typeof L === 'undefined') return;
    
    farmMap = L.map('farmMap').setView([12.9716, 77.5946], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(farmMap);
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(pos => {
            const uLat = pos.coords.latitude;
            const uLon = pos.coords.longitude;
            farmMap.setView([uLat, uLon], 16);
            L.marker([uLat, uLon]).addTo(farmMap).bindPopup("Current Location").openPopup();
        });
    }
    
    drawnItems = new L.FeatureGroup();
    farmMap.addLayer(drawnItems);
    
    const drawControl = new L.Control.Draw({
        edit: {
            featureGroup: drawnItems
        },
        draw: {
            polygon: {
                allowIntersection: false,
                showArea: true,
                drawError: {
                    color: '#e15656',
                    message: '<strong>Error:</strong> Boundaries cannot intersect!'
                },
                shapeOptions: {
                    color: '#2d8256'
                }
            },
            polyline: false,
            circle: false,
            marker: false,
            circlemarker: false,
            rectangle: false
        }
    });
    
    farmMap.addControl(drawControl);
    
    farmMap.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer;
        drawnItems.addLayer(layer);
        
        const latlngs = layer.getLatLngs()[0];
        const areaSqM = L.GeometryUtil.geodesicArea(latlngs);
        const acres = (areaSqM / 4046.86).toFixed(2);
        
        document.getElementById('plotAreaInput').value = acres;
        document.getElementById('plotCoordsInput').value = JSON.stringify(latlngs);
        
        alert(`Field mapped successfully! Area: ${acres} Acres. Give it a name below and save.`);
    });
    
    mapInitialized = true;
}

// Soil NPK and Crop Yield Predictor logic
function predictYield() {
    const crop = document.getElementById('soilCropSelect').value;
    const size = parseFloat(document.getElementById('soilAreaInput').value) || 1.0;
    const n = parseInt(document.getElementById('soilNInput').value) || 0;
    const p = parseInt(document.getElementById('soilPInput').value) || 0;
    const k = parseInt(document.getElementById('soilKInput').value) || 0;
    
    const resultBox = document.getElementById('yieldResultBox');
    if (!resultBox) return;
    
    let baseYieldPerAc = 2.5;
    let idealN = 80, idealP = 50, idealK = 70;
    
    if (crop === 'Potato') { baseYieldPerAc = 8.0; idealN = 120; idealP = 80; idealK = 150; }
    else if (crop === 'Tomato') { baseYieldPerAc = 12.0; idealN = 100; idealP = 60; idealK = 120; }
    else if (crop === 'Corn') { baseYieldPerAc = 3.5; idealN = 150; idealP = 60; idealK = 80; }
    else if (crop === 'Grape') { baseYieldPerAc = 6.0; idealN = 60; idealP = 40; idealK = 100; }
    
    const nRatio = Math.min(n / idealN, 1.2);
    const pRatio = Math.min(p / idealP, 1.2);
    const kRatio = Math.min(k / idealK, 1.2);
    const nutrientFactor = (nRatio + pRatio + kRatio) / 3.0;
    
    const projectedYield = (size * baseYieldPerAc * nutrientFactor).toFixed(1);
    
    let advice = "Nutrients are balanced. Keep organic matter levels high.";
    let details = [];
    if (n < idealN * 0.7) details.push("Nitrogen (N) is severely deficient. Add Ammonium Nitrate, Urea, or Composted Sheep Manure.");
    if (p < idealP * 0.7) details.push("Phosphorus (P) is low. Bone meal or rock phosphate application is highly recommended before flowering.");
    if (k < idealK * 0.7) details.push("Potassium (K) is insufficient. Apply wood ash or potash to strengthen plant immunity.");
    
    if (details.length > 0) {
        advice = "⚠️ Nutrient Deficiencies Detected:\n" + details.join("\n");
    }
    
    resultBox.innerHTML = `
        <div style="background:#f0f8f4; border-left:4px solid var(--primary-light); padding:20px; border-radius:10px; margin-top:20px;">
            <h4 style="color:var(--primary); margin-bottom:5px;">📊 Artificial Intelligence Predictions:</h4>
            <p style="font-size:24px; font-weight:800; color:var(--primary-light); margin:10px 0;">
                Projected Yield: ${projectedYield} Tonnes
            </p>
            <p style="font-size:12px; color:var(--text-muted); margin-bottom:15px;">
                (Based on average standard conditions for ${crop} across ${size} acre(s) under current soil values)
            </p>
            <p style="white-space:pre-line; font-weight:600; font-size:13.5px; color:#92400e;">
                ${advice}
            </p>
        </div>
    `;
}

// Generate PDF Diagnostic Report
function generatePDFReport() {
    window.print();
}

// Sidebar Toggle (Mobile)
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('active');
}

// Crop Guide Filter
function filterCrops(category, event) {
    document.querySelectorAll('.crop-filter-btn').forEach(btn => btn.classList.remove('active'));
    if (event) {
        event.target.classList.add('active');
    }

    document.querySelectorAll('.crop-card-item').forEach(card => {
        const cropType = card.getAttribute('data-crop-type');
        if (category === 'all' || cropType === category) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

// Crop Guide Search
function searchCrops() {
    const input = document.getElementById('cropSearchInput');
    if (!input) return;
    const query = input.value.toLowerCase();

    document.querySelectorAll('.crop-card-item').forEach(card => {
        const name = card.getAttribute('data-crop-name').toLowerCase();
        const diseases = card.getAttribute('data-crop-diseases').toLowerCase();
        const info = card.innerText.toLowerCase();

        if (name.includes(query) || diseases.includes(query) || info.includes(query)) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Read persisted language preference from selector, cookie, or localStorage
    const initialLang = getCurrentSelectedLanguage();
    currentLanguage = initialLang;
    localStorage.setItem('farmer_lang', currentLanguage);
    document.cookie = "farmer_lang=" + currentLanguage + "; path=/; max-age=31536000";

    // Sync form input and dropdown
    const formLangInput = document.getElementById('formLangInput');
    if (formLangInput) formLangInput.value = currentLanguage;

    applyTranslation();
    updateResultPageLanguage(currentLanguage);
    updateConsoleAssistant(currentLanguage);
    loadWeatherAlerts();

    // Attach submit listener to uploadForm for loading indicator and validation
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('imageInput');
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                e.preventDefault();
                alert(translationDB[currentLanguage]["error-no-image"] || "Please select an image first.");
                return false;
            }
            const btn = document.getElementById('btnAnalyze');
            if (btn) {
                btn.innerHTML = translationDB[currentLanguage]["loading-analyzing"] || "🌱 Analyzing Crop Leaf...";
                btn.style.opacity = '0.75';
            }
            const langInput = document.getElementById('formLangInput');
            if (langInput) langInput.value = currentLanguage;
        });
    }

    // Handle Enter key for floating chat
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChat();
            }
        });
    }

    // Handle Enter key for console chat
    const consoleChatInput = document.getElementById('consoleChatInput');
    if (consoleChatInput) {
        consoleChatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendConsoleChat();
            }
        });
    }

    // Cancel active speech when navigating away from result page via action buttons
    const btnScanAnother = document.getElementById('btnScanAnother');
    if (btnScanAnother) {
        btnScanAnother.addEventListener('click', () => stopSpeech());
    }
    const btnPdfReport = document.getElementById('btnPdfReport');
    if (btnPdfReport) {
        btnPdfReport.addEventListener('click', () => stopSpeech());
    }
    const btnDashboardLink = document.getElementById('btnDashboardLink');
    if (btnDashboardLink) {
        btnDashboardLink.addEventListener('click', () => stopSpeech());
    }
});