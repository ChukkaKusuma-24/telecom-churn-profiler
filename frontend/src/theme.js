const THEME_KEY = "pref_theme";

export function getSavedTheme() {
  try {
    const v = localStorage.getItem(THEME_KEY);
    if (v === "light" || v === "dark") return v;
  } catch {}
  // system preference as default
  if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
  return "light";
}

export function applyTheme(theme) {
  try {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
    }
    localStorage.setItem(THEME_KEY, theme);
  } catch {}
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || getSavedTheme();
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  return next;
}

export default { getSavedTheme, applyTheme, toggleTheme };
