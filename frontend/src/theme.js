const KEY = "subscription-tracker-theme";

export const currentTheme = () => document.documentElement.dataset.theme;

export function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(KEY, theme);
}

/** Use the saved choice, or follow the operating system until the user picks one. */
export function initTheme() {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.theme =
    localStorage.getItem(KEY) ?? (prefersDark ? "dark" : "light");
}
