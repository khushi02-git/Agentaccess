import { useState } from "react";
import { ChevronDown, Terminal, ShieldAlert, UserCog, Power, Gauge } from "lucide-react";
import SearchInput from "../components/SearchInput";
import FilterSelect from "../components/FilterSelect";
import StatusBadge from "../components/StatusBadge";
import { Pagination } from "../components/ui/pagination";
import { auditEvents } from "../data/auditEvents";
import { violations } from "../data/violations";
import { formatDateTime } from "../lib/utils";

const PAGE_SIZE = 8;
const violationByLog = Object.fromEntries(violations.map((v) => [v.logId, v]));

const typeIcons = {
  query: Terminal,
  violation: ShieldAlert,
  profile: UserCog,
  agent: Power,
  resource: Gauge,
};

const dotStyles = {
  success: "bg-primary",
  blocked: "bg-white",
  failed: "border border-muted-foreground bg-black",
  info: "border border-primary bg-black",
  warning: "border border-white bg-black",
};

function Detail({ label, children }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-0.5 text-sm">{children}</div>
    </div>
  );
}

export default function AuditTrail() {
  const [search, setSearch] = useState("");
  const [eventType, setEventType] = useState("all");
  const [page, setPage] = useState(1);
  const [openId, setOpenId] = useState(null);

  const reset = (setter) => (value) => {
    setter(value);
    setPage(1);
  };

  const filtered = auditEvents.filter(
    (e) =>
      (eventType === "all" || e.eventType === eventType) &&
      `${e.title} ${e.detail} ${e.reason ?? ""} ${e.profile ?? ""} ${e.eventType}`
        .toLowerCase()
        .includes(search.toLowerCase())
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const rows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Audit Trail</h2>

      <div className="flex flex-wrap items-center gap-3">
        <SearchInput value={search} onChange={reset(setSearch)} placeholder="Search audit events" />
        <FilterSelect
          label="event types"
          value={eventType}
          onChange={reset(setEventType)}
          options={["all", "query", "violation", "profile", "agent", "resource"]}
        />
      </div>

      {rows.length === 0 ? (
        <div className="rounded-lg border border-border bg-card px-5 py-10 text-center text-sm text-muted-foreground">
          No audit events match your filters.
        </div>
      ) : (
        <ol className="relative ml-3 border-l border-border">
          {rows.map((e) => {
            const open = openId === e.id;
            const Icon = typeIcons[e.eventType];
            const violation = e.eventType === "query" ? violationByLog[e.ref] : null;
            return (
              <li key={e.id} className="relative mb-4 ml-6">
                <span
                  className={`absolute -left-[31px] top-5 h-3 w-3 rounded-full ${dotStyles[e.outcome] ?? dotStyles.failed}`}
                />
                <button
                  onClick={() => setOpenId(open ? null : e.id)}
                  className="w-full rounded-lg border border-border bg-card p-4 text-left transition-colors hover:border-primary/40"
                >
                  <div className="flex flex-wrap items-center gap-3">
                    <Icon className="h-4 w-4 shrink-0 text-primary" />
                    <span className="block text-sm font-medium first-letter:uppercase">{e.title}</span>
                    <StatusBadge status={e.outcome} />
                    <span className="text-xs text-muted-foreground">{formatDateTime(e.timestamp)}</span>
                    {e.profile && <span className="text-xs text-muted-foreground">{e.profile}</span>}
                    <ChevronDown
                      className={`ml-auto h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
                    />
                  </div>
                  <div className="mt-2 truncate font-mono text-xs text-muted-foreground">{e.detail}</div>

                  {open && (
                    <div className="mt-4 grid gap-4 border-t border-border pt-4 sm:grid-cols-2">
                      <Detail label="Event ID">{e.id}</Detail>
                      <Detail label="Event type"><span className="capitalize">{e.eventType}</span></Detail>
                      <Detail label="Profile">{e.profile ?? "—"}</Detail>
                      <Detail label="Timestamp (UTC)">{e.timestamp}</Detail>
                      <Detail label="Reason">{e.reason ?? "—"}</Detail>
                      <Detail label="Linked record">
                        {e.ref ? (violation ? `${e.ref} → ${violation.id}` : e.ref) : "None"}
                      </Detail>
                      <div className="sm:col-span-2">
                        <div className="text-xs text-muted-foreground">Details</div>
                        <pre className="mt-1 whitespace-pre-wrap break-all rounded-md border border-border bg-black p-3 font-mono text-xs">
                          {e.detail}
                        </pre>
                      </div>
                    </div>
                  )}
                </button>
              </li>
            );
          })}
        </ol>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs text-muted-foreground">{filtered.length} events</span>
        <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
      </div>
    </div>
  );
}