import { useState } from "react";
import { Bot } from "lucide-react";
import { FoldedCard, FoldedCardFold, FoldedCardBorder } from "../components/ui/folded-card";
import StatusBadge from "../components/StatusBadge";
import { agent, permissionProfiles } from "../data/agent";
import {
    executeQuery,
    generateSql,
    recordEntitySelection,
    resolveEntity,
} from "../lib/api";
import { formatTime } from "../lib/utils";

const DEMO_AGENT_ID = 1;

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
    const [request, setRequest] = useState("");
    const [generation, setGeneration] = useState(null);
    const [generationError, setGenerationError] = useState("");
    const [generating, setGenerating] = useState(false);
    const [execution, setExecution] = useState(null);
    const [executionError, setExecutionError] = useState("");
    const [executing, setExecuting] = useState(false);
    const [entityResolution, setEntityResolution] = useState(null);
    const [entityResolutionError, setEntityResolutionError] = useState("");
    const [selectedMatchId, setSelectedMatchId] = useState(null);

    const handleRequestChange = (event) => {
        setRequest(event.target.value);
        setGeneration(null);
        setGenerationError("");
        setExecution(null);
        setExecutionError("");
        setEntityResolution(null);
        setEntityResolutionError("");
        setSelectedMatchId(null);
    };

    const generateSqlForRequest = async (requestText, match = null) => {
        const generationRequest = match
            ? `${requestText}\n\nThe user selected this record:\ntable_name = ${match.table_name}\nid_column = ${match.id_column}\nrecord_id = ${match.record_id}\ndisplay_name = ${match.display_name}\ndata = ${JSON.stringify(match.data)}\nUse this selected record for the SQL operation.`
            : requestText;
        setGeneration(await generateSql(generationRequest));
    };

    const handleGenerate = async (event) => {
        event.preventDefault();
        setGenerating(true);
        setGeneration(null);
        setGenerationError("");
        setExecution(null);
        setExecutionError("");
        setEntityResolution(null);
        setEntityResolutionError("");
        setSelectedMatchId(null);

        try {
            const resolution = await resolveEntity(DEMO_AGENT_ID, request.trim());
            setEntityResolution(resolution);

            if (resolution.status === "not_required") {
                await generateSqlForRequest(request.trim());
                return;
            }

            if (resolution.status === "multiple_matches") {
                setGeneration(null);
                return;
            }

            if (resolution.status === "no_match") {
                setGeneration(null);
                return;
            }

            if (resolution.status === "single_match") {
                setSelectedMatchId(`${resolution.match.table_name}:${resolution.match.record_id}`);
                await generateSqlForRequest(request.trim(), resolution.match);
                return;
            }

            await generateSqlForRequest(request.trim());
        } catch (error) {
            setGenerationError(error.message);
        } finally {
            setGenerating(false);
        }
    };

    const handleSelectMatch = async (match) => {
        setSelectedMatchId(`${match.table_name}:${match.record_id}`);
        setEntityResolutionError("");
        setGeneration(null);
        setGenerationError("");
        setExecution(null);
        setExecutionError("");
        setGenerating(true);

        try {
            const selected = await recordEntitySelection(DEMO_AGENT_ID, match);
            await generateSqlForRequest(request.trim(), selected);
        } catch (error) {
            setGenerationError(error.message);
        } finally {
            setGenerating(false);
        }
    };

    const handleExecute = async () => {
        if (
            !generation?.generated_sql ||
            generation.executed !== false ||
            generation.validation?.valid !== true
        ) {
            return;
        }

        setExecuting(true);
        setExecution(null);
        setExecutionError("");

        try {
            const result = await executeQuery(DEMO_AGENT_ID, generation.generated_sql);
            if (result.success) {
                setExecution(result);
            } else {
                setExecutionError(result.message || "The backend rejected the query.");
            }
        } catch (error) {
            setExecutionError(error.message);
        } finally {
            setExecuting(false);
        }
    };

    const canExecute =
        Boolean(generation?.generated_sql) &&
        generation?.validation?.valid === true &&
        generation.executed === false &&
        !generating &&
        !executing;

    const selectedMatch =
        entityResolution?.matches?.find(
            (match) => `${match.table_name}:${match.record_id}` === selectedMatchId
        ) ??
        (entityResolution?.status === "single_match" &&
        `${entityResolution.match.table_name}:${entityResolution.match.record_id}` === selectedMatchId
            ? entityResolution.match
            : null);

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

            <section className="space-y-4 rounded-lg border border-border bg-card p-5">
                <div>
                    <h3 className="text-sm font-medium">Ask Agent</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                        Development/demo identity: database agent ID {DEMO_AGENT_ID} (AdminAgent).
                        This is not production-secure authentication.
                    </p>
                </div>

                <form onSubmit={handleGenerate} className="space-y-3">
                    <label htmlFor="agent-request" className="block text-xs text-muted-foreground">
                        Natural-language database request
                    </label>
                    <textarea
                        id="agent-request"
                        value={request}
                        onChange={handleRequestChange}
                        disabled={generating || executing}
                        maxLength={2000}
                        rows={3}
                        placeholder="Show all employees from the IT department."
                        className="w-full resize-y rounded-md border border-border bg-black p-3 text-sm outline-none placeholder:text-muted-foreground focus:border-primary"
                    />
                    <button
                        type="submit"
                        disabled={!request.trim() || generating || executing}
                        className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:pointer-events-none disabled:opacity-40"
                    >
                        {generating ? "Generating SQL…" : "Generate SQL"}
                    </button>
                </form>

                {entityResolutionError && (
                    <p role="alert" className="rounded-md border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-400">
                        {entityResolutionError}
                    </p>
                )}

                {generationError && (
                    <p role="alert" className="rounded-md border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-400">
                        {generationError}
                    </p>
                )}

                {entityResolution?.status === "no_match" && (
                    <p className="rounded-md border border-border bg-black/30 p-3 text-sm text-muted-foreground">
                        {entityResolution.message || "No matching record found."}
                    </p>
                )}

                {entityResolution?.status === "multiple_matches" && (
                    <div className="space-y-3 rounded-md border border-amber-500/50 bg-amber-500/10 p-3">
                        <p className="text-sm font-medium">Multiple matching records found</p>
                        <p className="text-xs text-muted-foreground">Please select the record you mean before executing.</p>
                        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                            {entityResolution.matches.map((match) => {
                                const isSelected = `${match.table_name}:${match.record_id}` === selectedMatchId;
                                return (
                                    <div
                                        key={`${match.table_name}:${match.record_id}`}
                                        className={`rounded-md border p-3 ${isSelected ? "border-primary bg-accent/20" : "border-border bg-card"}`}
                                    >
                                        <div className="text-xs text-muted-foreground">{match.table_name}</div>
                                        <div className="mt-1 text-sm font-medium">ID: {match.record_id}</div>
                                        <div className="mt-1 text-sm">{match.display_name}</div>
                                        <div className="mt-1 text-xs text-muted-foreground">
                                            {JSON.stringify(match.data)}
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => handleSelectMatch(match)}
                                            disabled={generating}
                                            className="mt-3 h-8 rounded-md border border-primary/40 px-3 text-xs font-medium text-primary"
                                        >
                                            {isSelected ? "Selected" : "Select"}
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {selectedMatch && generation && (
                    <div className="rounded-md border border-primary/40 bg-accent/20 p-3 text-xs text-muted-foreground">
                        Selected record: {selectedMatch.table_name} · ID {selectedMatch.record_id} · {selectedMatch.display_name}
                    </div>
                )}

                {generation && (
                    <div className="space-y-4 border-t border-border pt-4">
                        <p className="text-xs text-muted-foreground">
                            Gemini generated this SQL. It was not executed until you explicitly clicked Execute.
                        </p>
                        <pre className="overflow-x-auto whitespace-pre-wrap break-words rounded-md border border-border bg-black p-3 font-mono text-xs">
                            {generation.generated_sql}
                        </pre>

                        <div className={`rounded-md border p-3 text-sm ${
                            generation.validation.valid
                                ? "border-primary/40 bg-accent/20"
                                : "border-red-500/50 bg-red-500/10"
                        }`}>
                            <div className="font-medium">
                                {generation.validation.valid ? "Validation passed" : "Query rejected"}
                            </div>
                            <div className="mt-1 text-xs">
                                Action: {generation.validation.action} · Risk: {generation.validation.risk_level}
                            </div>
                            <div className="mt-1 text-xs text-muted-foreground">
                                {generation.validation.reason}
                            </div>
                        </div>

                        {!generation.validation.valid && (
                            <p className="text-sm text-red-400">
                                This query was rejected and cannot be executed.
                            </p>
                        )}
                        <button
                            type="button"
                            onClick={handleExecute}
                            disabled={!canExecute}
                            className="h-9 rounded-md bg-primary px-4 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:pointer-events-none disabled:opacity-40"
                        >
                            {executing ? "Executing…" : "Execute"}
                        </button>
                    </div>
                )}

                {executionError && (
                    <p role="alert" className="rounded-md border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-400">
                        {executionError}
                    </p>
                )}

                {execution && (
                    <div className="space-y-2 rounded-md border border-primary/40 bg-accent/20 p-3">
                        <p className="text-sm font-medium">{execution.message}</p>
                        {execution.request_id != null && (
                            <p className="text-xs text-muted-foreground">
                                Request ID: {execution.request_id}
                            </p>
                        )}
                        {execution.result == null ||
                        (Array.isArray(execution.result) && execution.result.length === 0) ? (
                            <p className="text-sm text-muted-foreground">The query completed with no rows returned.</p>
                        ) : (
                            <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-black p-3 font-mono text-xs">
                                {JSON.stringify(execution.result, null, 2)}
                            </pre>
                        )}
                    </div>
                )}
            </section>

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