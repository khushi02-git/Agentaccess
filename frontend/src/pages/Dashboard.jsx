import { Database, ShieldAlert, Cpu, MemoryStick } from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import PixelCard from "../components/PixelCard";
import { agent } from "../data/agent";
import { logs } from "../data/logs";
import { systemStats } from "../data/systemStats";
import { formatTime } from "../lib/utils";

export default function Dashboard() {
  const recent = logs.slice(0, 6);

  return (
    <div className="space-y-8">
      <h2 className="pixel-font text-[16px] text-white">Dashboard</h2>

      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <PixelCard soft label="Queries today" value={agent.queriesToday} sub="All permission profiles" icon={Database} />
        <PixelCard soft danger label="Violations today" value={agent.violationsToday} sub="Blocked by validator" icon={ShieldAlert} />
        <PixelCard soft label="CPU usage" value={`${systemStats.cpuPercent}%`} sub="Host machine" icon={Cpu} />
        <PixelCard soft label="Memory usage" value={`${systemStats.memory.percent}%`} sub={`${systemStats.memory.usedGB} / ${systemStats.memory.totalGB} GB`} icon={MemoryStick} />
      </div>

      <PixelCard soft className="flush">
        <div className="border-b border-border px-5 py-3 text-sm font-medium">Recent activity</div>
        <ul className="divide-y divide-border">
          {recent.map((log) => (
            <li key={log.id} className="flex items-center gap-4 px-5 py-3">
              <span className="w-14 shrink-0 text-xs text-muted-foreground">{formatTime(log.timestamp)}</span>
              <span className="w-24 shrink-0 text-xs text-muted-foreground">{log.profile}</span>
              <span className="w-16 shrink-0 text-xs font-medium text-primary">{log.action}</span>
              <span className="min-w-0 flex-1 truncate font-mono text-xs">{log.query}</span>
              <StatusBadge status={log.decision} />
            </li>
          ))}
        </ul>
      </PixelCard>
    </div>
  );
}