import AdminMenu from "./AdminMenu";
import NotificationMenu from "./NotificationMenu";
import { useState, useEffect } from "react";
import { Menu, Bell, User, ChevronDown, Sun, Moon } from "lucide-react";
import theme from "../theme";

export default function Header({ title = "", onToggleSidebar }) {
  const [activeMenu, setActiveMenu] = useState(null);

  function toggleMenu(name) {
    setActiveMenu((s) => (s === name ? null : name));
  }

  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") setActiveMenu(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // theme
  const [currentTheme, setCurrentTheme] = useState(() => theme.getSavedTheme());
  useEffect(() => {
    theme.applyTheme(currentTheme);
  }, []);

  function handleToggleTheme() {
    const next = theme.toggleTheme();
    setCurrentTheme(next);
  }

  return (
    <header className="app-header">
      <div className="header-left">
        <button className="hamburger" aria-label="Toggle sidebar" onClick={onToggleSidebar}>
          <Menu />
        </button>
        <h2 className="page-title">{title}</h2>
      </div>
      <div className="header-right">
        <div className="notif-wrap">
          <button aria-label="Open notifications" className="icon-btn" onClick={() => toggleMenu("notifications")}>
            <Bell />
            <span className="badge">3</span>
          </button>
          <NotificationMenu open={activeMenu === "notifications"} onClose={() => setActiveMenu(null)} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button className="icon-btn" aria-label="Toggle theme" onClick={handleToggleTheme}>
            {currentTheme === "dark" ? <Sun /> : <Moon />}
          </button>
        </div>
        <div className="profile-wrap">
          <button className="profile-btn" onClick={() => toggleMenu("admin")} aria-label="Open admin menu" aria-expanded={activeMenu === "admin"}>
            <div className="avatar" style={{ width: 32, height: 32, borderRadius: 999, background: '#eef7f8', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginRight: 8 }}><User size={16} /></div>
            <span className="profile-name">Admin</span>
            <ChevronDown className={`chev ${activeMenu === "admin" ? "open" : ""}`} />
          </button>
          <AdminMenu open={activeMenu === "admin"} onClose={() => setActiveMenu(null)} />
        </div>
      </div>
    </header>
  );
}
