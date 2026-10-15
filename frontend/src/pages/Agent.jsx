import { Bot } from "lucide-react";
import { FoldedCard, FoldedCardFold, FoldedCardBorder } from "../components/ui/folded-card";
import StatusBadge from "../components/StatusBadge";
import { agent, permissionProfiles } from "../data/agent";
import { formatTime } from "../lib/utils";

function Chip({ children, denied }) {
    return (
        <span
            className={
                denied
                    ? "rounded border border-border px-2 py-0.5 text-xs text-muted-foreground line-through"
                    : "rounded border border-primary/40 bg-accent/40 px-2 py-0.5 text-xs font-medium text-primary"
            }
        >
            {children}
        </span>
    );
}

export default function Agent() {
    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold">Agent</h2>

            <div className="flex items-center gap-4 rounded-lg border border-border bg-card p-5">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-primary/40 bg-accent/40">
                    <Bot className="h-6 w-6 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-3">
                        <span className="font-semibold">{agent.name}</span>
                        <StatusBadge status={agent.status} />
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                        {agent.id} · Last active {formatTime(agent.lastActive)}
                    </div>
                </div>
                <div className="hidden gap-8 text-right sm:flex">
                    <div>
                        <div className="text-2xl font-semibold">{agent.queriesToday}</div>
                        <div className="text-xs text-muted-foreground">Queries</div>
                    </div>
                    <div>
                        <div className="text-2xl font-semibold">{agent.violationsToday}</div>
                        <div className="text-xs text-muted-foreground">Violations</div>
                    </div>
                </div>
            </div>

            <h3 className="text-sm font-medium text-muted-foreground">Permission profiles</h3>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {permissionProfiles.map((p) => (
                    <FoldedCard key={p.id} className="mx-0 w-full max-w-none bg-card p-5">
                        <FoldedCardFold />
                        <FoldedCardBorder />
                        <h4 className="pr-10 font-semibold">{p.name}</h4>
                        <div className="mt-1 text-xs text-muted-foreground">
                            {p.queriesToday} queries · {p.violationsToday} violations
                        </div>

                        <div className="mt-4 text-xs text-muted-foreground">Allowed</div>
                        <div className="mt-2 flex flex-wrap gap-2">
                            {p.allowed.map((op) => (
                                <Chip key={op}>{op}</Chip>
                            ))}
                        </div>

                        <div className="mt-4 text-xs text-muted-foreground">Denied</div>
                        <div className="mt-2 flex flex-wrap gap-2">
                            {p.denied.map((op) => (
                                <Chip key={op} denied>
                                    {op}
                                </Chip>
                            ))}
                        </div>
                    </FoldedCard>
                ))}
            </div>
        </div>
    );
}