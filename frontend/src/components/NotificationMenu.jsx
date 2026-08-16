import { useRef } from "react";
import useClickOutside from "../hooks/useClickOutside";
import { FiBell, FiClock, FiAlertCircle, FiCheckCircle } from "react-icons/fi";

const FALLBACK = [
  { id: 1, level: "high", title: "High churn risk detected", desc: "312 customers moved to high risk", ago: "2h" },
  { id: 2, level: "warn", title: "Contract expirations", desc: "126 contracts", ago: "1d" },
  { id: 3, level: "info", title: "Model retrained successfully", desc: "New clustering model", ago: "1 day ago" },
];

export default function NotificationMenu({ open, onClose }) {
  const ref = useRef();
  useClickOutside(ref, () => open && onClose());

  return (
    <div className={`notif-menu ${open ? "open" : ""}`} ref={ref} role="dialog">
      <div className="notif-header">
        <h4>Notifications</h4>
      </div>
      <div className="notif-list">
        {FALLBACK.map((n) => (
          <div className="notif-item" key={n.id}>
            <div className={`notif-dot ${n.level}`}></div>
            <div className="notif-body">
              <div className="notif-title">{n.title}</div>
              <div className="notif-desc">{n.desc}</div>
            </div>
            <div className="notif-time">{n.ago}</div>
          </div>
        ))}
      </div>
      <div className="notif-footer">View all →</div>
    </div>
  );
}
