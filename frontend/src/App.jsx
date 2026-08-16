import { Navigate, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Dashboard from "./pages/Dashboard";
import Predict from "./pages/Predict";
import Personas from "./pages/Personas";
import Customers from "./pages/Customers";
import Profile from "./pages/Profile";
import "./styles/App.css";

import { useState } from "react";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  function toggleSidebar() {
    setSidebarOpen((s) => !s);
  }

  return (
    <div className="app-shell">
      <Sidebar collapsed={!sidebarOpen} />
      <div className={`app-content ${sidebarOpen ? "with-sidebar" : "collapsed-sidebar"}`}>
        <Header title="Dashboard" onToggleSidebar={toggleSidebar} />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/predict" element={<Predict />} />
            <Route path="/personas" element={<Personas />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="app-footer">
          Educational telecom analytics demo — not medical or financial advice.
        </footer>
      </div>
    </div>
  );
}
