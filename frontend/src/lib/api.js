async function getJson(path) {
  return requestJson(path);
}

async function requestJson(path, options = {}) {
  let response;
  let payload;
  try {
    response = await fetch(path, { cache: "no-store", ...options });
  } catch {
    throw new Error("Unable to reach the AgentAccess backend.");
  }

  try {
    payload = await response.json();
  } catch {
    throw new Error(
      `The backend returned an invalid response (${response.status}).`
    );
  }

  if (!response.ok) {
    const detail =
      typeof payload?.detail === "string" ? `: ${payload.detail}` : "";
    throw new Error(`Backend request failed (${response.status})${detail}`);
  }

  if (payload === null || typeof payload !== "object") {
    throw new Error("The backend returned an empty or invalid response.");
  }

  return payload;
}

function postJson(path, body) {
  return requestJson(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function login(username, password) {
  const payload = await postJson("/auth/login", { username, password });
  if (typeof payload.authenticated !== "boolean") {
    throw new Error("The backend returned an invalid login response.");
  }
  return payload;
}

export async function generateSql(request) {
  const payload = await postJson("/gemini/generate", { request });
  const validation = payload.validation;
  if (
    typeof payload.generated_sql !== "string" ||
    payload.executed !== false ||
    !validation ||
    typeof validation.valid !== "boolean" ||
    typeof validation.risk_level !== "string" ||
    typeof validation.action !== "string" ||
    typeof validation.reason !== "string"
  ) {
    throw new Error("The backend returned an invalid SQL generation response.");
  }
  return payload;
}

export async function executeQuery(agentId, query) {
  const payload = await postJson("/query/execute", {
    agent_id: agentId,
    query,
  });
  if (typeof payload.success !== "boolean" || typeof payload.message !== "string") {
    throw new Error("The backend returned an invalid query execution response.");
  }
  return payload;
}

function isNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

export async function fetchSystemStats() {
  const payload = await getJson("/api/system/stats");
  const valid =
    isNumber(payload.cpu_percent) &&
    typeof payload.ram === "object" &&
    payload.ram !== null &&
    isNumber(payload.ram.total_gb) &&
    isNumber(payload.ram.used_gb) &&
    isNumber(payload.ram.percent) &&
    typeof payload.disk === "object" &&
    payload.disk !== null &&
    isNumber(payload.disk.percent) &&
    typeof payload.timestamp === "string" &&
    Array.isArray(payload.processes) &&
    payload.processes.every(
      (process) =>
        process !== null &&
        typeof process === "object" &&
        Number.isInteger(process.pid) &&
        typeof process.name === "string" &&
        isNumber(process.cpu_percent) &&
        isNumber(process.memory_mb)
    );

  if (!valid) {
    throw new Error("The backend returned invalid system statistics.");
  }

  return payload;
}

export async function fetchAuditEvents() {
  const payload = await getJson("/api/events?limit=1000");
  const valid =
    Array.isArray(payload.events) &&
    payload.events.every(
      (event) =>
        event !== null &&
        typeof event === "object" &&
        Number.isInteger(event.id) &&
        typeof event.timestamp === "string" &&
        Number.isFinite(new Date(event.timestamp).getTime()) &&
        typeof event.event === "string" &&
        (event.agent_id === null ||
          typeof event.agent_id === "string" ||
          Number.isInteger(event.agent_id)) &&
        (event.role === null || typeof event.role === "string") &&
        typeof event.details === "object" &&
        event.details !== null &&
        !Array.isArray(event.details) &&
        (event.event_type === undefined ||
          typeof event.event_type === "string") &&
        (event.action === null || typeof event.action === "string") &&
        (event.status === null || typeof event.status === "string") &&
        (event.query === null || typeof event.query === "string") &&
        (event.message === null || typeof event.message === "string")
    );

  if (!valid) {
    throw new Error("The backend returned invalid OS events.");
  }

  return payload.events.sort(
    (first, second) =>
      new Date(second.timestamp).getTime() -
      new Date(first.timestamp).getTime()
  );
}

export const fetchOSEvents = fetchAuditEvents;
