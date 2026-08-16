import { NavLink, useNavigate } from "react-router-dom";
import { FiHome as Home, FiUsers as Users, FiTarget as Target, FiFileText as FileText } from "react-icons/fi";
import { User as LucideUser, LogOut as LucideLogOut } from "lucide-react";

export default function Sidebar({ collapsed = false, onToggle }) {
  const navigate = useNavigate();
  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-top">
        <div className="brand-mark">TCP</div>
        {!collapsed && (
          <div className="brand-text">
            <div className="brand-title">Telecom Churn Profiler</div>
            <div className="brand-sub">Drive Discovery &amp; Personas</div>
          </div>
        )}
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
          <Home className="nav-icon" />
          {!collapsed && <span className="nav-label">Dashboard</span>}
        </NavLink>
        <NavLink to="/predict" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
          <Target className="nav-icon" />
          {!collapsed && <span className="nav-label">Predict</span>}
        </NavLink>
        <NavLink to="/personas" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
          <Users className="nav-icon" />
          {!collapsed && <span className="nav-label">Personas</span>}
        </NavLink>
        <NavLink to="/customers" className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}>
          <FileText className="nav-icon" />
          {!collapsed && <span className="nav-label">Customers</span>}
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <div className="avatar" aria-hidden="false" aria-label="User avatar">
          <LucideUser size={20} />
        </div>
        {!collapsed && (
          <>
            <div className="user-info">
              <div className="user-name">Admin User</div>
              <div className="user-email">admin@example.com</div>
            </div>
          </>
        )}
      </div>
    </aside>
  );
}
