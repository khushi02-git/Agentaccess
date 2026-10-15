import { createContext, useContext, useState } from "react";
import { NavLink } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { Menu, X } from "lucide-react";
import { cn } from "../../lib/utils";

const SidebarContext = createContext(undefined);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a Sidebar");
  }
  return context;
};

export const Sidebar = ({
  children,
  open: openProp,
  setOpen: setOpenProp,
  animate = true,
}) => {
  const [openState, setOpenState] = useState(false);
  const open = openProp !== undefined ? openProp : openState;
  const setOpen = setOpenProp !== undefined ? setOpenProp : setOpenState;

  return (
    <SidebarContext.Provider value={{ open, setOpen, animate }}>
      {children}
    </SidebarContext.Provider>
  );
};

export const SidebarBody = (props) => {
  return (
    <>
      <DesktopSidebar {...props} />
      <MobileSidebar {...props} />
    </>
  );
};

export const DesktopSidebar = ({ className, children, ...props }) => {
  const { open, setOpen, animate } = useSidebar();
  return (
    <motion.div
      className={cn(
        "hidden h-full w-[240px] shrink-0 flex-col border-r border-border bg-card px-3 py-4 md:flex",
        className
      )}
      animate={{ width: animate ? (open ? "240px" : "64px") : "240px" }}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const MobileSidebar = ({ className, children, ...props }) => {
  const { open, setOpen } = useSidebar();
  return (
    <div className="flex h-12 w-full items-center justify-end border-b border-border bg-card px-4 md:hidden">
      <Menu
        className="cursor-pointer text-foreground"
        onClick={() => setOpen(!open)}
      />
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ x: "-100%", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: "-100%", opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className={cn(
              "fixed inset-0 z-[100] flex flex-col justify-between bg-background p-8",
              className
            )}
            onClick={(e) => {
              if (e.target.closest("a")) setOpen(false);
            }}
            {...props}
          >
            <div
              className="absolute right-8 top-8 z-50 cursor-pointer text-foreground"
              onClick={() => setOpen(false)}
            >
              <X />
            </div>
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const SidebarLink = ({ link, className }) => {
  const { open, animate } = useSidebar();
  return (
    <NavLink
      to={link.to}
      end={link.to === "/"}
      className={({ isActive }) =>
        cn(
          "group/sidebar flex items-center justify-start gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
          isActive && "bg-muted text-primary",
          className
        )
      }
    >
      {link.icon}
      <motion.span
        animate={{
          display: animate ? (open ? "inline-block" : "none") : "inline-block",
          opacity: animate ? (open ? 1 : 0) : 1,
        }}
        className="inline-block whitespace-pre text-sm transition duration-150 group-hover/sidebar:translate-x-1"
      >
        {link.label}
      </motion.span>
    </NavLink>
  );
};