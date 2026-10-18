import { useEffect, useMemo, useState } from "react";
import SearchInput from "../components/SearchInput";
import FilterSelect from "../components/FilterSelect";
import { Pagination } from "../components/ui/pagination";
import { fetchAuditEvents } from "../lib/api";
import { formatDateTime } from "../lib/utils";

const PAGE_SIZE = 10;

function formatDetails(details) {
  return JSON.stringify(details);
}

export default function Logs() {
  const [events, setEvents] = useState([]);
  const [search, setSearch] = useState("");
  const [eventType, setEventType] = useState("all");
  const [page, setPage] = useState(1);
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
    const searchable = `${category} ${item.event} ${item.action ?? ""} ${item.status ?? ""} ${item.agent_id ?? ""} ${item.role ?? ""} ${item.message ?? ""} ${item.query ?? ""} ${formatDetails(item.details)}`
      .toLowerCase();
    return (
      (eventType === "all" || category === eventType) &&
      searchable.includes(search.toLowerCase())
    );
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const rows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const start = filtered.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const end = Math.min(page * PAGE_SIZE, filtered.length);
  const reset = (setter) => (value) => {
    setter(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Logs</h2>
      <p className="text-xs text-muted-foreground">
        Live OS monitoring and AgentAccess backend audit/security events.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <SearchInput
          value={search}
          onChange={reset(setSearch)}
          placeholder="Search audit events"
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

      {!loading && !error && events.length > 0 && (
        <div className="rounded-lg border border-border bg-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="border-b border-border">
                  <th className="px-5 py-2 font-medium">Time</th>
                  <th className="px-5 py-2 font-medium">Type</th>
                  <th className="px-5 py-2 font-medium">Action</th>
                  <th className="px-5 py-2 font-medium">Status</th>
                  <th className="px-5 py-2 font-medium">Message / reason</th>
                  <th className="px-5 py-2 font-medium">Query</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rows.map((item) => (
                  <tr key={`${item.source ?? "OS"}-${item.id}`}>
                    <td className="whitespace-nowrap px-5 py-3 text-xs text-muted-foreground">
                      {formatDateTime(item.timestamp)}
                    </td>
                    <td className="px-5 py-3 font-medium">
                      {item.source === "OS" ? `OS · ${item.event}` : item.event_type}
                    </td>
                    <td className="px-5 py-3">{item.action ?? "—"}</td>
                    <td className="px-5 py-3">{item.status ?? "—"}</td>
                    <td className="max-w-sm break-words px-5 py-3 text-xs text-muted-foreground">
                      {item.message ?? item.details?.reason ?? formatDetails(item.details)}
                      {item.agent_id != null && ` · Agent ${item.agent_id}`}
                      {item.role && ` · ${item.role}`}
                      {item.request_id != null && ` · Request ${item.request_id}`}
                    </td>
                    <td className="max-w-md break-all px-5 py-3 font-mono text-xs">
                      {item.query ?? "—"}
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-5 py-10 text-center text-sm text-muted-foreground">
                      No backend events match your filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-5 py-3">
            <span className="text-xs text-muted-foreground">
              Showing {start}–{end} of {filtered.length}
            </span>
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </div>
        </div>
      )}
    </div>
  );
}
