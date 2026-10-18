import { useState } from "react";
import {
  AlertTriangle,
  Check,
  CircleCheck,
  CircleX,
  Database,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";
import { checkAuthorization } from "../lib/api";

const operations = ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP"];

const scenarios = [
  {
    label: "Permitted read",
    detail: "Agent 1 · SELECT",
    agentId: 1,
    action: "SELECT",
    resource: "employees",
  },
  {
    label: "Role permission denied",
    detail: "Agent 3 · UPDATE",
    agentId: 3,
    action: "UPDATE",
    resource: "employees",
  },
  {
    label: "Restricted operation",
    detail: "Agent 1 · DROP",
    agentId: 1,
    action: "DROP",
    resource: "employees",
  },
  {
    label: "Unknown agent",
    detail: "Agent 999999 · SELECT",
    agentId: 999999,
    action: "SELECT",
    resource: "employees",
  },
];

const fieldClass =
  "mt-2 h-10 w-full rounded-md border border-border bg-black px-3 text-sm text-foreground outline-none focus:border-primary disabled:opacity-50";

export default function RBAC() {
  const [agentId, setAgentId] = useState("1");
  const [action, setAction] = useState("SELECT");
  const [resource, setResource] = useState("employees");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [validationError, setValidationError] = useState("");
  const [activeScenario, setActiveScenario] = useState("");

  const runAuthorization = async (request, scenarioLabel = "") => {
    setLoading(true);
    setActiveScenario(scenarioLabel);
    setResult(null);
    setError("");
    setValidationError("");

    try {
      const response = await checkAuthorization(
        request.agentId,
        request.action,
        request.resource
      );
      setResult({ ...response, request });
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Authorization could not be checked."
      );
    } finally {
      setLoading(false);
      setActiveScenario("");
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const numericAgentId = Number(agentId);
    const normalizedResource = resource.trim();

    if (!Number.isInteger(numericAgentId) || numericAgentId < 1) {
      setValidationError("Enter a positive whole-number agent ID.");
      setResult(null);
      setError("");
      return;
    }
    if (!normalizedResource || normalizedResource.length > 128) {
      setValidationError("Enter a resource name up to 128 characters long.");
      setResult(null);
      setError("");
      return;
    }

    runAuthorization({
      agentId: numericAgentId,
      action,
      resource: normalizedResource,
    });
  };

  const runScenario = (scenario) => {
    setAgentId(String(scenario.agentId));
    setAction(scenario.action);
    setResource(scenario.resource);
    runAuthorization({
      agentId: scenario.agentId,
      action: scenario.action,
      resource: scenario.resource,
    }, scenario.label);
  };

  const authorizationUnavailable =
    result &&
    !result.authorized &&
    (result.reason.startsWith("Authorization unavailable:") ||
      result.reason === "Authorization check failed; request denied");
  const outcomeClass = result?.authorized
    ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-300"
    : authorizationUnavailable
      ? "border-amber-500/50 bg-amber-500/10 text-amber-200"
      : "border-red-500/50 bg-red-500/10 text-red-300";

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md border border-primary/40 bg-accent/40">
            <ShieldCheck className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-primary">
              Access governance
            </p>
            <h2 className="text-xl font-semibold sm:text-2xl">
              Role-Based Access Control
            </h2>
          </div>
        </div>
        <p className="mt-4 max-w-3xl text-sm leading-6 text-muted-foreground">
          RBAC grants database operations according to an agent’s assigned role.
          Each check is evaluated by the backend against agent identity, role
          permissions, and blocked-operation policy; this panel reports that
          response without making its own access decision.
        </p>
      </div>

      <section className="rounded-lg border border-border bg-card p-5 sm:p-6">
        <div className="mb-5">
          <h3 className="text-sm font-semibold">Test an authorization request</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Submit a single operation to the live AgentAccess authorization API.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block text-xs font-medium text-muted-foreground" htmlFor="rbac-agent">
              Agent ID
              <input
                id="rbac-agent"
                type="number"
                min="1"
                step="1"
                required
                value={agentId}
                disabled={loading}
                onChange={(event) => setAgentId(event.target.value)}
                className={fieldClass}
                placeholder="1"
              />
            </label>

            <label className="block text-xs font-medium text-muted-foreground" htmlFor="rbac-action">
              Operation
              <select
                id="rbac-action"
                value={action}
                disabled={loading}
                onChange={(event) => setAction(event.target.value)}
                className={fieldClass}
              >
                {operations.map((operation) => (
                  <option key={operation} value={operation}>
                    {operation}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-xs font-medium text-muted-foreground" htmlFor="rbac-resource">
              Resource / table
              <input
                id="rbac-resource"
                type="text"
                required
                maxLength={128}
                value={resource}
                disabled={loading}
                onChange={(event) => setResource(event.target.value)}
                className={fieldClass}
                placeholder="employees"
              />
            </label>
          </div>

          {validationError && (
            <p role="alert" className="text-sm text-amber-300">
              {validationError}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:pointer-events-none disabled:opacity-50"
          >
            {loading ? (
              <>
                <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
                Checking access…
              </>
            ) : (
              <>
                <Check className="h-4 w-4" aria-hidden="true" />
                Check Access
              </>
            )}
          </button>
        </form>

        {error && (
          <div
            role="alert"
            className="mt-5 flex gap-3 rounded-md border border-amber-500/50 bg-amber-500/10 p-4 text-sm text-amber-200"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <div>
              <p className="font-medium">Authorization check failed</p>
              <p className="mt-1 text-amber-100/80">{error}</p>
            </div>
          </div>
        )}

        {result && (
          <div
            aria-live="polite"
            className={`mt-5 rounded-md border p-4 ${outcomeClass}`}
          >
            <div className="flex flex-wrap items-center gap-2">
              {result.authorized ? (
                <CircleCheck className="h-5 w-5 shrink-0" aria-hidden="true" />
              ) : authorizationUnavailable ? (
                <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden="true" />
              ) : (
                <CircleX className="h-5 w-5 shrink-0" aria-hidden="true" />
              )}
              <h4 className="font-semibold">
                {result.authorized
                  ? "Allowed"
                  : authorizationUnavailable
                    ? "Check failed · Request denied"
                    : "Denied"}
              </h4>
              <span className="ml-auto text-xs opacity-80">Backend response</span>
            </div>
            <dl className="mt-4 grid gap-x-6 gap-y-3 border-t border-current/20 pt-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-xs opacity-70">Agent ID</dt>
                <dd className="mt-1 font-medium">{result.request.agentId}</dd>
              </div>
              <div>
                <dt className="text-xs opacity-70">Assigned role</dt>
                <dd className="mt-1 font-medium">{result.role ?? "Not assigned"}</dd>
              </div>
              <div>
                <dt className="text-xs opacity-70">Permission</dt>
                <dd className="mt-1 font-medium">{result.permission ?? "Not returned"}</dd>
              </div>
              <div>
                <dt className="text-xs opacity-70">Requested resource</dt>
                <dd className="mt-1 inline-flex items-center gap-1.5 font-medium">
                  <Database className="h-3.5 w-3.5" aria-hidden="true" />
                  {result.request.resource}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-xs opacity-70">Reason</dt>
                <dd className="mt-1 font-medium">{result.reason}</dd>
              </div>
            </dl>
          </div>
        )}
      </section>

      <section aria-labelledby="rbac-scenarios-heading" className="space-y-3">
        <div>
          <h3 id="rbac-scenarios-heading" className="text-sm font-semibold">
            Quick test scenarios
          </h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Uses sample agents from the database seed; each button calls the backend.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {scenarios.map((scenario) => (
            <button
              key={scenario.label}
              type="button"
              disabled={loading}
              onClick={() => runScenario(scenario)}
              className="flex min-h-16 items-center gap-3 rounded-md border border-border bg-card px-4 py-3 text-left transition-colors hover:border-primary/50 disabled:pointer-events-none disabled:opacity-50"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-border bg-black">
                {activeScenario === scenario.label ? (
                  <LoaderCircle className="h-4 w-4 animate-spin text-primary" aria-hidden="true" />
                ) : (
                  <ShieldCheck className="h-4 w-4 text-primary" aria-hidden="true" />
                )}
              </div>
              <span className="min-w-0">
                <span className="block text-sm font-medium text-foreground">{scenario.label}</span>
                <span className="mt-0.5 block text-xs text-muted-foreground">{scenario.detail}</span>
              </span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}