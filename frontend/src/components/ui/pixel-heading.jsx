import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { cn } from "../../lib/utils";

const PIXEL_FONTS = [
  "font-pixel-square",
  "font-pixel-grid",
  "font-pixel-circle",
  "font-pixel-triangle",
  "font-pixel-line",
];

const FONT_LABELS = ["Square", "Grid", "Circle", "Triangle", "Line"];
const FONT_COUNT = PIXEL_FONTS.length;

const PREFIX_FONT_MAP = {
  square: "font-pixel-square",
  grid: "font-pixel-grid",
  circle: "font-pixel-circle",
  triangle: "font-pixel-triangle",
  line: "font-pixel-line",
};

const ISOLATE_FONT_MAP = {
  sans: "font-sans",
  mono: "font-mono",
};

function resolveIsolateFont(value) {
  return ISOLATE_FONT_MAP[value] ?? value;
}

// Golden ratio: keeps neighbouring characters from sharing a font
const PHI = (1 + Math.sqrt(5)) / 2;

// Internal tick rate in ms
const TICK_MS = 50;

function goldenBase(index) {
  return Math.floor((index * PHI * FONT_COUNT) % FONT_COUNT);
}

function pseudoRandom(tick, index) {
  return ((tick * 2654435761 + index * 340573321) >>> 0) % FONT_COUNT;
}

