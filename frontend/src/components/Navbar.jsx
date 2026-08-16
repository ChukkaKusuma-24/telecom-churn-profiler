import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-brand">
        <span className="brand-mark" aria-hidden="true" />
        <div>
          <div className="brand-title">Telecom Churn Profiler</div>
          <div className="brand-sub">Driver Discovery &amp; Personas</div>
        </div>
      </div>
      <nav className="navbar-links">
        <NavLink to="/" end>
          Dashboard
        </NavLink>
        <NavLink to="/predict">Predict</NavLink>
        <NavLink to="/personas">Personas</NavLink>
        <NavLink to="/customers">Customers</NavLink>
      </nav>
    </header>
  );
}
