import { useEffect, useMemo, useRef, useState } from "react";
import {
    ComposableMap,
    Geographies,
    Geography,
    Graticule,
    Marker,
    ZoomableGroup,
} from "react-simple-maps";

import INDIA_TOPO from "./india.topo.json";

/* Real India states map. The topojson (38 KB) ships inside this chunk, so
   the map renders immediately — no CDN request, no spinner. Every state is
   a hoverable region; the states that have centres are highlighted and
   labelled with their count.

   Above the map, an accessible set of checkboxes lets the viewer show/hide
   each centre state — toggling instantly updates the markers, the
   highlighted regions and the legend. Includes +/- zoom controls, a white
   cursor tooltip, and a screen-reader status line. */

const BRAND = "#184E30";
const PIN = "#155E38";   // pins in professional dark green
const INK = "#1A2820";
const SUB = "#596A5F";
const NO_CENTRE = "#E2EEE5";
const HOVER_NO_CENTRE = "#C8E2D0";

/* Sequential green scale: a state's shade encodes how many centres it has
   (light = few, dark = many) — one cohesive hue, modern choropleth style.
   SCALE_LOW is kept saturated so even a 1-centre state reads clearly as
   green against the neutral light green land. */
const SCALE_LOW = "#6DB589";
const SCALE_HIGH = "#184E30";

const hexToRgb = (h) => {
    const x = h.replace("#", "");
    return [parseInt(x.slice(0, 2), 16), parseInt(x.slice(2, 4), 16), parseInt(x.slice(4, 6), 16)];
};
const mixHex = (a, b, t) => {
    const A = hexToRgb(a);
    const B = hexToRgb(b);
    const c = A.map((v, i) => Math.round(v + (B[i] - v) * t));
    return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
};
const fillForCount = (count, max) => {
    if (!count) return NO_CENTRE;
    const t = max > 1 ? 0.3 + 0.7 * ((count - 1) / (max - 1)) : 0.75;
    return mixHex(SCALE_LOW, SCALE_HIGH, t);
};

/* Approximate label positions (lon, lat) for the count markers. */
const STATE_CENTROIDS = {
    "andhra pradesh": [79.7, 15.9],
    "arunachal pradesh": [94.7, 28.2],
    "assam": [92.9, 26.2],
    "bihar": [85.8, 25.8],
    "chhattisgarh": [82.0, 21.3],
    "goa": [74.1, 15.3],
    "gujarat": [71.8, 22.6],
    "haryana": [76.1, 29.2],
    "himachal pradesh": [77.2, 31.8],
    "jharkhand": [85.3, 23.6],
    "karnataka": [76.0, 15.0],
    "kerala": [76.5, 10.5],
    "madhya pradesh": [78.5, 23.5],
    "maharashtra": [76.5, 19.5],
    "manipur": [93.9, 24.7],
    "meghalaya": [91.3, 25.5],
    "mizoram": [92.8, 23.3],
    "nagaland": [94.5, 26.1],
    "odisha": [84.5, 20.5],
    "punjab": [75.3, 31.0],
    "rajasthan": [74.2, 26.6],
    "sikkim": [88.5, 27.6],
    "tamil nadu": [78.4, 11.1],
    "telangana": [79.0, 17.9],
    "tripura": [91.7, 23.7],
    "uttar pradesh": [80.9, 27.0],
    "uttarakhand": [79.3, 30.1],
    "west bengal": [87.8, 23.8],
    "delhi": [77.1, 28.6],
    "jammu and kashmir": [75.3, 33.5],
    "ladakh": [77.6, 34.2],
    "puducherry": [79.8, 11.9],
    "chandigarh": [76.8, 30.7],
};

const norm = (s) => (s || "").toString().trim().toLowerCase();

/* Canonicalise so map names line up with our data (e.g. "NCT of Delhi"). */
const ALIASES = {
    "nct of delhi": "delhi",
    "orissa": "odisha",
    "pondicherry": "puducherry",
    "uttaranchal": "uttarakhand",
};
const canon = (s) => {
    const n = norm(s);
    if (ALIASES[n]) return ALIASES[n];
    return n.replace(/^nct of /, "").replace(/ & /g, " and ");
};

const geoName = (props = {}) =>
    props.st_nm ||
    props.NAME_1 ||
    props.ST_NM ||
    props.name ||
    props.NAME ||
    "";

const INITIAL = { coordinates: [82.5, 22.3], zoom: 1.0 };

