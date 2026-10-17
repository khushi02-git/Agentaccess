import json
import tempfile
from pathlib import Path

import audit_log
from access_matrix import ACCESS_MATRIX, OBJECTS, acl, authorize, capabilities, check_access
from agent_monitor import monitor_agent
from scheduler_live import LiveScheduler
from scheduler_sim import pick_priority


def use_temp_log():
    audit_log.LOG_FILE = Path(tempfile.mkdtemp()) / "audit.jsonl"
    audit_log._next_id = None


def read_log():
    with open(audit_log.LOG_FILE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def rights_of(role):
    return {(obj, right) for obj, rights in ACCESS_MATRIX[role].items() for right in rights}


# ---- pure matrix tests (instant) -------------------------------------------
def test_default_deny():
    assert not check_access("intruder", "scheduler", "submit")     # unknown role
    assert not check_access("admin", "database", "drop")           # unknown object
    assert not check_access("admin", "process", "teleport")        # unknown right
    assert not check_access("admin", "network", "connect_other")   # never granted


def test_known_grants_and_refusals():
    assert check_access("admin", "process", "spawn")
    assert not check_access("read_only", "process", "spawn")
    assert not check_access("writer", "process", "spawn")
    assert check_access("read_only", "scheduler", "submit")
    assert check_access("writer", "filesystem", "write_workdir")
    assert not check_access("read_only", "filesystem", "write_workdir")


def test_least_privilege_ordering():
    assert rights_of("read_only") <= rights_of("writer") <= rights_of("admin")
    assert rights_of("read_only") < rights_of("admin")             # strictly less


def test_acl_and_capability_views_agree_with_the_matrix():
    for role in ACCESS_MATRIX:
        for obj in OBJECTS:
            for right in ("read", "submit", "spawn", "connect_llm",
                          "connect_other", "read_workdir", "write_workdir"):
                by_row = right in capabilities(role).get(obj, [])
                by_column = right in acl(obj).get(role, [])
                assert by_row == by_column == check_access(role, obj, right)


# ---- tests that write the audit log ----------------------------------------
def test_authorize_records_the_decision():
    use_temp_log()
    assert authorize("a1", "admin", "process", "spawn") is True
    assert authorize("a2", "read_only", "process", "spawn") is False
    events = [(e["event"], e["agent_id"]) for e in read_log()]
    assert events == [("access_granted", "a1"), ("access_denied", "a2")]


def test_submit_is_denied_for_an_unknown_role():
    use_temp_log()
    sched = LiveScheduler(1, pick_priority, verbose=False)
    try:
        sched.submit("intruder", burst=1)
        assert False, "should have been refused"
    except PermissionError:
        pass
    sched.close()
    sched.wait_until_done()
    kinds = [e["event"] for e in read_log()]
    assert kinds == ["access_denied"]                  # no job was ever created


# ---- tests with real processes (about 10 seconds) ---------------------------
def test_read_only_agent_is_terminated_for_spawning():
    use_temp_log()
    result = monitor_agent("t_ro", "read_only", stress="spawn", stress_after=2,
                           duration=10, verbose=False)
    assert result["outcome"] == "terminated_by_monitor"
    events = read_log()
    assert any(e["event"] == "access_denied" for e in events)
    assert any(e["event"] == "violation"
               and e["details"]["rule"] == "unauthorized_spawn" for e in events)


def test_admin_agent_may_spawn():
    use_temp_log()
    result = monitor_agent("t_admin", "admin", stress="spawn", stress_after=2,
                           duration=6, verbose=False)
    assert result["outcome"] == "completed"
    events = read_log()
    assert any(e["event"] == "access_granted" for e in events)
    assert not any(e["event"] == "violation" for e in events)


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"passed: {t.__name__}")
    print(f"\nall {len(tests)} tests passed")