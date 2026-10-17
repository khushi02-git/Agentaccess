import argparse
import random
import subprocess
import sys
import time

QUERIES = [
    "SELECT * FROM users LIMIT 10",
    "SELECT name FROM products",
    "UPDATE orders SET status = 'shipped' WHERE id = 7",
    "DELETE FROM logs WHERE id = 3",
]


def fake_gemini_call(query):
    time.sleep(random.uniform(0.3, 0.8))
    return f"result for: {query}"


def burn_cpu(seconds):
    end = time.time() + seconds
    while time.time() < end:
        sum(i * i for i in range(10_000))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="agent_1")
    parser.add_argument("--role", default="read_only")
    parser.add_argument("--stress", choices=["none", "cpu", "memory", "spawn"], default="none")
    parser.add_argument("--stress-after", type=int, default=10)
    args = parser.parse_args()

    hog = []
    spawned = False
    start = time.time()
    count = 0

    while True:
        count += 1
        query = random.choice(QUERIES)
        fake_gemini_call(query)
        print(f"[{args.name}|{args.role}] request {count}: {query}", flush=True)

        stressing = args.stress != "none" and time.time() - start >= args.stress_after
        if stressing and args.stress == "cpu":
            burn_cpu(1.0)
        elif stressing and args.stress == "memory" and len(hog) < 20:
            hog.append(b"x" * (50 * 1024 * 1024))
        elif stressing and args.stress == "spawn" and not spawned:
            # start a child process: something only some roles may do
            subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
            spawned = True


if __name__ == "__main__":
    main()