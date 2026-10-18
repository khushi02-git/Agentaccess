import { useEffect, useState } from "react";
import PixelCard from "../components/PixelCard";
import { fetchSystemStats } from "../lib/api";

const REFRESH_INTERVAL_MS = 10000;

export default function SystemMonitor() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const refresh = async () => {
      try {
        const nextStats = await fetchSystemStats();
        if (active) {
          setStats(nextStats);
          setError("");
        }
      } catch (requestError) {
        if (active) {
          setError(requestError.message);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    refresh();
    const interval = window.setInterval(refresh, REFRESH_INTERVAL_MS);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="pixel-font text-[24px] text-white">System Monitor</h1>

      {loading && !stats && (
        <p className="text-sm text-muted-foreground">Loading system metrics…</p>
      )}

      {error && (
        <p role="alert" className="rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-400">
          {stats ? `Could not refresh metrics: ${error}` : error}
        </p>
      )}

      {stats && (
        <>
          <div className="grid gap-8 sm:grid-cols-2 xl:grid-cols-3">
            <PixelCard
              label="CPU"
              value={`${stats.cpu_percent}%`}
              percent={stats.cpu_percent}
              sub="Overall utilization"
            />
            <PixelCard
              label="Memory"
              value={`${stats.ram.percent}%`}
              percent={stats.ram.percent}
              sub={`${stats.ram.used_gb} / ${stats.ram.total_gb} GB`}
            />
            <PixelCard
              label="Disk"
              value={`${stats.disk.percent}%`}
              percent={stats.disk.percent}
              sub="Used space"
            />
          </div>

          <p className="text-xs text-muted-foreground">
            Metrics sampled {new Date(stats.timestamp).toLocaleString()}
          </p>

          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border px-5 py-3 text-sm font-medium">
              Processes
            </div>
            {stats.processes.length === 0 ? (
              <p className="px-5 py-8 text-center text-sm text-muted-foreground">
                No process data is currently available.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs text-muted-foreground">
                    <tr className="border-b border-border">
                      <th className="px-5 py-2 font-medium">PID</th>
                      <th className="px-5 py-2 font-medium">Name</th>
                      <th className="px-5 py-2 font-medium">CPU %</th>
                      <th className="px-5 py-2 font-medium">Memory (MB)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {stats.processes.map((process) => (
                      <tr key={process.pid}>
                        <td className="px-5 py-3 font-mono text-xs text-muted-foreground">
                          {process.pid}
                        </td>
                        <td className="px-5 py-3">{process.name}</td>
                        <td className="px-5 py-3">{process.cpu_percent}</td>
                        <td className="px-5 py-3">{process.memory_mb}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {!loading && !stats && !error && (
        <p className="text-sm text-muted-foreground">
          System metrics are not currently available.
        </p>
      )}
    </div>
  );
}
