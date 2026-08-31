import { Moon, Sun, Languages } from "lucide-react";
import { useApp } from "../AppContext.jsx";

export default function TopBar() {
  const { theme, toggleTheme, lang, toggleLang, t } = useApp();

  return (
    <div className="topbar">
      <div className="brand">
        <span className="brand-mark"></span>
        <span className="brand-title">{t.brandTitle}</span>
      </div>

      <div className="topbar-actions">
        <span className="brand-sub">{t.brandSub}</span>
        <button className="icon-btn" onClick={toggleLang}>
          <Languages size={14} />
          {lang === "ar" ? "EN" : "AR"}
        </button>
        <button className="icon-btn" onClick={toggleTheme}>
          {theme === "light" ? <Moon size={14} /> : <Sun size={14} />}
        </button>
      </div>
    </div>
  );
}