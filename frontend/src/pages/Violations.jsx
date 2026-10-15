import { useState } from "react";
import { ShieldAlert } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import StatCard from "../components/StatCard";
import SearchInput from "../components/SearchInput";
import FilterSelect from "../components/FilterSelect";
import StatusBadge from "../components/StatusBadge";
import { violations as initial } from "../data/violations";
import { formatDateTime } from "../lib/utils";

const severities = ["critical", "high", "medium", "low"];
const severityRank = { critical: 0, high: 1, medium: 2, low: 3 };
const statusRank = { open: 0, acknowledged: 1, resolved: 2 };

const actions = {
  open: [
    { label: "Resolve", to: "resolved", primary: true },
    { label: "Acknowledge", to: "acknowledged" },
  ],
  acknowledged: [{ label: "Resolve", to: "resolved", primary: true }],
  resolved: [{ label: "Reopen", to: "open" }],
};

export default function Violations() {
  const [items, setItems] = useState(initial);
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("all");
  const [status, setStatus] = useState("all");

  const setItemStatus = (id, next) =>
    setItems((prev) => prev.map((v) => (v.id === id ? { ...v, status: next } : v)));

  const countBy = (s) => items.filter((v) => v.severity === s).length;
  const unresolvedBy = (s) => items.filter((v) => v.severity === s && v.status !== "resolved").length;

  const chartData = [...new Set(items.map((v) => v.type))].map((type) => ({
    type: type.replaceAll("_", " ").toLowerCase(),
    count: items.filter((v) => v.type === type).length,
  }));

  const visible = items
    .filter(
      (v) =>
        (severity === "all" || v.severity === severity) &&
        (status === "all" || v.status === status) &&
        `${v.query} ${v.rule} ${v.type} ${v.profile}`.toLowerCase().includes(search.toLowerCase())
    )
    .sort(
      (a, b) =>
        statusRank[a.status] - statusRank[b.status] ||
        severityRank[a.severity] - severityRank[b.severity] ||
        new Date(b.timestamp) - new Date(a.timestamp)
    );

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Violations</h2>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {severities.map((s) => (
          <StatCard
            key={s}
            label={s[0].toUpperCase() + s.slice(1)}
            value={countBy(s)}
            hint={`${unresolvedBy(s)} unresolved`}
            icon={ShieldAlert}
          />
        ))}
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 text-sm font-medium">Violations by type</div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid stroke="#262626" strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" allowDecimals={false} stroke="#a3a3a3" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="type" width={150} stroke="#a3a3a3" tick={{ fontSize: 12 }} />
              <Tooltip
                cursor={{ fill: "#141414" }}
                contentStyle={{ background: "#0a0a0a", border: "1px solid #262626", borderRadius: 8 }}
                labelStyle={{ color: "#ffffff" }}
              />
              <Bar dataKey="count" name="Violations" fill="#22c55e" radius={[0, 4, 4, 0]} barSize={22} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={setSearch} placeholder="Search violations" />
        <FilterSelect label="severities" value={severity} onChange={setSeverity} options={["all", ...severities]} />
        <FilterSelect label="statuses" value={status} onChange={setStatus} options={["all", "open", "acknowledged", "resolved"]} />
      </div>

      {visible.length === 0 ? (
        <div className="rounded-lg border border-border bg-card px-5 py-10 text-center text-sm text-muted-foreground">
          No violations match your filters.
        </div>
      ) : (
        <ul className="space-y-3">
          {visible.map((v) => (
            <li key={v.id} className="rounded-lg border border-border bg-card p-4">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge status={v.severity} />
                <span className="text-sm font-medium capitalize">{v.type.replaceAll("_", " ").toLowerCase()}</span>
                <span className="text-xs text-muted-foreground">
                  {v.profile} · {formatDateTime(v.timestamp)}
                </span>
                <span className="ml-auto">
                  <StatusBadge status={v.status} />
                </span>
              </div>

              <div className="mt-2 text-sm text-muted-foreground">{v.rule}</div>
              <div className="mt-2 truncate rounded-md border border-border bg-black px-3 py-2 font-mono text-xs">
                {v.query}
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                {actions[v.status].map((a) => (
                  <button
                    key={a.to}
                    onClick={() => setItemStatus(v.id, a.to)}
                    className={
                      a.primary
                        ? "h-8 rounded-md bg-primary px-3 text-xs font-medium text-black transition-opacity hover:opacity-90"
                        : "h-8 rounded-md border border-border px-3 text-xs font-medium transition-colors hover:border-primary/40"
                    }
                  >
                    {a.label}
                  </button>
                ))}
                <span className="ml-auto text-xs text-muted-foreground">
                  {v.id} · {v.logId}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}