function MapSpinner({ height }) {
    return (
        <div
            className="flex flex-col items-center justify-center gap-3"
            style={{ height }}
        >
            <span className="h-9 w-9 animate-spin rounded-full border-4 border-[#E0EBE2] border-t-[#184E30]" />
            <span className="text-[12px] font-medium text-[#184E30]">
                Loading map...
            </span>
        </div>
    );
}

export default function StateWiseCentresMap({ centres = [], height = 420, onStateClick }) {
    const geoData = INDIA_TOPO;
    const failed = false;
    const [hover, setHover] = useState(null); // { name, total }
    const [cursor, setCursor] = useState({ x: 0, y: 0 });
    const [position, setPosition] = useState(INITIAL);
    const wrapRef = useRef(null);
    const selectAllRef = useRef(null);

    // Highest centre count drives the sequential scale.
    const maxCount = useMemo(
        () => centres.reduce((m, c) => Math.max(m, c.total || 0), 0),
        [centres]
    );

    // Per-state fill (keyed by canonical name) on the sequential green scale.
    const colorByState = useMemo(() => {
        const map = {};
        centres.forEach((c) => {
            map[canon(c.state_name)] = fillForCount(c.total || 0, maxCount);
        });
        return map;
    }, [centres, maxCount]);

    const allKeys = useMemo(
        () => centres.map((c) => canon(c.state_name)),
        [centres]
    );
    const keysSig = allKeys.join("|");

    // Which states are shown. Defaults to all; re-syncs whenever the dashboard
    // filters bring a different set of centres.
    const [selected, setSelected] = useState(() => new Set(allKeys));
    useEffect(() => {
        setSelected(new Set(keysSig ? keysSig.split("|") : []));
    }, [keysSig]);

    const visibleCentres = useMemo(
        () => centres.filter((c) => selected.has(canon(c.state_name))),
        [centres, selected]
    );

    // Index visible centres by canonical state name (with their colour).
    const byState = useMemo(() => {
        const map = {};
        visibleCentres.forEach((c) => {
            const key = canon(c.state_name);
            map[key] = { ...c, color: colorByState[key] };
        });
        return map;
    }, [visibleCentres, colorByState]);

    const allSelected = selected.size === allKeys.length && allKeys.length > 0;
    const noneSelected = selected.size === 0;

    useEffect(() => {
        if (selectAllRef.current) {
            selectAllRef.current.indeterminate = !allSelected && !noneSelected;
        }
    }, [allSelected, noneSelected]);

    const handleStateClick = (stateName) => {
        const coords =
            STATE_CENTROIDS[norm(stateName)] ||
            STATE_CENTROIDS[canon(stateName)];
        if (coords) {
            setPosition({ coordinates: coords, zoom: 2.6 });
        }
        if (onStateClick) {
            onStateClick(stateName);
        }
    };

    const toggle = (key) =>
        setSelected((prev) => {
            const next = new Set(prev);
            if (next.has(key)) next.delete(key);
            else next.add(key);
            return next;
        });

    const toggleAll = () => {
        if (!allSelected) setPosition(INITIAL);
        setSelected(allSelected ? new Set() : new Set(allKeys));
    };

    const zoomIn = () =>
        setPosition((p) => ({ ...p, zoom: Math.min(p.zoom * 1.5, 8) }));
    const zoomOut = () =>
        setPosition((p) => {
            const nextZoom = Math.max(p.zoom / 1.5, 1);
            if (nextZoom <= 1.05) return INITIAL;
            return { ...p, zoom: nextZoom };
        });
    const resetView = () => setPosition(INITIAL);

    const filterZoomEvent = (evt) => {
        // Disable mouse wheel zoom completely so scrolling in/beside the map scrolls the page
        if (evt.type === "wheel") return false;

        // When at base zoom (1x), disable panning so dragging/swiping in blank space doesn't move the map
        if (position.zoom <= 1.05 && (evt.type === "mousedown" || evt.type === "touchstart")) {
            return false;
        }

        return !evt.ctrlKey && !evt.button;
    };

    const onMove = (e) => {
        const rect = wrapRef.current?.getBoundingClientRect();
        if (rect) setCursor({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    };

    if (!geoData && !failed) return <MapSpinner height={height} />;

    const statusText = `Showing ${visibleCentres.length} of ${centres.length} state${centres.length === 1 ? "" : "s"} with centres on the map.`;

    // Keep the tooltip inside the card (flip left near the right edge).
    const cardW = wrapRef.current?.clientWidth || 0;
    const flip = cardW && cursor.x > cardW - 170;

    return (
        <div className="flex h-full w-full flex-col">
            <style>{`
                .swc-chip { display:inline-flex; align-items:center; flex:0 0 auto; gap:5px; border:1px solid #D8E4DB; border-radius:0; padding:4px 8px; font-size:11px; line-height:15px; color:${INK}; background:#fff; cursor:pointer; white-space:nowrap; transition:border-color .15s ease, background .15s ease, opacity .15s ease; }
                .swc-chip-row { scrollbar-width:none; -ms-overflow-style:none; }
                .swc-chip-row::-webkit-scrollbar { display:none; }
                .swc-chip:hover { border-color:#82B996; background:#F2F8F4; }
                .swc-chip[data-on="false"] { opacity:.5; }
                .swc-chip:focus-within { outline:2px solid #184E30; outline-offset:-2px; }
                .swc-cb { width:13px; height:13px; accent-color:#184E30; cursor:pointer; margin:0; }
                .swc-swatch { width:10px; height:10px; border-radius:0; display:inline-block; flex-shrink:0; }
                .swc-count { font-weight:600; color:${SUB}; font-variant-numeric:tabular-nums; }
                .swc-zoom:focus-visible { outline:2px solid #184E30; outline-offset:-2px; }
                .swc-pulse { transform-box:fill-box; transform-origin:center; animation:swc-pulse 2.4s cubic-bezier(.4,0,.6,1) infinite; }
                @keyframes swc-pulse { 0%{ transform:scale(.55); opacity:.5 } 75%{ transform:scale(2); opacity:0 } 100%{ opacity:0 } }
                @media (prefers-reduced-motion: reduce) {
                    .swc-chip { transition:none; }
                    .swc-pulse { animation:none; opacity:0 !important; }
                }
            `}</style>

            {/* Checkbox controls — show / hide each centre state. */}
            <fieldset className="m-0 mb-[10px] min-w-0 shrink-0 border-0 p-0">
                <legend className="sr-only">Show or hide centre states on the map</legend>

                <div className="swc-chip-row flex flex-wrap items-center gap-[8px] pb-[2px]">
                    {centres.length > 1 && (
                        <label className="swc-chip" data-on={allSelected ? "true" : "false"}>
                            <input
                                ref={selectAllRef}
                                type="checkbox"
                                className="swc-cb"
                                checked={allSelected}
                                onChange={toggleAll}
                            />
                            <span className="font-medium">All states</span>
                        </label>
                    )}

                    {centres.map((c) => {
                        const key = canon(c.state_name);
                        const on = selected.has(key);
                        return (
                            <label key={key} className="swc-chip" data-on={on ? "true" : "false"}
                                onMouseEnter={() => on && setHover({ name: c.state_name, total: c.total, key, src: "chip" })}
                                onMouseLeave={() => setHover(null)}>
                                <input
                                    type="checkbox"
                                    className="swc-cb"
                                    checked={on}
                                    onChange={() => toggle(key)}
                                    aria-label={`${c.state_name}: ${c.total} ${c.total === 1 ? "centre" : "centres"}`}
                                />
                                <span
                                    className="swc-swatch"
                                    style={{ background: colorByState[key] }}
                                    aria-hidden="true"
                                />
                                <span>{c.state_name}</span>
                                <span className="swc-count">{c.total}</span>
                            </label>
                        );
                    })}
                </div>
            </fieldset>

            {/* Map */}
            <div
                ref={wrapRef}
                role="group"
                aria-label="Map of India highlighting states that have centres"
                className="relative flex min-h-0 w-full flex-1 items-center justify-center overflow-hidden rounded-none border border-[#E2EBE4] bg-[#F9FAF9]"
                style={{ boxShadow: "inset 0 0 55px rgba(24,78,48,0.04)" }}
                onMouseMove={onMove}
            >
                <ComposableMap
                    projection="geoMercator"
                    projectionConfig={{ scale: height * 2, center: [82.5, 22.3] }}
                    width={Math.round(height * 1.95)}
                    height={height}
                    preserveAspectRatio="xMidYMid meet"
                    style={{ width: "100%", height: "100%" }}
                >
                    <ZoomableGroup
                        zoom={position.zoom}
                        center={position.coordinates}
                        minZoom={1}
                        maxZoom={8}
                        onMoveEnd={setPosition}
                        filterZoomEvent={filterZoomEvent}
                    >
                        <Graticule stroke="#E3ECE5" strokeWidth={0.4} step={[5, 5]} />
                        <Geographies geography={geoData}>
                            {({ geographies }) =>
                                geographies.map((geo) => {
                                    const name = geoName(geo.properties);
                                    const key = canon(name);
                                    const hit = byState[key];
                                    const active = hover && hover.key === key;
                                    return (
                                        <Geography
                                            key={geo.rsmKey}
                                            geography={geo}
                                            onMouseEnter={() =>
                                                setHover({
                                                    name,
                                                    total: hit ? hit.total : 0,
                                                    key,
                                                    src: "map",
                                                })
                                            }
                                            onMouseLeave={() => setHover(null)}
                                            onClick={() =>
                                                hit &&
                                                handleStateClick(hit.state_name || name)
                                            }
                                            style={{
                                                default: {
                                                    fill: hit ? hit.color : (active ? HOVER_NO_CENTRE : NO_CENTRE),
                                                    stroke: active ? "#0D3A20" : "#BED8C4",
                                                    strokeWidth: active ? 1.4 : 0.65,
                                                    outline: "none",
                                                    filter: active && hit ? "brightness(1.10)" : "none",
                                                    transition: "fill .15s ease, stroke .15s ease, filter .15s ease",
                                                },
                                                hover: {
                                                    fill: hit ? hit.color : HOVER_NO_CENTRE,
                                                    stroke: "#0D3A20",
                                                    strokeWidth: 1.4,
                                                    outline: "none",
                                                    filter: hit ? "brightness(1.10)" : "none",
                                                    cursor: hit ? "pointer" : "default",
                                                },
                                                pressed: { outline: "none" },
                                            }}
                                        />
                                    );
                                })
                            }
                        </Geographies>

                        {/* Clean circular count badges (state name shows on hover). */}
                        {visibleCentres.map((c) => {
                            const coords = STATE_CENTROIDS[norm(c.state_name)];
                            if (!coords) return null;
                            const key = canon(c.state_name);
                            const active = hover && hover.key === key;
                            const k = (active ? 0.92 : 0.8) / position.zoom; // pin drawn in unit coords, scaled to screen
                            return (
                                <Marker
                                    key={c.state_name}
                                    coordinates={coords}
                                    onMouseEnter={() => setHover({ name: c.state_name, total: c.total, key, src: "map" })}
                                    onMouseLeave={() => setHover(null)}
                                    onClick={() => handleStateClick(c.state_name)}
                                    style={{
                                        default: { cursor: "pointer", outline: "none" },
                                        hover: { cursor: "pointer", outline: "none" },
                                        pressed: { outline: "none" },
                                    }}
                                >
                                    <g transform={`scale(${k}) translate(0 ${active ? -4 : 0})`} style={{ transition: "transform .18s cubic-bezier(.34,1.56,.64,1)" }}>
                                        {/* pulsing ring around the pin head */}
                                        <circle className="swc-pulse" cx="0" cy="-20" r="13" fill={PIN} opacity={active ? 0.42 : 0.28} style={{ pointerEvents: "none" }} />
                                        {/* ground shadow at the tip */}
                                        <ellipse cx="0" cy="1.5" rx="5" ry="1.8" fill="rgba(24,78,48,0.28)" style={{ pointerEvents: "none" }} />
                                        {/* pin body (tip at 0,0) */}
                                        <path d="M0 0 C -5 -9 -10 -13 -10 -20 A 10 10 0 1 1 10 -20 C 10 -13 5 -9 0 0 Z"
                                            fill={PIN} stroke="#ffffff" strokeWidth="1.6"
                                            style={{ filter: `drop-shadow(0 2px 3px rgba(18,60,36,${active ? 0.55 : 0.40}))` }} />
                                        {/* count in the head */}
                                        <text x="0" y="-20" textAnchor="middle" dominantBaseline="central"
                                            style={{ fontFamily: "inherit", fontSize: 11, fontWeight: 700, fill: "#ffffff", pointerEvents: "none" }}>
                                            {c.total}
                                        </text>
                                    </g>
                                    {/* state name below the pin */}
                                    <text
                                        textAnchor="middle"
                                        y={10 / position.zoom}
                                        style={{
                                            fontFamily: "inherit",
                                            fontSize: 9 / position.zoom,
                                            fontWeight: 600,
                                            fill: INK,
                                            stroke: "#ffffff",
                                            strokeWidth: 2.6 / position.zoom,
                                            paintOrder: "stroke",
                                            pointerEvents: "none",
                                        }}
                                    >
                                        {c.state_name}
                                    </text>
                                </Marker>
                            );
                        })}
                    </ZoomableGroup>
                </ComposableMap>

                {/* Zoom controls (top-left) */}
                <div className="absolute left-3 top-3 z-[10] flex flex-col overflow-hidden rounded-none border border-[#CFDFD4] bg-white shadow-sm">
                    <button
                        type="button"
                        onClick={zoomIn}
                        aria-label="Zoom in"
                        className="swc-zoom flex h-7 w-7 items-center justify-center text-[17px] leading-none text-[#1A2820] transition-colors hover:bg-[#EEF5F0]"
                    >
                        +
                    </button>
                    <div className="h-px bg-[#DFEBE2]" />
                    <button
                        type="button"
                        onClick={zoomOut}
                        aria-label="Zoom out"
                        className="swc-zoom flex h-7 w-7 items-center justify-center text-[19px] leading-none text-[#1A2820] transition-colors hover:bg-[#EEF5F0]"
                    >
                        −
                    </button>
                    {(position.zoom > 1.05 || position.coordinates[0] !== INITIAL.coordinates[0] || position.coordinates[1] !== INITIAL.coordinates[1]) && (
                        <>
                            <div className="h-px bg-[#DFEBE2]" />
                            <button
                                type="button"
                                onClick={resetView}
                                aria-label="Reset map view"
                                title="Reset map view"
                                className="swc-zoom flex h-7 w-7 items-center justify-center text-[13px] leading-none text-[#1A2820] transition-colors hover:bg-[#EEF5F0]"
                            >
                                ⟲
                            </button>
                        </>
                    )}
                </div>

                {/* Simple cursor tooltip (only while hovering the map) */}
                {hover && hover.src === "map" && (
                    <div
                        style={{
                            position: "absolute",
                            left: flip ? cursor.x - 12 : cursor.x + 14,
                            top: cursor.y + 12,
                            transform: flip ? "translateX(-100%)" : "none",
                            background: "#ffffff",
                            border: "1px solid #D2E3D7",
                            borderRadius: 0,
                            padding: "5px 9px",
                            fontSize: 12,
                            boxShadow: "0 4px 12px -4px rgba(24,78,48,0.18)",
                            pointerEvents: "none",
                            whiteSpace: "nowrap",
                            zIndex: 20,
                        }}
                    >
                        <span style={{ fontWeight: 700, color: INK }}>{hover.name}</span>
                        <span style={{ color: SUB }}> · {hover.total} {hover.total === 1 ? "centre" : "centres"}</span>
                    </div>
                )}

                {noneSelected && (
                    <div
                        className="pointer-events-none absolute inset-x-0 bottom-3 flex justify-center"
                        aria-hidden="true"
                    >
                        <span className="rounded-none bg-white/95 px-[12px] py-[5px] text-[11.5px] font-medium text-[#596A5F] shadow-sm">
                            No states selected — tick a box above to show centres.
                        </span>
                    </div>
                )}
            </div>

            {/* Legend + screen-reader status */}
            <div
                className="mt-[10px] flex shrink-0 flex-nowrap items-center gap-x-[16px] overflow-x-auto text-[11.5px]"
                style={{ color: INK }}
            >
                <div className="flex flex-nowrap items-center gap-x-[16px] whitespace-nowrap">
                    <span className="flex items-center gap-[7px]">
                        <span style={{ color: SUB }}>Fewer</span>
                        <span
                            aria-hidden="true"
                            style={{
                                width: 56,
                                height: 10,
                                borderRadius: 3,
                                display: "inline-block",
                                background: `linear-gradient(90deg, ${SCALE_LOW}, ${SCALE_HIGH})`,
                            }}
                        />
                        <span style={{ color: SUB }}>More centres</span>
                    </span>
                    <span className="flex items-center gap-[6px]">
                        <span
                            className="swc-swatch"
                            style={{ background: NO_CENTRE, border: "1px solid #CADECF" }}
                            aria-hidden="true"
                        />
                        No centres
                    </span>
                </div>
            </div>

            <p className="sr-only" role="status" aria-live="polite">
                {statusText}
            </p>
        </div>
    );
}
