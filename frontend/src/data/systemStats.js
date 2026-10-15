export const systemStats = {
  cpuPercent: 42.5,
  memory: { totalGB: 16, usedGB: 9.4, percent: 58.8 },
  disk: { totalGB: 512, usedGB: 301, percent: 58.8 },
  uptimeSeconds: 183240,
  timestamp: "2026-10-09T10:42:00Z",
};

export const systemHistory = [
  { time: "10:37", cpu: 31, memory: 55 },
  { time: "10:38", cpu: 38, memory: 56 },
  { time: "10:39", cpu: 52, memory: 57 },
  { time: "10:40", cpu: 47, memory: 58 },
  { time: "10:41", cpu: 40, memory: 58 },
  { time: "10:42", cpu: 42, memory: 59 },
];

export const processes = [
  { pid: 4120, name: "python.exe", cpuPercent: 18.2, memoryMB: 412, status: "running" },
  { pid: 5188, name: "mysqld.exe", cpuPercent: 11.4, memoryMB: 780, status: "running" },
  { pid: 7032, name: "node.exe", cpuPercent: 6.1, memoryMB: 295, status: "running" },
  { pid: 2216, name: "docker.exe", cpuPercent: 2.3, memoryMB: 150, status: "sleeping" },
  { pid: 9904, name: "code.exe", cpuPercent: 1.8, memoryMB: 520, status: "sleeping" },
];