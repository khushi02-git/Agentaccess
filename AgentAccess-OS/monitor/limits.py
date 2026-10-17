# Resource budget and enforcement policy for each role.
#   cpu_percent     : % of ONE core, judged on the AVERAGE of the last
#                     `window_seconds` samples (a rate, so one spike is ignored)
#   memory_mb       : hard ceiling, judged on EVERY sample (a level, not a rate)
#   suspend_seconds : how long a violating agent is frozen before it may resume
#   max_strikes     : violation number at which the agent is terminated instead
#                     (strike 1 -> suspend, ..., strike max_strikes -> terminate)
ROLE_LIMITS = {
    "read_only": {"cpu_percent": 40, "memory_mb": 300, "window_seconds": 5,
                  "suspend_seconds": 5, "max_strikes": 2},
    "writer":    {"cpu_percent": 80, "memory_mb": 600, "window_seconds": 5,
                  "suspend_seconds": 5, "max_strikes": 2},
    "admin":     {"cpu_percent": 90, "memory_mb": 1500, "window_seconds": 5,
                  "suspend_seconds": 5, "max_strikes": 3},
}


# Scheduling priority derived from the role (lower number = more important).
ROLE_PRIORITY = {"admin": 1, "writer": 2, "read_only": 3}