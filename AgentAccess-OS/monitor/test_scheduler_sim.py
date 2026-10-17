from scheduler_sim import (
    make_pick_aging, pick_fcfs, pick_priority, pick_sjf,
    simulate, starvation_example, worked_example,
)


def order(result):
    return [name for name, _, _ in result["schedule"]]


def start_of(result, name):
    return next(r["start"] for r in result["rows"] if r["name"] == name)


def test_fcfs():
    r = simulate(worked_example(), pick_fcfs)
    assert order(r) == ["R1", "R2", "R3", "R4"]
    assert r["avg_waiting"] == 5.0
    assert r["avg_turnaround"] == 8.75


def test_priority():
    r = simulate(worked_example(), pick_priority)
    assert order(r) == ["R1", "R3", "R2", "R4"]
    assert r["avg_waiting"] == 4.75
    assert r["avg_turnaround"] == 8.5


def test_sjf():
    r = simulate(worked_example(), pick_sjf)
    assert order(r) == ["R1", "R3", "R2", "R4"]
    assert r["avg_waiting"] == 4.75


def test_admin_waits_less_under_priority():
    fcfs = simulate(worked_example(), pick_fcfs)
    prio = simulate(worked_example(), pick_priority)
    wait = lambda res, n: next(r["waiting"] for r in res["rows"] if r["name"] == n)
    assert wait(prio, "R3") < wait(fcfs, "R3")   # admin is better off
    assert wait(prio, "R2") > wait(fcfs, "R2")   # writer pays for it


def test_throughput_is_policy_independent():
    results = [simulate(worked_example(), p) for p in (pick_fcfs, pick_sjf, pick_priority)]
    assert len({r["throughput"] for r in results}) == 1
    assert all(r["utilization"] == 100.0 for r in results)


def test_starvation_and_aging():
    no_aging = simulate(starvation_example(), pick_priority)
    aging = simulate(starvation_example(), make_pick_aging(3))
    assert order(no_aging)[-1] == "L"          # starves: runs dead last
    assert start_of(no_aging, "L") == 19
    assert start_of(aging, "L") == 10          # aging rescues it
    assert order(aging)[-1] != "L"


def test_idle_gap():
    from scheduler_sim import make_request
    reqs = [make_request("A", "admin", 0, 2), make_request("B", "admin", 10, 2)]
    r = simulate(reqs, pick_fcfs)
    assert start_of(r, "B") == 10              # server waited for B to arrive
    assert r["utilization"] == round(100 * 4 / 12, 1)


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"passed: {t.__name__}")
    print(f"\nall {len(tests)} tests passed")