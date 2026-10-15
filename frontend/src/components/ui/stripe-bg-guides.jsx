import { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";

const easingFunctions = {
  linear: [0, 0, 1, 1],
  easeIn: [0.42, 0, 1, 1],
  easeOut: [0, 0, 0.58, 1],
  easeInOut: [0.42, 0, 0.58, 1],
  spring: [0.175, 0.885, 0.32, 1.275],
};

// Converts "4rem" or "64px" to a pixel number
function toPx(value) {
  const n = parseFloat(value);
  return String(value).includes("rem") ? n * 16 : n;
}

export function StripeBgGuides({
  columnCount = 4,
  className = "",
  solidLines = [],
  animated = true,
  animationDuration = 62,
  animationDelay = 0.8,
  glowColor = "#22c55e",
  glowSize = "10vh",
  glowOpacity = 0.4,
  randomize = true,
  randomInterval = 9000,
  direction = "both",
  easing = "spring",
  responsive = false,
  minColumnWidth = "4rem",
  maxActiveColumns = 3,
  darkMode = true,
  contained = true,
}) {
  const [windowWidth, setWindowWidth] = useState(
    typeof window !== "undefined" ? window.innerWidth : 0
  );

  const columns = useMemo(() => {
    const count = responsive
      ? Math.max(Math.floor(windowWidth / toPx(minColumnWidth)), 1)
      : columnCount;
    return [...Array(count)];
  }, [columnCount, responsive, windowWidth, minColumnWidth]);

  const [activeColumns, setActiveColumns] = useState(columns.map(() => true));

  const getRandomColumns = useCallback(() => {
    const next = columns.map(() => Math.random() < 0.5);
    const activeCount = next.filter(Boolean).length;
    if (activeCount > maxActiveColumns) {
      const toDeactivate = next
        .map((isActive, index) => (isActive ? index : -1))
        .filter((index) => index !== -1)
        .sort(() => Math.random() - 0.5)
        .slice(0, activeCount - maxActiveColumns);
      toDeactivate.forEach((index) => {
        next[index] = false;
      });
    }
    return next;
  }, [columns, maxActiveColumns]);

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    setActiveColumns(columns.map(() => true));
  }, [columns]);

  useEffect(() => {
    if (randomize && animated) {
      const intervalId = setInterval(() => {
        setActiveColumns(getRandomColumns());
      }, randomInterval);
      return () => clearInterval(intervalId);
    }
    setActiveColumns(columns.map(() => true));
  }, [randomize, animated, randomInterval, getRandomColumns, columns]);

  const animationVariants = useMemo(() => {
    const variants = {
      "top-to-bottom": {
        initial: { top: "-100%" },
        animate: { top: "100%" },
      },
      "bottom-to-top": {
        initial: { top: "100%" },
        animate: { top: "-100%" },
      },
      both: {
        initial: { top: "100%" },
        animate: { top: ["-100%", "100%"] },
      },
      random: {
        initial: () => ({ top: Math.random() < 0.5 ? "-100%" : "100%" }),
        animate: () => ({ top: Math.random() < 0.5 ? "-100%" : "100%" }),
      },
    };
    return variants[direction] || variants["top-to-bottom"];
  }, [direction]);

  const lineColors = useMemo(
    () => ({
      solid: darkMode ? "#1e293b" : "hsl(233 14.1% 96.1%)",
      dashed: darkMode ? "#334155" : "hsl(233 14% 93%)",
    }),
    [darkMode]
  );

  const fadeColor = darkMode ? "#020617" : "#ffffff";

  return (
    <div
      className={`pointer-events-none ${
        contained ? "absolute inset-0" : "fixed inset-0"
      } ${className}`}
      aria-hidden="true"
      style={{ zIndex: contained ? 0 : -1 }}
    >
      <div className="z-0 h-full w-full px-4 sm:px-6 lg:px-24">
        <div
          className="mx-auto h-full w-full"
          style={{
            display: "grid",
            gridTemplateColumns: responsive
              ? `repeat(auto-fit, minmax(${minColumnWidth}, 1fr))`
              : `repeat(${columnCount}, minmax(0, 1fr))`,
            gap: "2rem",
          }}
        >
          {columns.map((_, index) => (
            <div key={index} className="relative h-full">
              <div
                className={`absolute inset-y-0 ${
                  index === 0
                    ? "left-0"
                    : index === columns.length - 1
                      ? "right-0"
                      : "left-1/2"
                } w-px overflow-hidden`}
                style={
                  solidLines.includes(index + 1)
                    ? { background: lineColors.solid }
                    : {
                        backgroundImage: `linear-gradient(to bottom, ${lineColors.dashed} 50%, transparent 50%)`,
                        backgroundSize: "1px 8px",
                      }
                }
              >
                <AnimatePresence>
                  {animated && activeColumns[index] && (
                    <motion.div
                      key={`glow-${index}`}
                      className="absolute w-full"
                      style={{
                        height: glowSize,
                        background: `linear-gradient(to bottom, transparent, ${glowColor}, ${fadeColor})`,
                        opacity: glowOpacity,
                      }}
                      initial={
                        typeof animationVariants.initial === "function"
                          ? animationVariants.initial()
                          : animationVariants.initial
                      }
                      animate={
                        typeof animationVariants.animate === "function"
                          ? animationVariants.animate()
                          : animationVariants.animate
                      }
                      exit={
                        typeof animationVariants.initial === "function"
                          ? animationVariants.initial()
                          : animationVariants.initial
                      }
                      transition={{
                        duration: animationDuration,
                        repeat: Infinity,
                        ease: easingFunctions[easing],
                        delay: index * animationDelay,
                      }}
                    />
                  )}
                </AnimatePresence>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}