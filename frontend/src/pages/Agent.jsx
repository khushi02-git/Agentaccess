import { useState } from "react";
import { Bot } from "lucide-react";
import { FoldedCard, FoldedCardFold, FoldedCardBorder } from "../components/ui/folded-card";
import StatusBadge from "../components/StatusBadge";
import { agent, permissionProfiles } from "../data/agent";
import { executeQuery, generateSql } from "../lib/api";
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

    const handleRequestChange = (event) => {
        setRequest(event.target.value);
        setGeneration(null);
        setGenerationError("");
        setExecution(null);
        setExecutionError("");
    };

    const handleGenerate = async (event) => {
        event.preventDefault();
        setGenerating(true);
        setGeneration(null);
        setGenerationError("");
        setExecution(null);
        setExecutionError("");

        try {
            setGeneration(await generateSql(request.trim()));
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

                {generationError && (
                    <p role="alert" className="rounded-md border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-400">
                        {generationError}
                    </p>
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