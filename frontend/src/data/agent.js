export const agent = {
  id: "agt-001",
  name: "AgentAccess AI Agent",
  status: "active", // active | idle | blocked
  lastActive: "2026-10-09T10:42:00Z",
  queriesToday: 269,
  violationsToday: 6,
};

export const permissionProfiles = [
  { id: "prf-readonly", name: "Read-only", allowed: ["SELECT"], denied: ["INSERT", "UPDATE", "DELETE", "DROP"], queriesToday: 98, violationsToday: 1 },
  { id: "prf-readwrite", name: "Read-write", allowed: ["SELECT", "INSERT", "UPDATE"], denied: ["DELETE", "DROP"], queriesToday: 137, violationsToday: 0 },
  { id: "prf-admin", name: "Admin", allowed: ["SELECT", "INSERT", "UPDATE", "DELETE"], denied: ["DROP"], queriesToday: 34, violationsToday: 5 },
];