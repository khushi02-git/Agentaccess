from access_matrix import acl, capabilities, check_access, format_matrix
from agent_monitor import monitor_agent, show_recent_events
from scheduler_live import LiveScheduler
from scheduler_sim import pick_priority


def main():
    print("ACCESS MATRIX  (rows = roles, columns = objects, * = enforced by code today)\n")
    print(format_matrix())
    print("\nColumn view (ACL) for 'process':      ", acl("process"))
    print("Row view (capabilities) of 'read_only':", capabilities("read_only"))
    print("\nDefault deny: may an unknown role submit jobs?",
          check_access("intruder", "scheduler", "submit"))

    print("\n--- 1. an unknown role tries to submit a job ---")
    sched = LiveScheduler(1, pick_priority)
    try:
        sched.submit("intruder", burst=2)
    except PermissionError as error:
        print("blocked:", error)
    sched.close()
    sched.wait_until_done()

    print("\n--- 2. a read_only agent tries to create a process ---")
    monitor_agent("spawn_ro", "read_only", stress="spawn", stress_after=2, duration=8)

    print("\n--- 3. an admin agent does the same ---")
    monitor_agent("spawn_admin", "admin", stress="spawn", stress_after=2, duration=6)

    show_recent_events(12)


if __name__ == "__main__":
    main()