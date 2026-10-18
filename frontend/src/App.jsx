import { Routes, Route } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Agent from "./pages/Agent";
import SystemMonitor from "./pages/SystemMonitor";
import Logs from "./pages/Logs";
import AuditTrail from "./pages/AuditTrail";
import Violations from "./pages/Violations";
import RBAC from "./pages/RBAC";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="agent" element={<Agent />} />
        <Route path="system" element={<SystemMonitor />} />
        <Route path="logs" element={<Logs />} />
        <Route path="audit" element={<AuditTrail />} />
        <Route path="violations" element={<Violations />} />
        <Route path="rbac" element={<RBAC />} />
      </Route>
    </Routes>
  );
}