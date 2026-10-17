import subprocess
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
AGENT_SCRIPT = ROOT / "agent_runner" / "dummy_agent.py"


def start_agent(name, role, stress="none", stress_after=10):
    # sys.executable = the exact Python running this file (the venv one)
    cmd = [
        sys.executable, str(AGENT_SCRIPT),
        "--name", name, "--role", role,
        "--stress", stress, "--stress-after", str(stress_after),
    ]
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL)


class AgentTracker:
    def __init__(self, popen):
        self.root = psutil.Process(popen.pid)
        self._cache = {}  # pid -> Process, so CPU readings keep their history

    def _all_processes(self):
        procs = [self.root]
        try:
            procs += self.root.children(recursive=True)
        except psutil.NoSuchProcess:
            pass
        return procs

    def sample(self):
        cpu = 0.0
        ram = 0
        count = 0
        for p in self._all_processes():
            p = self._cache.setdefault(p.pid, p)
            try:
                cpu += p.cpu_percent(interval=None)
                ram += p.memory_info().rss
                count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {
            "pid": self.root.pid,
            "process_count": count,
            "cpu_percent": round(cpu, 1),
            "memory_mb": round(ram / 1024**2, 1),
        }

    def suspend(self):
        """Freeze the agent and all its children. Their memory stays allocated."""
        for p in self._all_processes():
            try:
                p.suspend()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def resume(self):
        """Let a suspended agent (and its children) run again."""
        for p in self._all_processes():
            try:
                p.resume()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def status(self):
        """Ask the OS: 'suspended' if every process is stopped, else 'active'."""
        states = []
        for p in self._all_processes():
            try:
                states.append(p.status())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if states and all(s == psutil.STATUS_STOPPED for s in states):
            return "suspended"
        return "active"

    def stop(self):
        procs = self._all_processes()
        for p in procs:
            try:
                p.resume()      # a suspended process cannot act on a polite request
                p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        _, alive = psutil.wait_procs(procs, timeout=3)
        for p in alive:
            p.kill()