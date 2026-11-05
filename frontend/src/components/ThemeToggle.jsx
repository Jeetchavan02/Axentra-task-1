import { useState } from "react";

import { applyTheme, currentTheme } from "../theme";

export default function ThemeToggle() {
  const [theme, setTheme] = useState(currentTheme);
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      onClick={() => {
        applyTheme(next);
        setTheme(next);
      }}
    >
      {next === "dark" ? "Dark mode" : "Light mode"}
    </button>
  );
}