function extractText(children) {
  if (typeof children === "string") return children;
  if (typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(extractText).join("");
  if (children !== null && typeof children === "object" && "props" in children) {
    return extractText(children.props.children);
  }
  return "";
}

/**
 * Heading where each character can use a different pixel font.
 * mode: "uniform" | "multi" | "wave" | "random"
 */
export function PixelHeading({
  children,
  as: Tag = "h1",
  className,
  cycleInterval = 150,
  defaultFontIndex = 0,
  onFontIndexChange,
  showLabel = false,
  mode = "multi",
  staggerDelay = 50,
  autoPlay = false,
  prefix,
  prefixFont = "none",
  isolate,
  onMouseEnter,
  onMouseLeave,
  onFocus,
  onBlur,
  onKeyDown,
  ...props
}) {
  const text = useMemo(() => extractText(children), [children]);

  const [msElapsed, setMsElapsed] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const intervalRef = useRef(null);
  const prevUniformIndex = useRef(defaultFontIndex);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  useEffect(() => {
    if (!autoPlay) return;
    setIsActive(true);
    setMsElapsed(0);
    intervalRef.current = setInterval(() => {
      setMsElapsed((prev) => prev + TICK_MS);
    }, TICK_MS);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoPlay]);

  const charFonts = useMemo(() => {
    const fonts = [];
    let vi = 0; // visible-character index (skips spaces)

    for (let i = 0; i < text.length; i++) {
      if (text[i] === " ") {
        fonts.push(-1);
        continue;
      }

      switch (mode) {
        case "uniform": {
          const cycles = Math.floor(msElapsed / cycleInterval);
          fonts.push((defaultFontIndex + cycles) % FONT_COUNT);
          break;
        }
        case "multi": {
          const base = goldenBase(vi);
          const charMs = Math.max(0, msElapsed - vi * staggerDelay);
          const cycles = Math.floor(charMs / cycleInterval);
          fonts.push((base + cycles) % FONT_COUNT);
          break;
        }
        case "wave": {
          const charMs = Math.max(0, msElapsed - vi * staggerDelay);
          const cycles = Math.floor(charMs / cycleInterval);
          fonts.push((vi + cycles) % FONT_COUNT);
          break;
        }
        case "random": {
          const charMs = Math.max(0, msElapsed - vi * staggerDelay);
          const cycles = Math.floor(charMs / cycleInterval);
          fonts.push(cycles > 0 ? pseudoRandom(cycles, vi) : goldenBase(vi));
          break;
        }
      }
      vi++;
    }
    return fonts;
  }, [text, mode, msElapsed, cycleInterval, staggerDelay, defaultFontIndex]);

  useEffect(() => {
    if (mode !== "uniform") return;
    const idx = charFonts.find((f) => f !== -1) ?? defaultFontIndex;
    if (idx !== prevUniformIndex.current) {
      prevUniformIndex.current = idx;
      onFontIndexChange?.(idx);
    }
  }, [charFonts, mode, defaultFontIndex, onFontIndexChange]);

  const activeLabel = useMemo(() => {
    if (mode === "uniform") {
      const idx = charFonts.find((f) => f !== -1) ?? 0;
      return FONT_LABELS[idx];
    }
    const modeLabels = {
      uniform: "",
      multi: "Multi",
      wave: "Wave",
      random: "Random",
    };
    return modeLabels[mode];
  }, [mode, charFonts]);

  const startCycling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsActive(true);
    setMsElapsed(0);
    intervalRef.current = setInterval(() => {
      setMsElapsed((prev) => prev + TICK_MS);
    }, TICK_MS);
  }, []);

  const stopCycling = useCallback(() => {
    if (autoPlay) {
      setIsActive(true);
      return;
    }
    setIsActive(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, [autoPlay]);

  const handleMouseEnter = useCallback(
    (e) => {
      startCycling();
      onMouseEnter?.(e);
    },
    [startCycling, onMouseEnter]
  );

  const handleMouseLeave = useCallback(
    (e) => {
      stopCycling();
      onMouseLeave?.(e);
    },
    [stopCycling, onMouseLeave]
  );

  const handleFocus = useCallback(
    (e) => {
      startCycling();
      onFocus?.(e);
    },
    [startCycling, onFocus]
  );

  const handleBlur = useCallback(
    (e) => {
      stopCycling();
      onBlur?.(e);
    },
    [stopCycling, onBlur]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setMsElapsed((prev) => prev + cycleInterval);
      }
      onKeyDown?.(e);
    },
    [cycleInterval, onKeyDown]
  );

  const uniformIdx =
    mode === "uniform"
      ? (charFonts.find((f) => f !== -1) ?? defaultFontIndex)
      : 0;

  return (
    <div
      data-slot="pixel-heading"
      className="inline-flex flex-col items-start gap-2"
    >
      <Tag
        data-state={isActive ? "active" : "idle"}
        data-mode={mode}
        aria-label={prefix ? `${prefix} ${text}` : text}
        tabIndex={0}
        className={cn(
          "cursor-default select-none",
          "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none",
          mode === "uniform" && PIXEL_FONTS[uniformIdx],
          className
        )}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        {...props}
      >
        {/* Static prefix */}
        {prefix && (
          <>
            {isolate ? (
              prefix.split("").map((char, i) => (
                <span
                  key={`p${i}`}
                  className={cn(
                    prefixFont !== "none" ? PREFIX_FONT_MAP[prefixFont] : undefined,
                    isolate[char] ? resolveIsolateFont(isolate[char]) : undefined
                  )}
                  aria-hidden
                >
                  {char}
                </span>
              ))
            ) : (
              <span
                className={
                  prefixFont !== "none" ? PREFIX_FONT_MAP[prefixFont] : undefined
                }
                aria-hidden
              >
                {prefix}
              </span>
            )}
            <span> </span>
          </>
        )}

        {/* Animated characters */}
        {mode === "uniform"
          ? children
          : text.split("").map((char, i) =>
              char === " " ? (
                <span key={i}> </span>
              ) : isolate?.[char] ? (
                <span
                  key={i}
                  className={resolveIsolateFont(isolate[char])}
                  aria-hidden
                >
                  {char}
                </span>
              ) : (
                <span key={i} className={PIXEL_FONTS[charFonts[i]]} aria-hidden>
                  {char}
                </span>
              )
            )}
      </Tag>
      {showLabel && (
        <output
          data-slot="pixel-heading-label"
          aria-live="polite"
          className={cn(
            "text-xs tracking-widest text-muted-foreground uppercase transition-opacity duration-200",
            isActive || autoPlay ? "opacity-100" : "opacity-0"
          )}
        >
          {activeLabel}
        </output>
      )}
    </div>
  );
}