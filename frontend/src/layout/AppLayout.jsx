import { Outlet } from "react-router-dom";
import { PixelHeading } from "../components/ui/pixel-heading";
import {
  LayoutDashboard,
  Bot,
  Activity,
  ScrollText,
  History,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { Sidebar, SidebarBody, SidebarLink } from "../components/ui/sidebar";

const icon = "h-5 w-5 shrink-0 text-foreground";

const links = [
  { label: "Dashboard", to: "/", icon: <LayoutDashboard className={icon} /> },
  { label: "Agent", to: "/agent", icon: <Bot className={icon} /> },
  { label: "System Monitor", to: "/system", icon: <Activity className={icon} /> },
  { label: "Logs", to: "/logs", icon: <ScrollText className={icon} /> },
  { label: "Audit Trail", to: "/audit", icon: <History className={icon} /> },
  { label: "Violations", to: "/violations", icon: <ShieldAlert className={icon} /> },
  { label: "RBAC", to: "/rbac", icon: <ShieldCheck className={icon} /> },
];

export default function AppLayout() {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar>
        <SidebarBody className="justify-between gap-10">
          <div className="flex flex-col gap-2">
            {links.map((link) => (
              <SidebarLink key={link.to} link={link} />
            ))}
          </div>
        </SidebarBody>
      </Sidebar>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-20 shrink-0 items-center justify-between border-b border-border px-6">
          <PixelHeading mode="wave" as="h1" className="text-3xl text-primary">
            AgentAccess
          </PixelHeading>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-primary" />
            Agent active
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}