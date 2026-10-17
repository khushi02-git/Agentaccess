from audit_log import log_event

# Objects the OS layer protects (the COLUMNS of the matrix)
OBJECTS = ["system_stats", "process_list", "scheduler", "process", "network", "filesystem"]

# The ACCESS MATRIX: rows = roles (domains), columns = objects, cells = sets of rights.
# Anything not listed is NOT allowed (default deny).
ACCESS_MATRIX = {
    "read_only": {
        "system_stats": {"read"},
        "scheduler":    {"submit"},
        "network":      {"connect_llm"},
        "filesystem":   {"read_workdir"},
    },
    "writer": {
        "system_stats": {"read"},
        "scheduler":    {"submit"},
        "network":      {"connect_llm"},
        "filesystem":   {"read_workdir", "write_workdir"},
    },
    "admin": {
        "system_stats": {"read"},
        "process_list": {"read"},
        "scheduler":    {"submit"},
        "process":      {"spawn"},
        "network":      {"connect_llm"},
        "filesystem":   {"read_workdir", "write_workdir"},
    },
}

# Rights the code really checks today. The others are the policy that Phase F
# (Docker: network allow-list, read-only filesystem, process limits) will enforce.
ENFORCED_NOW = {("scheduler", "submit"), ("process", "spawn")}


def check_access(role, obj, right):
    """The DECISION: is this role allowed this right on this object? Default deny."""
    return right in ACCESS_MATRIX.get(role, {}).get(obj, set())


def authorize(agent_id, role, obj, right, **details):
    """Decide AND record the decision in the audit log. Returns True or False."""
    allowed = check_access(role, obj, right)
    log_event("access_granted" if allowed else "access_denied", agent_id, role,
              object=obj, right=right, **details)
    return allowed


def acl(obj):
    """Column view (access control list): for one object, who holds which rights."""
    return {role: sorted(rights[obj])
            for role, rights in ACCESS_MATRIX.items() if rights.get(obj)}


def capabilities(role):
    """Row view (capability list): everything one role may do."""
    return {obj: sorted(rights)
            for obj, rights in ACCESS_MATRIX.get(role, {}).items() if rights}


def format_matrix():
    """The matrix as a text table. A * marks rights that the code enforces today."""
    roles = list(ACCESS_MATRIX)

    def cell(role, obj):
        rights = sorted(ACCESS_MATRIX[role].get(obj, set()))
        text = ",".join(r + ("*" if (obj, r) in ENFORCED_NOW else "") for r in rights)
        return text or "-"

    widths = {obj: max(len(obj), *(len(cell(r, obj)) for r in roles)) for obj in OBJECTS}
    header = f"{'role':<11}" + "  ".join(f"{obj:<{widths[obj]}}" for obj in OBJECTS)
    lines = [header, "-" * len(header)]
    for role in roles:
        lines.append(f"{role:<11}" + "  ".join(f"{cell(role, obj):<{widths[obj]}}"
                                              for obj in OBJECTS))
    return "\n".join(lines)