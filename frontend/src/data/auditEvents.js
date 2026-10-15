import { logs } from "./logs";
import { violations } from "./violations";

const queryEvents = logs.map((l) => ({
  id: `evt-${l.id}`,
  eventType: "query",
  timestamp: l.timestamp,
  title: `${l.action} query ${l.decision}`,
  detail: l.query,
  outcome: l.status,
  profile: l.profile,
  reason: l.reason,
  ref: l.id,
}));

const violationEvents = violations.map((v) => ({
  id: `evt-${v.id}`,
  eventType: "violation",
  timestamp: new Date(new Date(v.timestamp).getTime() + 1000).toISOString(),
  title: `${v.type.replaceAll("_", " ").toLowerCase()} (${v.severity})`,
  detail: v.query,
  outcome: "blocked",
  profile: v.profile,
  reason: v.rule,
  ref: v.id,
}));

const systemEvents = [
  { id: "evt-s01", eventType: "agent", timestamp: "2026-10-09T05:00:00Z", title: "Agent started", detail: "Session initialized under the Read-only profile", outcome: "info", profile: "Read-only" },
  { id: "evt-s02", eventType: "profile", timestamp: "2026-10-09T05:29:00Z", title: "Profile switched to Admin", detail: "Read-only → Admin", outcome: "info", profile: "Admin", reason: "Scheduled session cleanup" },
  { id: "evt-s03", eventType: "profile", timestamp: "2026-10-09T05:45:00Z", title: "Profile switched to Read-only", detail: "Admin → Read-only", outcome: "info", profile: "Read-only", reason: "Cleanup task finished" },
  { id: "evt-s04", eventType: "profile", timestamp: "2026-10-09T07:30:00Z", title: "Profile switched to Read-write", detail: "Read-only → Read-write", outcome: "info", profile: "Read-write", reason: "Order update task" },
  { id: "evt-s05", eventType: "resource", timestamp: "2026-10-09T07:43:40Z", title: "CPU limit exceeded", detail: "CPU usage reached 91% (limit 85%)", outcome: "warning", profile: "Read-write" },
  { id: "evt-s06", eventType: "profile", timestamp: "2026-10-09T08:10:00Z", title: "Profile switched to Read-only", detail: "Read-write → Read-only", outcome: "info", profile: "Read-only", reason: "Schema review task" },
  { id: "evt-s07", eventType: "profile", timestamp: "2026-10-09T09:10:00Z", title: "Profile switched to Read-write", detail: "Read-only → Read-write", outcome: "info", profile: "Read-write", reason: "Order maintenance task" },
  { id: "evt-s08", eventType: "profile", timestamp: "2026-10-09T09:55:00Z", title: "Profile switched to Admin", detail: "Read-write → Admin", outcome: "info", profile: "Admin", reason: "Table maintenance task" },
  { id: "evt-s09", eventType: "resource", timestamp: "2026-10-09T09:59:10Z", title: "Memory limit exceeded", detail: "Memory usage reached 88% (limit 85%)", outcome: "warning", profile: "Admin" },
  { id: "evt-s10", eventType: "agent", timestamp: "2026-10-09T09:59:30Z", title: "Agent paused", detail: "Auto-paused after 2 blocked queries within 90 seconds", outcome: "warning", profile: "Admin" },
  { id: "evt-s11", eventType: "agent", timestamp: "2026-10-09T10:28:00Z", title: "Agent resumed", detail: "Resumed by operator under the Read-only profile", outcome: "info", profile: "Read-only" },
  { id: "evt-s12", eventType: "profile", timestamp: "2026-10-09T10:30:00Z", title: "Profile switched to Read-write", detail: "Read-only → Read-write", outcome: "info", profile: "Read-write", reason: "Customer import task" },
  { id: "evt-s13", eventType: "profile", timestamp: "2026-10-09T10:35:00Z", title: "Profile switched to Read-only", detail: "Read-write → Read-only", outcome: "info", profile: "Read-only", reason: "Reporting task" },
  { id: "evt-s14", eventType: "profile", timestamp: "2026-10-09T10:41:00Z", title: "Profile switched to Read-write", detail: "Read-only → Read-write", outcome: "info", profile: "Read-write", reason: "Order sync task" },
];

export const auditEvents = [...queryEvents, ...violationEvents, ...systemEvents].sort(
  (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
);