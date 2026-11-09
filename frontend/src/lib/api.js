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

export async function resolveEntity(agentId, request) {
  const payload = await postJson("/query/resolve-entity", {
    agent_id: agentId,
    request,
  });
  const isMatch = (match) =>
    match !== null &&
    typeof match === "object" &&
    typeof match.table_name === "string" &&
    typeof match.id_column === "string" &&
    Number.isInteger(match.record_id) &&
    typeof match.display_name === "string" &&
    match.data !== null &&
    typeof match.data === "object" &&
    !Array.isArray(match.data);
  if (
    !["not_required", "no_match", "single_match", "multiple_matches"].includes(payload.status) ||
    !Array.isArray(payload.matches) ||
    !payload.matches.every(isMatch) ||
    (payload.status === "single_match" && !isMatch(payload.match)) ||
    (payload.message !== undefined &&
      payload.message !== null &&
      typeof payload.message !== "string")
  ) {
    throw new Error("The backend returned an invalid entity resolution response.");
  }
  return payload;
}

export async function recordEntitySelection(agentId, match) {
  const payload = await postJson("/query/resolve-entity/selection", {
    agent_id: agentId,
    table_name: match.table_name,
    id_column: match.id_column,
    record_id: match.record_id,
    display_name: match.display_name,
    data: match.data,
  });
  const selected = payload.match;
  if (
    payload.success !== true ||
    typeof payload.message !== "string" ||
    selected === null ||
    typeof selected !== "object" ||
    typeof selected.table_name !== "string" ||
    typeof selected.id_column !== "string" ||
    !Number.isInteger(selected.record_id) ||
    typeof selected.display_name !== "string" ||
    selected.data === null ||
    typeof selected.data !== "object" ||
    Array.isArray(selected.data)
  ) {
    throw new Error("The backend returned an invalid entity-selection response.");
  }
  return selected;
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

export async function checkAuthorization(agentId, action, resource) {
  const payload = await postJson("/auth/authorize", {
    agent_id: agentId,
    action,
    resource,
  });
  const valid =
    typeof payload.authorized === "boolean" &&
    (payload.role === null || typeof payload.role === "string") &&
    (payload.permission === null || typeof payload.permission === "string") &&
    typeof payload.reason === "string";

  if (!valid) {
    throw new Error("The backend returned an invalid authorization response.");
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
