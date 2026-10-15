import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import StatusBadge from "../components/StatusBadge";
import { systemStats, systemHistory, processes } from "../data/systemStats";
import PixelCard from "../components/PixelCard";

function formatUptime(seconds) {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${d}d ${h}h ${m}m`;
}



export default function SystemMonitor() {
  const { cpuPercent, memory, disk, uptimeSeconds } = systemStats;

  return (
    <div className="space-y-6">
      <h1 className="pixel-font text-[24px] text-white">System Monitor</h1>

      <div className="grid gap-8 sm:grid-cols-2 xl:grid-cols-4">
        <PixelCard
          label="CPU"
          value={`${cpuPercent}%`}
          percent={cpuPercent}
          sub="Overall utilization"
        />
        <PixelCard
          label="Memory"
          value={`${memory.percent}%`}
          percent={memory.percent}
          sub={`${memory.usedGB} / ${memory.totalGB} GB`}
        />
        <PixelCard
          label="Disk"
          value={`${disk.percent}%`}
          percent={disk.percent}
          sub={`${disk.usedGB} / ${disk.totalGB} GB`}
        />
        <PixelCard
          label="Uptime"
          value={formatUptime(uptimeSeconds)}
          sub="Since last restart"
        />
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 text-sm font-medium">CPU and memory over time</div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={systemHistory}>
              <CartesianGrid stroke="#262626" strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#a3a3a3" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} stroke="#a3a3a3" tick={{ fontSize: 12 }} unit="%" />
              <Tooltip
                contentStyle={{ background: "#0a0a0a", border: "1px solid #262626", borderRadius: 8 }}
                labelStyle={{ color: "#ffffff" }}
              />
              <Legend />
              <Line type="monotone" dataKey="cpu" name="CPU" stroke="#22c55e" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="memory" name="Memory" stroke="#ffffff" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-5 py-3 text-sm font-medium">Processes</div>
        <table className="w-full text-left text-sm">
          <thead className="text-xs text-muted-foreground">
            <tr className="border-b border-border">
              <th className="px-5 py-2 font-medium">PID</th>
              <th className="px-5 py-2 font-medium">Name</th>
              <th className="px-5 py-2 font-medium">CPU %</th>
              <th className="px-5 py-2 font-medium">Memory (MB)</th>
              <th className="px-5 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {processes.map((p) => (
              <tr key={p.pid}>
                <td className="px-5 py-3 font-mono text-xs text-muted-foreground">{p.pid}</td>
                <td className="px-5 py-3">{p.name}</td>
                <td className="px-5 py-3">{p.cpuPercent}</td>
                <td className="px-5 py-3">{p.memoryMB}</td>
                <td className="px-5 py-3">
                  <StatusBadge status={p.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}