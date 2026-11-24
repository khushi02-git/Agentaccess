import { useEffect, useState } from "react";
import { Database, ShieldAlert, Cpu, MemoryStick } from "lucide-react";
import PixelCard from "../components/PixelCard";
import { fetchSystemStats, fetchAuditEvents } from "../lib/api";
import { formatTime } from "../lib/utils";

const REFRESH_MS = 10000;

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const [s, e] = await Promise.all([fetchSystemStats(), fetchAuditEvents()]);
        if (active) { setStats(s); setEvents(e); }
      } catch {
        /* keep the last good values */
      }
    };
    refresh();
    const id = setInterval(refresh, REFRESH_MS);
    return () => { active = false; clearInterval(id); };
  }, []);

  const queries = events.filter((e) => e.event_type === "QUERY").length;
  const violations = events.filter((e) => e.status === "BLOCKED").length;
  const recent = events.slice(0, 6);

  return (
    <div className="space-y-8">
      <h2 className="pixel-font text-[16px] text-white">Dashboard</h2>

      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <PixelCard soft label="Queries" value={queries} sub="From audit log" icon={Database} />
        <PixelCard soft danger label="Violations" value={violations} sub="Blocked events" icon={ShieldAlert} />
        <PixelCard soft label="CPU usage" value={stats ? `${stats.cpu_percent}%` : "—"} sub="Host machine" icon={Cpu} />
        <PixelCard soft label="Memory usage" value={stats ? `${stats.ram.percent}%` : "—"}
          sub={stats ? `${stats.ram.used_gb} / ${stats.ram.total_gb} GB` : ""} icon={MemoryStick} />
      </div>

      <PixelCard soft className="flush">
        <div className="border-b border-border px-5 py-3 text-sm font-medium">Recent activity</div>
        <ul className="divide-y divide-border">
          {recent.map((ev) => (
            <li key={ev.id} className="flex items-center gap-4 px-5 py-3">
              <span className="w-14 shrink-0 text-xs text-muted-foreground">{formatTime(ev.timestamp)}</span>
              <span className="w-24 shrink-0 text-xs text-muted-foreground">{ev.role ?? "—"}</span>
              <span className="w-16 shrink-0 text-xs font-medium text-primary">{ev.action ?? ev.event}</span>
              <span className="min-w-0 flex-1 truncate font-mono text-xs">{ev.query ?? ev.message ?? ""}</span>
              <span className="text-xs">{ev.status ?? ""}</span>
            </li>
          ))}
        </ul>
      </PixelCard>
    </div>
  );
}