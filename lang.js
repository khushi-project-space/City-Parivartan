// ==========================
// 🌐 Language Manager
// ==========================

// Object to store translations
let translations = {};
let currentLang = "en"; // keep track of active language

// Map language codes to JSON filenames
const LANG_FILES = {
  en: "lang-en.json",
  gu: "lang-gu.json",
  hi: "lang-hi.json"
};

// Helper: get translation for key
function t(key) {
  return translations[key] || key; // fallback to key if missing
}

// Load the selected language JSON and update all elements
async function loadLanguage(lang) {
  try {
    const res = await fetch(`/static/${LANG_FILES[lang]}`);
    if (!res.ok) throw new Error("Language file not found");
    translations = await res.json();
    currentLang = lang;

    // Update navbar
    updateNavbarText();

    // Update page-specific elements
    updatePageText();

    // Re-run validation messages (if form exists)
    refreshValidationErrors();

    // 🔹 If map exists, reload issues with translated labels
    if (typeof loadIssues === "function") {
      loadIssues();
    }

    console.log(`✅ Language loaded: ${lang}`, translations);
  } catch (err) {
    console.error("❌ Error loading language file:", err);
  }
}

// ==========================
// 🔹 Navbar Text Update
// ==========================
function updateNavbarText() {
  const navMap = {
    navHome: "home",
    navReport: "report_issue",
    navExplore: "explore_issues",
    navSteps: "how_to_use",
    navStatus: "track_status",
    navLogin: "login_signup",
    navLogout: "logout"
  };

  for (let id in navMap) {
    const el = document.getElementById(id);
    if (el && translations[navMap[id]]) {
      el.textContent = translations[navMap[id]];
    }
  }
}

// ==========================
// 🔹 Page Content Update
// ==========================
function updatePageText() {
  // 1. Update normal text (labels, spans, divs, buttons, etc.)
  document.querySelectorAll("[data-key]").forEach(el => {
    const key = el.getAttribute("data-key");
    if (translations[key]) {
      el.textContent = translations[key];
    }
  });

  // 2. Update placeholders (inputs, textarea)
  document.querySelectorAll("[data-key-placeholder]").forEach(el => {
    const key = el.getAttribute("data-key-placeholder");
    if (translations[key]) {
      el.setAttribute("placeholder", translations[key]);
    }
  });

  // 3. Update values (for <input type="submit"> or buttons with value)
  document.querySelectorAll("[data-key-value]").forEach(el => {
    const key = el.getAttribute("data-key-value");
    if (translations[key]) {
      el.setAttribute("value", translations[key]);
    }
  });
}

// ==========================
// 🔹 Validation Refresh
// ==========================
function refreshValidationErrors() {
  // If form exists, re-validate current values so errors get translated
  if (document.getElementById("title")) {
    document.getElementById("title_error").textContent =
      validateTitle(document.getElementById("title").value.trim());
  }
  if (document.getElementById("description")) {
    document.getElementById("desc_error").textContent =
      validateDesc(document.getElementById("description").value.trim());
  }
  if (document.getElementById("location")) {
    document.getElementById("area_error").textContent =
      validateArea(document.getElementById("location").value.trim());
  }
}

// ==========================
// 🔹 Initialize on Page Load
// ==========================
document.addEventListener("DOMContentLoaded", () => {
  const languageSelector = document.getElementById("languageSelector");

  // Change event for dropdown
  if (languageSelector) {
    languageSelector.addEventListener("change", (e) => {
      const lang = e.target.value;
      localStorage.setItem("lang", lang);
      loadLanguage(lang);
    });
  }

  // Load saved language or fallback to English
  const savedLang = localStorage.getItem("lang") || "en";
  if (languageSelector) languageSelector.value = savedLang;
  loadLanguage(savedLang);
});
