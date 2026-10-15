import { Badge } from "./ui/8bit-badge";

const variantFor = {
  allowed: "success",
  success: "success",
  active: "success",
  running: "success",
  info: "success",
  acknowledged: "success",
  medium: "success",
  blocked: "danger",
  high: "danger",
  open: "danger",
  critical: "critical",
  warning: "warning",
  failed: "muted",
  sleeping: "muted",
  idle: "muted",
  low: "muted",
  resolved: "muted",
};

export default function StatusBadge({ status }) {
  return <Badge variant={variantFor[status] ?? "muted"}>{status}</Badge>;
}