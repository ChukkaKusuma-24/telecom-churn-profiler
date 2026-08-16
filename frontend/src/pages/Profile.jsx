import { useEffect } from "react";
import { User } from "lucide-react";

export default function Profile() {
  useEffect(() => {
    document.title = "Profile — Telecom Churn Profiler";
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          <div style={{ width: 64, height: 64, borderRadius: 999, background: "#eef7f8", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <User size={36} />
          </div>
          <div>
            <p className="eyebrow">Profile</p>
            <h1>Admin</h1>
            <p className="muted">Application administrator</p>
          </div>
        </div>
      </div>

      <section className="panel">
        <h3>Account</h3>
        <p><strong>Name:</strong> Admin</p>
        <p><strong>Email:</strong> admin@example.com</p>
        <p><strong>Role:</strong> Administrator</p>
      </section>
    </div>
  );
}
