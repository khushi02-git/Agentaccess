import { useState } from "react";
import SearchInput from "../components/SearchInput";
import FilterSelect from "../components/FilterSelect";
import StatusBadge from "../components/StatusBadge";
import { Pagination } from "../components/ui/pagination";
import { logs } from "../data/logs";
import { permissionProfiles } from "../data/agent";
import { formatDateTime } from "../lib/utils";

const PAGE_SIZE = 5;
const sorted = [...logs].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
const profileOptions = ["all", ...permissionProfiles.map((p) => p.name)];

export default function Logs() {
    const [search, setSearch] = useState("");
    const [decision, setDecision] = useState("all");
    const [profile, setProfile] = useState("all");
    const [page, setPage] = useState(1);

    const reset = (setter) => (value) => {
        setter(value);
        setPage(1);
    };

    const filtered = sorted.filter(
        (l) =>
            (decision === "all" || l.decision === decision) &&
            (profile === "all" || l.profile === profile) &&
            `${l.query} ${l.reason ?? ""} ${l.action} ${l.decision} ${l.status} ${l.profile}`
                .toLowerCase()
                .includes(search.toLowerCase())
    );

    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    const rows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
    const start = filtered.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
    const end = Math.min(page * PAGE_SIZE, filtered.length);

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold">Logs</h2>

            <div className="flex flex-wrap items-center gap-3">
                <SearchInput value={search} onChange={reset(setSearch)} placeholder="Search queries or reasons" />
                <FilterSelect label="decisions" value={decision} onChange={reset(setDecision)} options={["all", "allowed", "blocked"]} />
                <FilterSelect label="profiles" value={profile} onChange={reset(setProfile)} options={profileOptions} />
            </div>

            <div className="rounded-lg border border-border bg-card">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="text-xs text-muted-foreground">
                            <tr className="border-b border-border">
                                <th className="px-5 py-2 font-medium">Time</th>
                                <th className="px-5 py-2 font-medium">Profile</th>
                                <th className="px-5 py-2 font-medium">Action</th>
                                <th className="px-5 py-2 font-medium">Query</th>
                                <th className="px-5 py-2 font-medium">Decision</th>
                                <th className="px-5 py-2 font-medium">Status</th>
                                <th className="px-5 py-2 font-medium">Reason</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {rows.map((l) => (
                                <tr key={l.id}>
                                    <td className="whitespace-nowrap px-5 py-3 text-xs text-muted-foreground">{formatDateTime(l.timestamp)}</td>
                                    <td className="whitespace-nowrap px-5 py-3">{l.profile}</td>
                                    <td className="px-5 py-3 text-xs font-medium text-primary">{l.action}</td>
                                    <td className="max-w-xs truncate px-5 py-3 font-mono text-xs">{l.query}</td>
                                    <td className="px-5 py-3"><StatusBadge status={l.decision} /></td>
                                    <td className="px-5 py-3"><StatusBadge status={l.status} /></td>
                                    <td className="px-5 py-3 text-xs text-muted-foreground">{l.reason ?? "—"}</td>
                                </tr>
                            ))}
                            {rows.length === 0 && (
                                <tr>
                                    <td colSpan={7} className="px-5 py-10 text-center text-sm text-muted-foreground">
                                        No logs match your filters.
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
                    <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
                </div>
            </div>
        </div>
    );
}