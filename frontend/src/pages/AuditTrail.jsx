import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Activity } from "lucide-react";
import SearchInput from "../components/SearchInput";
import FilterSelect from "../components/FilterSelect";
import { Pagination } from "../components/ui/pagination";
import { fetchAuditEvents } from "../lib/api";
import { formatDateTime } from "../lib/utils";

const PAGE_SIZE = 8;

function formatDetails(details) {
  return JSON.stringify(details, null, 2);
}

export default function AuditTrail() {
  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [eventType, setEventType] = useState("all");
  const [page, setPage] = useState(1);
  const [openId, setOpenId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    fetchAuditEvents()
      .then((data) => {
        if (active) {
          setEvents(data);
          setError("");
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(requestError.message);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const eventTypes = useMemo(
    () => [
      "all",
      ...new Set(
        events.map((item) =>
          item.source === "OS" ? `OS:${item.event}` : item.event_type
        )
      ),
    ],
    [events]
  );
  const filtered = events.filter((item) => {
    const category =
      item.source === "OS" ? `OS:${item.event}` : item.event_type;
    const searchable = `${category} ${item.event} ${item.agent_id ?? ""} ${item.role ?? ""} ${item.action ?? ""} ${item.query ?? ""} ${item.status ?? ""} ${item.risk_level ?? ""} ${item.message ?? ""} ${item.request_id ?? ""} ${formatDetails(item.details)}`
      .toLowerCase();
    return (
      (eventType === "all" || category === eventType) &&
      searchable.includes(search.toLowerCase())
    );
  });
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const rows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const reset = (setter) => (value) => {
    setter(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Audit Trail</h2>
      <p className="text-xs text-muted-foreground">
        Live AgentAccess security/audit activity and OS monitoring events.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <SearchInput
          value={search}
          onChange={reset(setSearch)}
          placeholder="Search security and audit events"
        />
        <FilterSelect
          label="event types"
          value={eventType}
          onChange={reset(setEventType)}
          options={eventTypes}
        />
      </div>

      {loading && (
        <p className="text-sm text-muted-foreground">Loading audit events…</p>
      )}
      {error && (
        <p role="alert" className="rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-400">
          {error}
        </p>
      )}
      {!loading && !error && events.length === 0 && (
        <p className="rounded-lg border border-border bg-card px-5 py-10 text-center text-sm text-muted-foreground">
          No backend events are available.
        </p>
      )}

      {!loading && !error && events.length > 0 && rows.length === 0 && (
        <p className="rounded-lg border border-border bg-card px-5 py-10 text-center text-sm text-muted-foreground">
          No backend events match your filters.
        </p>
      )}

      {!loading && !error && rows.length > 0 && (
        <ol className="relative ml-3 border-l border-border">
          {rows.map((item) => {
            const eventKey = `${item.source ?? "OS"}-${item.id}`;
            const open = openId === eventKey;
            return (
              <li key={eventKey} className="relative mb-4 ml-6">
                <span className="absolute -left-[31px] top-5 h-3 w-3 rounded-full bg-primary" />
                <button
                  type="button"
                  onClick={() => setOpenId(open ? null : eventKey)}
                  className="w-full rounded-lg border border-border bg-card p-4 text-left transition-colors hover:border-primary/40"
                >
                  <div className="flex flex-wrap items-center gap-3">
                    <Activity className="h-4 w-4 shrink-0 text-primary" />
                    <span className="text-sm font-medium">
                      {item.source === "OS" ? `OS · ${item.event}` : item.event_type}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatDateTime(item.timestamp)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Agent {item.agent_id ?? "—"} · {item.role ?? "—"}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {item.status ?? "—"}
                    </span>
                    <ChevronDown
                      className={`ml-auto h-4 w-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
                    />
                  </div>

                  {open && (
                    <div className="mt-4 grid gap-4 border-t border-border pt-4 sm:grid-cols-2">
                      <div>
                        <div className="text-xs text-muted-foreground">Event ID</div>
                        <div className="mt-0.5 text-sm">{item.id}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Agent ID</div>
                        <div className="mt-0.5 text-sm">{item.agent_id ?? "—"}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Role</div>
                        <div className="mt-0.5 text-sm">{item.role ?? "—"}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Action</div>
                        <div className="mt-0.5 text-sm">{item.action ?? "—"}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Status</div>
                        <div className="mt-0.5 text-sm">{item.status ?? "—"}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Risk level</div>
                        <div className="mt-0.5 text-sm">{item.risk_level ?? "—"}</div>
                      </div>
                      <div>
                        <div className="text-xs text-muted-foreground">Request ID</div>
                        <div className="mt-0.5 text-sm">{item.request_id ?? "—"}</div>
                      </div>
                      <div className="sm:col-span-2">
                        <div className="text-xs text-muted-foreground">Query</div>
                        <pre className="mt-1 whitespace-pre-wrap break-all rounded-md border border-border bg-black p-3 font-mono text-xs">
                          {item.query ?? "—"}
                        </pre>
                      </div>
                      <div className="sm:col-span-2">
                        <div className="text-xs text-muted-foreground">Message / reason</div>
                        <div className="mt-0.5 text-sm">
                          {item.message ?? item.details?.reason ?? "—"}
                        </div>
                      </div>
                      <div className="sm:col-span-2">
                        <div className="text-xs text-muted-foreground">Details</div>
                        <pre className="mt-1 whitespace-pre-wrap break-all rounded-md border border-border bg-black p-3 font-mono text-xs">
                          {formatDetails(item.details)}
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

      {!loading && !error && events.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs text-muted-foreground">
            {filtered.length} OS events
          </span>
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </div>
      )}
    </div>
  );
}
