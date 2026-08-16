import { useRef } from "react";
import useClickOutside from "../hooks/useClickOutside";
import { User, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function AdminMenu({ open, onClose }) {
  const ref = useRef();
  useClickOutside(ref, () => open && onClose());
  const navigate = useNavigate();

  function goProfile() {
    onClose();
    navigate("/profile");
  }

  function doLogout() {
    onClose();
    // No backend auth configured — provide safe UI action
    // Clear demo flags if present
    try {
      localStorage.removeItem("demo_user");
    } catch {}
    alert("No authentication configured. This is a local demo.\nDemo user state cleared.");
    navigate("/");
  }

  return (
    <div className={`admin-menu ${open ? "open" : ""}`} ref={ref} role="dialog">
      <div className="admin-top">
        <User />
        <div>
          <div className="admin-name">Admin User</div>
          <div className="admin-email">admin@example.com</div>
        </div>
      </div>
      <div className="admin-actions">
        <button className="admin-action" onClick={goProfile} aria-label="Open profile"><User /> Profile</button>
        <button className="admin-action" onClick={doLogout} aria-label="Logout"><LogOut /> Logout</button>
      </div>
    </div>
  );
}
