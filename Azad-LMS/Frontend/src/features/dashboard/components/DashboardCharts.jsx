import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
    FiChevronRight,
    FiChevronLeft,
    FiAlertTriangle,
    FiClock,
    FiAward,
    FiDownload,
} from "react-icons/fi";
import { FaBuilding, FaFemale } from "react-icons/fa";

import ChartPanel from "./ChartPanel";
import ChartDetailModal from "./ChartDetailModal";
import { INK, SUB, BRAND, formatNumber } from "../hook/dashboardTheme";
import { getParticipantImageUrl } from "@/shared/utils/mediaUrl";
import {
    getStateWiseTrainees,
    getStateWiseTraineeStatus,
    getCentreWiseTrainees,
    getNeedAttentionSummary,
    getNeedAttentionLearners,
    getLearnerActivityDetail,
    getCentreLeaderboard,
    getTopLearners,
    exportNeedAttentionLearners,
    getTraineeStatusDetails,
} from "@/features/dashboard/services/DashboardService";

const StateWiseCentresMap = lazy(() => import("./StateWiseCentresMap"));

/* Strict allowed centre_ids per state so other states' centres never leak */
const STATE_ALLOWED_CENTRES = {
    delhi: new Set([1, 3, 5]),
    ncr: new Set([1, 3, 5]),
    "west bengal": new Set([9, 10]),
    "tamil nadu": new Set([13]),
    rajasthan: new Set([14]),
};

function isCentreInState(stateName, centreId, rowStateName) {
    const targetState = String(stateName || "").trim().toLowerCase();
    const rowState = String(rowStateName || "").trim().toLowerCase();
    const allowedIds = STATE_ALLOWED_CENTRES[targetState];
    const numericId = Number(centreId);

    if (allowedIds) {
        if (!Number.isFinite(numericId) || numericId <= 0) return false;
        return allowedIds.has(numericId) && (!rowState || rowState === targetState);
    }
    return rowState === targetState;
}

/* ------------------------------------------------------------------
   Palette — brand purple ramp + earthy status tones + gold
------------------------------------------------------------------- */
const AGE_COLORS = ["#732269", "#9B4F90", "#BE7FB4"]; // 18-25, 26-35, 36-45
const PERF = { good: "#2E8F66", avg: "#C08A2E", yet: "#978BA8" };
const MUTED = "#53495C";
const HAIR = "#F0EAF0";

/* Format date & time helpers */
const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function formatTimeDisplay(dateStr) {
    if (!dateStr) return "—";
    try {
        const d = new Date(dateStr);
        if (Number.isNaN(d.getTime())) return String(dateStr);
        const day = d.getDate();
        const mon = MONTHS_SHORT[d.getMonth()];
        let hours = d.getHours();
        const minutes = String(d.getMinutes()).padStart(2, "0");
        const ampm = hours >= 12 ? "PM" : "AM";
        hours = hours % 12 || 12;
        return `${hours}:${minutes} ${ampm} · ${day} ${mon}`;
    } catch {
        return String(dateStr);
    }
}

function formatDateDisplay(dateStr) {
    if (!dateStr) return "—";
    try {
        const d = new Date(dateStr);
        if (Number.isNaN(d.getTime())) return String(dateStr);
        const day = d.getDate();
        const mon = MONTHS_SHORT[d.getMonth()];
        const year = d.getFullYear();
        return `${day} ${mon} ${year}`;
    } catch {
        return String(dateStr);
    }
}

function formatTotalSpent(seconds = 0, minutes = 0) {
    const totalSec = Number(seconds) > 0 ? Number(seconds) : (Number(minutes) || 0) * 60;
    if (totalSec <= 0) return "0 min";
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;
    if (h > 0) {
        return m > 0 ? `${h}h ${m}m` : `${h}h`;
    }
    if (m > 0) {
        return `${m} min`;
    }
    return `${s}s`;
}

/* Avatar generator — uses participant uploaded photo or stylized dynamic initials */
function Avatar({ name = "", image = null, id = 0, size = 32 }) {
    const [failed, setFailed] = useState(false);
    const palette = ["#732269", "#2C8FE0", "#0E8C7E", "#2E8F66", "#C08A2E", "#A93FBF", "#D9774B", "#5C6AC4"];
    const str = (name && name !== "Learner" && name !== "Trainee") ? name : String(id || "1");
    let h = 0;
    for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
    const bg = palette[Math.abs(h) % palette.length];

    const initials = name && name !== "Learner" && name !== "Trainee"
        ? name.split(" ").map((w) => w[0]).filter(Boolean).slice(0, 2).join("").toUpperCase()
        : "";

    const mediaUrl = image ? getParticipantImageUrl(image) : null;

    if (mediaUrl && !failed) {
        return (
            <img
                src={mediaUrl}
                alt={name || "Trainee"}
                loading="lazy"
                onError={() => setFailed(true)}
                className="rounded-full object-cover shrink-0"
                style={{ width: size, height: size, border: "1px solid #E3E6ED" }}
            />
        );
    }

    if (initials) {
        return (
            <span
                className="grid place-items-center rounded-full text-white font-bold shrink-0 shadow-sm select-none"
                style={{
                    width: size,
                    height: size,
                    fontSize: `${Math.max(10, Math.round(size * 0.38))}px`,
                    backgroundColor: bg,
                }}
            >
                {initials}
            </span>
        );
    }

    return (
        <span
            className="grid place-items-center rounded-full text-white font-semibold shrink-0"
            style={{
                width: size,
                height: size,
                backgroundColor: bg,
            }}
        >
            <FaFemale size={Math.round(size * 0.52)} />
        </span>
    );
}

const nameCell = (row) => (
    <div className="flex items-center gap-[10px]">
        <Avatar name={row.name} image={row.image} id={row.participant_id} />
        <div>
            <div className="font-semibold text-[#1F1B2E] transition-colors group-hover:text-[#732269] group-hover:underline">{row.name}</div>
            {row.mobile && <div style={{ fontSize: "11px", color: SUB }}>{row.mobile}</div>}
        </div>
    </div>
);

/* Trainee profile card */
function LearnerProfile({ it }) {
    const done = Number(it.completed_modules ?? it.completed_modules_count ?? it.modules ?? 0) || 0;
    const total = Number(it.total_assigned_modules ?? it.total_modules ?? it.total_modules_count ?? it.assigned_modules ?? 0);
    const displayTotal = total > 0 ? total : Math.max(done, 0);
    const pct = displayTotal > 0
        ? Math.min(100, Math.round((done / displayTotal) * 100))
        : (typeof it.module_completion_percentage === "number" && !isNaN(it.module_completion_percentage)
            ? Math.round(it.module_completion_percentage)
            : 0);
    const barBlocks = displayTotal > 0 ? (displayTotal <= 16 ? displayTotal : 10) : 1;
    const filledBlocks = Math.min(barBlocks, Math.round((pct / 100) * barBlocks));
    const totalTimeText = formatTotalSpent(it.totalSec, it.minutes);

    const Field = ({ label, value }) => (
        <div className="min-w-0">
            <div style={{ fontSize: "10px", letterSpacing: "0.07em", textTransform: "uppercase", color: SUB, fontWeight: 600 }}>{label}</div>
            <div className="truncate" style={{ fontSize: "13.5px", color: INK, fontWeight: 600, marginTop: "3px" }}>{value || "—"}</div>
        </div>
    );

    return (
        <div className="overflow-hidden border border-[#ECE6EF] bg-white">
            <div className="flex items-center gap-[16px] bg-[#FAF6FA] p-[16px]">
                <Avatar name={it.name} image={it.image} id={it.participant_id} size={74} />
                <div className="min-w-0">
                    <div style={{ fontFamily: "Lora, serif", fontSize: "22px", fontWeight: 700, color: "#241B2B", lineHeight: 1.15 }}>{it.name}</div>
                    <div style={{ fontSize: "13px", color: SUB, marginTop: "4px" }}>{it.centre}{it.state ? ` · ${it.state}` : ""}</div>
                </div>
                <div className="ml-auto text-right" style={{ flex: "none" }}>
                    <div className="tabular-nums" style={{ fontSize: "30px", fontWeight: 700, color: "#2E8F66", lineHeight: 1 }}>{pct}<span style={{ fontSize: "15px", color: SUB, fontWeight: 500 }}>%</span></div>
                    <div style={{ fontSize: "10.5px", color: SUB, marginTop: "2px" }}>Overall completion</div>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-x-[20px] gap-y-[14px] border-t border-[#F0EAF0] p-[16px] sm:grid-cols-5">
                <Field label="Centre" value={it.centre} />
                <Field label="State" value={it.state} />
                <Field
                    label="Overall Score"
                    value={
                        (it.assessment_percentage != null && !isNaN(Number(it.assessment_percentage))) || (it.scorePct != null && !isNaN(Number(it.scorePct)))
                            ? (() => {
                                const rawPct = Number(it.assessment_percentage ?? it.scorePct ?? 0);
                                const pctStr = Number.isInteger(rawPct) ? String(rawPct) : rawPct.toFixed(2);
                                if (it.obtained_marks != null && it.total_marks != null && Number(it.total_marks) > 0) {
                                    const om = Number(it.obtained_marks);
                                    const tm = Number(it.total_marks);
                                    const omStr = Number.isInteger(om) ? String(om) : om.toFixed(2);
                                    const tmStr = Number.isInteger(tm) ? String(tm) : tm.toFixed(2);
                                    return `${pctStr}% (${omStr}/${tmStr})`;
                                }
                                return `${pctStr}%`;
                            })()
                            : it.score != null
                                ? `${it.score} pts`
                                : "—"
                    }
                />
                <Field label="Last active" value={it.time} />
                <Field label="Total learning time" value={totalTimeText} />
            </div>
            <div className="border-t border-[#F0EAF0] p-[16px]">
                <div className="mb-[8px] flex items-center justify-between">
                    <span style={{ fontSize: "10px", letterSpacing: "0.07em", textTransform: "uppercase", color: SUB, fontWeight: 600 }}>Modules completed</span>
                    <span className="tabular-nums" style={{ fontSize: "12.5px", fontWeight: 700, color: INK }}>{done} of {displayTotal}</span>
                </div>
                <div className="flex items-center gap-[4px]" style={{ height: 12 }}>
                    {Array.from({ length: barBlocks }).map((_, i) => (
                        <span key={i} className="flex-1" style={{ height: "100%", background: i < filledBlocks ? BRAND : "#ECE6EF" }} />
                    ))}
                </div>
            </div>
        </div>
    );
}

/* Section Card */
function SectionCard({ title, action, className = "", style, children }) {
    return (
        <div
            className={`flex flex-col overflow-hidden border border-[#ECE6EF] bg-white shadow-[0_1px_2px_rgba(36,27,43,0.05),0_12px_26px_-20px_rgba(36,27,43,0.26)] rounded-none ${className}`}
            style={{ borderRadius: 0, ...style }}
        >
            <div className="flex shrink-0 items-center justify-between gap-[8px] px-[14px] py-[5px] min-h-[34px]" style={{ backgroundColor: "#732269" }}>
                <h3
                    className="m-0 min-w-0 truncate font-semibold"
                    style={{
                        fontFamily: "Lora, serif",
                        color: "#FFFFFF",
                        fontSize: "13.5px",
                        lineHeight: "18px",
                    }}
                >
                    {title}
                </h3>
                {action}
            </div>
            <div className="min-h-0 flex-1 px-[16px] pb-[16px] pt-[14px]">
                {children}
            </div>
        </div>
    );
}

/* ---- Trainees at a glance (vertical bars by state; clicking state shows its centres) ---- */
const TRAINEE_BAR_COLORS = ["#732269", "#2C8FE0", "#C08A2E", "#2E8F66", "#D9774B"];
function TraineesBars({ data, total, onBar, drillLabel, onBack }) {
    const [hover, setHover] = useState(null);
    const rawMax = data.reduce((m, d) => Math.max(m, d.total), 0) || 1;
    const niceMax = Math.max(50, Math.ceil(rawMax / 50) * 50);
    const ticks = [niceMax, Math.round((niceMax * 2) / 3), Math.round(niceMax / 3), 0];
    const interactive = Boolean(onBar);

    return (
        <div className="flex h-full min-h-0 flex-col">
            {drillLabel ? (
                <div className="mb-[12px] flex flex-wrap items-center gap-x-[9px] gap-y-[4px]">
                    <button
                        type="button"
                        onClick={onBack}
                        className="flex items-center gap-[2px] border border-[#ECE6EF] py-[3px] pl-[5px] pr-[8px] transition-colors hover:bg-[#FBF8FB]"
                        style={{ fontSize: "11px", fontWeight: 600, color: BRAND }}
                    >
                        <FiChevronLeft size={14} /> All states
                    </button>
                    <span style={{ fontSize: "13.5px", fontWeight: 600, color: "#2E2340" }}>{drillLabel}</span>
                    <span className="tabular-nums" style={{ fontSize: "11.5px", color: SUB }}>· {formatNumber(total)} trainees</span>
                </div>
            ) : (
                <div className="mb-[12px] flex items-baseline gap-[8px]">
                    <span className="tabular-nums" style={{ color: INK, fontSize: "30px", fontWeight: 700, lineHeight: 1, letterSpacing: "-0.02em" }}>{formatNumber(total)}</span>
                    <span style={{ color: SUB, fontSize: "12px" }}>trainees enrolled</span>
                </div>
            )}

            <div className="flex min-h-0 flex-1 gap-[9px] pt-[26px]">
                <div className="flex flex-col justify-between pb-[1px] text-right" style={{ width: 22 }}>
                    {ticks.map((v, i) => (
                        <span key={i} className="tabular-nums" style={{ fontSize: "9.5px", lineHeight: 1, color: "#A89CB1" }}>{v}</span>
                    ))}
                </div>
                <div className="relative flex flex-1 items-end gap-[8px] sm:gap-[12px]" style={{ minHeight: 150 }}>
                    <div className="pointer-events-none absolute inset-0 flex flex-col justify-between">
                        {[0, 1, 2, 3].map((g) => (<div key={g} style={{ borderTop: "1px dashed #EFE9F0" }} />))}
                    </div>
                    {data.map((d, i) => {
                        const pct = Math.round((d.total / (total || 1)) * 100);
                        return (
                            <div
                                key={d.centre_id ?? d.name}
                                role={interactive ? "button" : undefined}
                                tabIndex={interactive ? 0 : undefined}
                                onMouseEnter={() => setHover(i)}
                                onMouseLeave={() => setHover(null)}
                                onClick={() => interactive && onBar(d)}
                                onKeyDown={(e) => interactive && (e.key === "Enter" || e.key === " ") && onBar(d)}
                                className={`group relative z-[1] flex h-full flex-1 flex-col items-center justify-end ${interactive ? "cursor-pointer" : "cursor-default"}`}
                            >
                                {hover === i && (
                                    <div className="pointer-events-none absolute bottom-full left-1/2 z-[20] mb-[5px] -translate-x-1/2 whitespace-nowrap rounded-[4px] border border-[#ECE6EF] bg-white px-[10px] py-[6px] text-center shadow-[0_10px_24px_-10px_rgba(36,27,43,0.35)]">
                                        <div style={{ fontSize: "11px", fontWeight: 700, color: INK }}>{d.name}</div>
                                        <div className="tabular-nums" style={{ fontSize: "10.5px", color: SUB, marginTop: "1px" }}>{d.total} trainees · {pct}%</div>
                                    </div>
                                )}
                                <span className="mb-[6px] tabular-nums" style={{ fontSize: "12px", fontWeight: 700, color: INK }}>{d.total}</span>
                                <div
                                    className={`w-full transition-[filter] duration-150 ${interactive ? "group-hover:brightness-110" : ""}`}
                                    style={{
                                        maxWidth: 42,
                                        height: `${d.total > 0 ? Math.max(3, (d.total / niceMax) * 100) : 0}%`,
                                        background: d.total > 0 ? TRAINEE_BAR_COLORS[i % TRAINEE_BAR_COLORS.length] : "transparent",
                                        transformOrigin: "bottom",
                                    }}
                                />
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="mt-[10px] flex gap-[9px] border-t border-[#EDEAF2] pt-[9px]">
                <div style={{ width: 22 }} />
                <div className="flex flex-1 gap-[8px] sm:gap-[12px]">
                    {data.map((d) => (
                        <div
                            key={d.centre_id ?? d.name}
                            onClick={() => interactive && onBar(d)}
                            className={`flex flex-col items-center justify-start min-w-0 flex-1 text-center px-0.5 ${interactive ? "cursor-pointer" : "cursor-default"}`}
                        >
                            <div
                                className={`w-full text-center text-[#2E2340] leading-[1.2] transition-colors ${interactive ? "hover:text-[#732269]" : ""}`}
                                style={{ fontSize: "11px", fontWeight: 600, wordBreak: "break-word" }}
                                title={d.name}
                            >
                                {d.name}
                            </div>
                            <div
                                className="tabular-nums text-[#8A7B94] leading-tight"
                                style={{ fontSize: "9.5px", marginTop: "3px", whiteSpace: "nowrap" }}
                            >
                                {Math.round((d.total / (total || 1)) * 100)}% of total
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

/* ---- Age group (donut + breakdown table) ---- */
function AgeDonut({ data, total }) {
    const [hv, setHv] = useState(null);
    let acc = 0;
    const segs = data.map((d, i) => {
        const val = Number(d.total) || 0;
        const pct = total ? (val / total) * 100 : 0;
        const seg = { color: AGE_COLORS[i % AGE_COLORS.length], len: pct, off: -acc, label: d.age_group, val, pct };
        acc += pct;
        return seg;
    });
    const active = hv != null ? segs[hv] : null;
    const R = 15.9155;
    const th = { textAlign: "left", fontSize: "9.5px", letterSpacing: "0.1em", textTransform: "uppercase", color: SUB, fontWeight: 600, padding: "0 4px 7px", borderBottom: "1px solid #E9E2EA" };
    const td = { padding: "11px 4px", borderBottom: "1px solid #F0EAF0" };
    return (
        <div className="flex h-full flex-col items-center">
            <div className="relative" style={{ width: 240, height: 240, flex: "none" }}>
                <svg viewBox="0 0 42 42" width="240" height="240">
                    <circle cx="21" cy="21" r="15.9155" fill="none" stroke={HAIR} strokeWidth="6.5" />
                    {segs.map((s, i) => (
                        <circle
                            key={i}
                            cx="21"
                            cy="21"
                            r="15.9155"
                            fill="none"
                            stroke={s.color}
                            strokeWidth={hv === i ? 9 : 6.5}
                            opacity={hv != null && hv !== i ? 0.4 : 1}
                            style={{ cursor: "pointer", transition: "stroke-width .15s ease, opacity .15s ease" }}
                            onMouseEnter={() => setHv(i)}
                            onMouseLeave={() => setHv(null)}
                            pathLength="100"
                            strokeDasharray={`${s.len} ${100 - s.len}`}
                            strokeDashoffset={s.off}
                            transform="rotate(-90 21 21)"
                        />
                    ))}
                    {segs.map((s, i) => {
                        if (s.pct < 4) return null;
                        const midFrac = (-s.off + s.len / 2) / 100;
                        const a = (-90 + midFrac * 360) * (Math.PI / 180);
                        return (
                            <text
                                key={`l${i}`}
                                x={21 + R * Math.cos(a)}
                                y={21 + R * Math.sin(a)}
                                textAnchor="middle"
                                dominantBaseline="central"
                                fontSize="3.3"
                                fontWeight="700"
                                fill="#fff"
                                stroke="#3A2140"
                                strokeWidth="0.7"
                                paintOrder="stroke"
                                style={{ pointerEvents: "none" }}
                            >
                                {Math.round(s.pct)}%
                            </text>
                        );
                    })}
                </svg>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
                    {active ? (
                        <>
                            <b className="tabular-nums" style={{ fontSize: "26px", fontWeight: 700, color: INK, letterSpacing: "-0.02em", lineHeight: 1 }}>{Math.round(active.pct)}%</b>
                            <span className="flex items-center gap-[5px]" style={{ fontSize: "10.5px", fontWeight: 600, color: INK, marginTop: "5px" }}>
                                <i style={{ width: 8, height: 8, background: active.color, display: "inline-block" }} />{active.label}
                            </span>
                            <span className="tabular-nums" style={{ fontSize: "10px", color: SUB, marginTop: "1px" }}>{active.val} trainees</span>
                        </>
                    ) : (
                        <>
                            <b className="tabular-nums" style={{ fontSize: "31px", fontWeight: 700, color: INK, letterSpacing: "-0.02em", lineHeight: 1 }}>{formatNumber(total)}</b>
                            <span style={{ fontSize: "9.5px", color: SUB, textTransform: "uppercase", letterSpacing: "0.08em", marginTop: "3px" }}>Trainees</span>
                        </>
                    )}
                </div>
            </div>

            <table className="mt-[16px] w-full" style={{ borderCollapse: "collapse", fontSize: "12.5px" }}>
                <thead><tr><th style={th}>Age band</th><th style={{ ...th, textAlign: "right" }}>Count</th><th style={{ ...th, textAlign: "right" }}>Share</th></tr></thead>
                <tbody>
                    {segs.map((s, i) => (
                        <tr
                            key={i}
                            onMouseEnter={() => setHv(i)}
                            onMouseLeave={() => setHv(null)}
                            style={{ cursor: "pointer", background: hv === i ? "#FAF5FA" : "transparent", transition: "background .12s ease" }}
                        >
                            <td style={td}><span style={{ display: "inline-block", width: 10, height: 10, marginRight: 8, background: s.color, verticalAlign: "middle" }} />{s.label}</td>
                            <td className="tabular-nums" style={{ ...td, textAlign: "right", fontWeight: 700, color: INK }}>{s.val}</td>
                            <td style={td}>
                                <div className="flex items-center justify-end gap-[8px]">
                                    <span className="relative inline-block" style={{ width: 34, height: 5, background: "#F0EAF0", flex: "none" }}>
                                        <span className="absolute left-0 top-0 h-full" style={{ width: `${s.pct}%`, background: s.color }} />
                                    </span>
                                    <span className="tabular-nums" style={{ color: INK, fontWeight: 600, minWidth: 26, textAlign: "right" }}>{Math.round(s.pct)}%</span>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

/* ---- Performance distribution ---- */
function PerfBars({ data, onSeg }) {
    const [hv, setHv] = useState(null);
    const [hidden] = useState(() => new Set());
    const cats = [
        { key: "Good", label: "Good", color: PERF.good },
        { key: "Average", label: "Average", color: PERF.avg },
        { key: "Yet", label: "Yet to start", color: PERF.yet },
    ];
    const isVis = (key) => !hidden.has(key);
    const topToBottom = [cats[2], cats[1], cats[0]];
    const vTotal = (d) => cats.reduce((s, c) => s + (isVis(c.key) ? (Number(d[c.key]) || 0) : 0), 0);
    const rawMax = data.reduce((m, d) => Math.max(m, vTotal(d)), 0) || 1;
    const step = rawMax <= 40 ? 20 : 50;
    const niceMax = Math.max(step, Math.ceil(rawMax / step) * step);
    const ticks = [niceMax, Math.round((niceMax * 2) / 3), Math.round(niceMax / 3), 0];
    return (
        <div className="flex h-full min-h-0 flex-col">
            <div className="mb-[12px] flex flex-wrap gap-x-[16px] gap-y-[4px]">
                {cats.map((c) => {
                    const catTotal = data.reduce((sum, d) => sum + (Number(d[c.key]) || 0), 0);
                    return (
                        <button
                            key={c.key}
                            type="button"
                            onClick={() => onSeg && onSeg(null, c.label, catTotal)}
                            className="flex items-center gap-[6px] transition-all hover:opacity-75 cursor-pointer"
                            title={`Click to view all ${c.label} learners (${catTotal})`}
                        >
                            <i style={{ width: 10, height: 10, background: c.color, display: "inline-block" }} />
                            <span style={{ fontSize: "11.5px", color: MUTED, fontWeight: 500 }}>{c.label}</span>
                        </button>
                    );
                })}
            </div>

            <div className="flex min-h-0 flex-1 gap-[9px] pt-[26px]">
                <div className="flex flex-col justify-between pb-[1px] text-right" style={{ width: 22 }}>
                    {ticks.map((v, i) => (
                        <span key={i} className="tabular-nums" style={{ fontSize: "9.5px", lineHeight: 1, color: "#A89CB1" }}>{v}</span>
                    ))}
                </div>
                <div className="relative flex flex-1 items-end gap-[8px] sm:gap-[12px]" style={{ minHeight: 150 }}>
                    <div className="pointer-events-none absolute inset-0 flex flex-col justify-between">
                        {[0, 1, 2, 3].map((g) => (<div key={g} style={{ borderTop: "1px dashed #EFE9F0" }} />))}
                    </div>
                    {data.map((d, si) => {
                        const vt = vTotal(d);
                        return (
                            <div key={d.state} className="relative z-[1] flex h-full flex-1 flex-col items-center justify-end">
                                {hv && hv.s === si && (
                                    <div className="pointer-events-none absolute bottom-full left-1/2 z-[6] mb-[7px] -translate-x-1/2 whitespace-nowrap border border-[#ECE6EF] bg-white px-[9px] py-[5px] text-center shadow-[0_10px_24px_-10px_rgba(36,27,43,0.35)]">
                                        <div style={{ fontSize: "11px", fontWeight: 700, color: INK }}>{d.state}</div>
                                        <div className="tabular-nums" style={{ fontSize: "10.5px", color: SUB, marginTop: "1px" }}>{hv.label}: {hv.val} · click to view</div>
                                    </div>
                                )}
                                <span className="mb-[6px] tabular-nums" style={{ fontSize: "12px", fontWeight: 700, color: INK }}>{vt}</span>
                                <div className="flex w-full flex-col justify-end" style={{ maxWidth: 42, height: `${vt > 0 ? Math.max(2, (vt / niceMax) * 100) : 0}%` }}>
                                    {topToBottom.filter((c) => isVis(c.key)).map((c) => {
                                        const val = Number(d[c.key]) || 0;
                                        if (val <= 0) return null;
                                        const on = hv && hv.s === si && hv.key === c.key;
                                        return (
                                            <div
                                                key={c.key}
                                                onMouseEnter={() => setHv({ s: si, key: c.key, label: c.label, val })}
                                                onMouseLeave={() => setHv(null)}
                                                onClick={() => onSeg && onSeg(d.state, c.label, val)}
                                                className="w-full cursor-pointer transition-[filter] duration-150 hover:brightness-110"
                                                style={{ height: `${(val / vt) * 100}%`, minHeight: 6, background: c.color, filter: on ? "brightness(1.12)" : "none" }}
                                            />
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="mt-[10px] flex gap-[9px] border-t border-[#EDEAF2] pt-[9px]">
                <div style={{ width: 22 }} />
                <div className="flex flex-1 gap-[8px] sm:gap-[12px]">
                    {data.map((d) => (
                        <div key={d.state} className="flex flex-col items-center justify-start min-w-0 flex-1 text-center px-0.5">
                            <div
                                className="w-full text-center text-[#2E2340] leading-[1.2]"
                                style={{ fontSize: "11px", fontWeight: 600, wordBreak: "break-word" }}
                                title={d.state}
                            >
                                {d.state}
                            </div>
                            <div
                                className="tabular-nums text-[#8A7B94] leading-tight"
                                style={{ fontSize: "9.5px", marginTop: "3px", whiteSpace: "nowrap" }}
                            >
                                {d.total ?? vTotal(d)} total
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

/* ---- Need attention (follow-up alerts) ---- */
function NeedAttention({ att, onOpen }) {
    const Row = ({ kind, color, bg, borderColor, n, label, ico }) => (
        <button
            type="button"
            onClick={() => onOpen && onOpen(kind)}
            className="group flex w-full items-center gap-[14px] border p-[14px] text-left transition-all hover:-translate-y-[1px] hover:shadow-[0_10px_22px_-10px_rgba(36,27,43,0.4)] rounded-none"
            style={{ background: bg, borderColor: borderColor, borderRadius: 0 }}
        >
            <span className="grid place-items-center rounded-full" style={{ width: 44, height: 44, flex: "none", background: color, color: "#fff" }}>{ico}</span>
            <div className="min-w-0 flex-1">
                <div className="tabular-nums" style={{ fontSize: "26px", fontWeight: 700, color, lineHeight: 1, letterSpacing: "-0.02em" }}>
                    {formatNumber(n)} <span style={{ fontSize: "12px", fontWeight: 600, color: "#6B6478", letterSpacing: 0 }}>learners</span>
                </div>
                <div style={{ fontSize: "12px", fontWeight: 500, color: "#4A4356", marginTop: "4px" }}>{label}</div>
            </div>
            <span className="flex items-center gap-[3px] whitespace-nowrap transition-all group-hover:gap-[6px]" style={{ fontSize: "11.5px", fontWeight: 700, color }}>
                View list <FiChevronRight size={13} />
            </span>
        </button>
    );
    return (
        <SectionCard title="Need Attention">
            <div className="flex flex-col gap-[10px]">
                <Row kind="never" color="#E0574B" bg="#FDE8E4" borderColor="#F3C0BA" n={att.never_logged_in} label="Never logged in since enrolment" ico={<FiAlertTriangle size={20} />} />
                <Row kind="inactive" color="#E8963D" bg="#FDF2DF" borderColor="#F3D5A0" n={att.inactive_30d} label="No activity in the last 30 days" ico={<FiClock size={20} />} />
                <div style={{ fontSize: "11.5px", color: SUB }}>Lists open centre-wise so field staff can follow up directly.</div>
            </div>
        </SectionCard>
    );
}

/* Top learners — ranked by assessment score + learning time (/dashboard/top-learners) */
function TopLearners({ items = [], onOpen, loading = false }) {
    return (
        <SectionCard title="Top learners">
            {loading ? (
                <div className="flex flex-col gap-[14px] py-[8px]">
                    {[1, 2, 3, 4, 5].map((k) => (
                        <div key={k} className="flex items-center gap-[12px] animate-pulse">
                            <span className="h-[38px] w-[38px] rounded-full bg-[#EBE7F1]" />
                            <div className="flex-1 space-y-1.5">
                                <span className="block h-[13px] w-24 bg-[#EBE7F1]" />
                                <span className="block h-[10px] w-16 bg-[#F4F2F7]" />
                            </div>
                            <span className="h-[12px] w-12 bg-[#F4F2F7]" />
                        </div>
                    ))}
                </div>
            ) : items.length === 0 ? (
                <div className="py-[24px] text-center text-[12px] text-[#8A7B94]">
                    No learner assessment scores recorded yet.
                </div>
            ) : (
                <div className="flex flex-col">
                    {items.slice(0, 5).map((it, i) => {
                        const rank = it.rank ?? (i + 1);
                        const participantId = it.participant_id || it.id;
                        const name = (it.name || it.participant_name || `Learner ${i + 1}`).trim();
                        const centre = it.centre || it.centre_name || "—";
                        const state = it.state || it.state_name || "";
                        const rawPct = Number(it.assessment_percentage ?? 0);
                        const pct = Number.isInteger(rawPct) ? String(rawPct) : rawPct.toFixed(2);
                        const timeSpentStr = formatTotalSpent(it.totalSec, it.minutes);

                        return (
                            <button
                                type="button"
                                key={participantId || i}
                                onClick={() => onOpen && onOpen({ ...it, rank, participant_id: participantId, name, centre, state })}
                                className="group relative flex w-full items-center gap-[12px] py-[10px] text-left transition-colors first:pt-0 last:pb-0 hover:bg-[#FBF8FB]"
                            >
                                <div className="relative shrink-0 flex items-center gap-[10px]">
                                    <div
                                        className="flex items-center justify-center font-bold text-[12px] tabular-nums"
                                        style={{
                                            width: 22,
                                            height: 22,
                                            borderRadius: "50%",
                                            background: rank === 1 ? "#FFF4DE" : rank === 2 ? "#EDF0F3" : rank === 3 ? "#F9ECE0" : "#F4F0F7",
                                            color: rank === 1 ? "#A3720E" : rank === 2 ? "#55606B" : rank === 3 ? "#8E5421" : "#732269",
                                            border: rank === 1 ? "1.5px solid #F3CF7A" : rank === 2 ? "1.5px solid #C4CBD3" : rank === 3 ? "1.5px solid #DCB38D" : "1px solid #E3DCE7",
                                        }}
                                        title={`Rank ${rank}`}
                                    >
                                        {rank}
                                    </div>
                                    <Avatar name={name} image={it.image} id={participantId || i} size={38} />
                                </div>

                                <div className="min-w-0 flex-1">
                                    <b
                                        className="truncate text-[#1F1B2E] transition-colors group-hover:text-[#732269]"
                                        style={{ fontSize: "13.5px", fontWeight: 600, display: "block", lineHeight: 1.25 }}
                                    >
                                        {name}
                                    </b>
                                    <div className="flex items-center gap-[6px] truncate" style={{ fontSize: "11.5px", color: SUB, marginTop: "2px" }}>
                                        <span>{centre}</span>
                                        {state && (
                                            <>
                                                <span className="text-[#D9D3E0]">·</span>
                                                <span>{state}</span>
                                            </>
                                        )}
                                    </div>
                                </div>

                                <div className="flex shrink-0 items-center gap-[6px] whitespace-nowrap">
                                    <span
                                        className="inline-flex items-center gap-[4px] font-semibold tabular-nums"
                                        style={{ fontSize: "11px", color: BRAND, background: "#F5EEF3", padding: "2px 7px" }}
                                        title={`Total time spent: ${timeSpentStr}`}
                                    >
                                        <FiClock size={10} />
                                        <span>{timeSpentStr}</span>
                                    </span>
                                    <span style={{ color: "#D9D3E0" }}>|</span>
                                    <span
                                        className="tabular-nums font-bold"
                                        style={{ fontSize: "15px", color: "#2E8F66", lineHeight: 1 }}
                                    >
                                        {pct}<span style={{ fontSize: "10px", color: SUB, fontWeight: 500 }}>%</span>
                                    </span>
                                </div>
                            </button>
                        );
                    })}
                </div>
            )}
        </SectionCard>
    );
}

/* Medal renderer */
function starPath(cx, cy, R, r) {
    let d = "";
    for (let i = 0; i < 10; i++) {
        const a = (Math.PI / 5) * i - Math.PI / 2;
        const rr = i % 2 === 0 ? R : r;
        d += (i === 0 ? "M" : "L") + (cx + rr * Math.cos(a)).toFixed(1) + " " + (cy + rr * Math.sin(a)).toFixed(1);
    }
    return d + "Z";
}

function Medal({ m, rank, winner }) {
    return (
        <svg width={winner ? 70 : 52} viewBox="0 0 64 62" fill="none" aria-hidden="true">
            <polygon points="24,2 33,2 38,30 29,30" fill={m.d} />
            <polygon points="40,2 31,2 26,30 35,30" fill={m.m} />
            {winner && (
                <g stroke={m.m} strokeWidth="1.8" fill="none" strokeLinecap="round" opacity="0.92">
                    <path d="M13 58 Q3 46 8 31" />
                    <path d="M11 52 Q7 51 6 47" /><path d="M11 46 Q7.5 45 7 41" /><path d="M12 40 Q9 39 9 35" />
                    <path d="M51 58 Q61 46 56 31" />
                    <path d="M53 52 Q57 51 58 47" /><path d="M53 46 Q56.5 45 57 41" /><path d="M52 40 Q55 39 55 35" />
                </g>
            )}
            <circle cx="32" cy="44" r="15" fill={m.tint} stroke={m.m} strokeWidth="2.5" />
            <circle cx="32" cy="44" r="11" fill="none" stroke={m.m} strokeWidth="1" opacity="0.45" />
            {winner
                ? <path d={starPath(32, 44, 7.6, 3.1)} fill={m.m} />
                : <text x="32" y="45" textAnchor="middle" dominantBaseline="central" fontSize="16" fontWeight="700" fill={m.m} style={{ fontFamily: "Poppins, sans-serif" }}>{rank}</text>}
        </svg>
    );
}

/* Top performing centres — display only, clicking a centre does nothing */
function TopPerformers({ items = [] }) {
    const at = (r) => items.find((x) => x.rank === r) || items[r - 1] || {};

    const C = { p: "#732269", g: "#C79A3A", s: "#9AA1A9", b: "#B07A4B", e: "#2E8F66" };
    const CONF = [
        { x: 58, y: 42, w: 7, h: 7, r: 20, c: C.p }, { x: 95, y: 16, w: 2, h: 12, r: 35, c: C.g },
        { x: 128, y: 56, t: 1, r: 0, c: C.e }, { x: 150, y: 24, w: 6, h: 6, r: 50, c: C.s },
        { x: 184, y: 10, w: 2, h: 11, r: -25, c: C.b }, { x: 206, y: 44, w: 7, h: 7, r: 15, c: C.g },
        { x: 230, y: 20, t: 1, r: 30, c: C.p }, { x: 250, y: 6, w: 6, h: 6, r: 40, c: C.e },
        { x: 262, y: 34, w: 2, h: 13, r: 0, c: C.g }, { x: 276, y: 12, w: 7, h: 7, r: 25, c: C.s },
        { x: 290, y: 4, t: 1, r: -20, c: C.p }, { x: 302, y: 30, w: 2, h: 12, r: 20, c: C.b },
        { x: 320, y: 48, w: 6, h: 6, r: 45, c: C.g }, { x: 336, y: 15, t: 1, r: 10, c: C.e },
        { x: 360, y: 28, w: 7, h: 7, r: 30, c: C.p }, { x: 390, y: 12, w: 2, h: 11, r: -30, c: C.s },
        { x: 414, y: 50, t: 1, r: 15, c: C.b }, { x: 436, y: 24, w: 6, h: 6, r: 20, c: C.g },
        { x: 460, y: 38, w: 2, h: 12, r: 40, c: C.p }, { x: 120, y: 30, t: 1, r: -15, c: C.g },
        { x: 170, y: 58, w: 6, h: 6, r: 35, c: C.p }, { x: 482, y: 16, w: 7, h: 7, r: 25, c: C.e },
    ];

    const Col = ({ it, rank, m, ped, winner }) => (
        <div
            className="relative flex min-w-0 flex-col items-center px-[6px] text-center select-none"
            style={{ zIndex: 1 }}
        >
            <div className="grid place-items-center" style={{ height: 26 }}>
                {winner && <FiAward size={22} style={{ color: m.m }} />}
            </div>
            <div className="relative grid place-items-center" style={{ height: winner ? 70 : 58 }}>
                {winner && (
                    <svg className="pointer-events-none absolute" style={{ width: 124, height: 124, left: "50%", top: "50%", transform: "translate(-50%,-50%)", zIndex: 0 }} viewBox="0 0 120 120" aria-hidden="true">
                        {Array.from({ length: 12 }).map((_, i) => (
                            <path key={i} d="M60 60 L56 12 L64 12 Z" fill={m.m} opacity="0.09" transform={`rotate(${i * 30} 60 60)`} />
                        ))}
                    </svg>
                )}
                <div className="relative" style={{ zIndex: 2 }}><Medal m={m} rank={rank} winner={winner} /></div>
            </div>
            <div className="mt-[6px] w-full truncate text-[#1F1B2E]" style={{ fontSize: "12.5px", fontWeight: 600, lineHeight: 1.25 }}>{it.centre || "—"}</div>
            <div className="w-full truncate" style={{ fontSize: "10.5px", color: SUB, marginTop: "1px" }}>{it.state || ""}</div>
            <div className="tabular-nums" style={{ marginTop: "6px", fontSize: winner ? "24px" : "20px", fontWeight: 700, letterSpacing: "-0.02em", color: INK, lineHeight: 1 }}>
                {it.completion ?? 0}<span style={{ fontSize: "11px", fontWeight: 500, color: SUB }}>%</span>
            </div>
            <div style={{ fontSize: "10.5px", color: MUTED, marginTop: "1px" }}>{it.active ?? 0} active</div>
            <div className="relative -mx-[6px] mt-[11px] flex w-[calc(100%+12px)] items-center justify-center" style={{ height: ped, paddingTop: 12 }}>
                <svg width="100%" height={ped} viewBox={`0 0 100 ${ped}`} preserveAspectRatio="none" style={{ position: "absolute", inset: 0 }} aria-hidden="true">
                    <polygon points="0,12 9,0 91,0 100,12" fill="#8E3C84" />
                    <rect x="0" y="12" width="100" height={ped - 12} fill="#732269" />
                    <rect x="0" y="12" width="100" height={3} fill={m.bar} />
                    <line x1="9" y1="0" x2="0" y2="12" stroke="#5F1B57" strokeWidth="1" />
                    <line x1="91" y1="0" x2="100" y2="12" stroke="#5F1B57" strokeWidth="1" />
                    <line x1="0" y1="12" x2="0" y2={ped} stroke="#5F1B57" strokeWidth="1" />
                    <line x1="100" y1="12" x2="100" y2={ped} stroke="#5F1B57" strokeWidth="1" />
                    <rect x="0" y={ped - 2} width="100" height="2" fill="#4A1443" />
                </svg>
                <span className="relative z-[1] select-none text-[22px] font-bold leading-none text-white opacity-95" style={{ fontFamily: "Lora, serif" }}>{rank}</span>
            </div>
        </div>
    );

    const FloorCard = ({ it }) => (
        <div
            className="flex h-[180px] w-full flex-col items-center border border-[#ECE6EF] bg-white p-[11px] text-center select-none"
        >
            <span
                className="grid shrink-0 place-items-center !rounded-none bg-[#FAF6FA] text-[#732269]"
                style={{ width: 26, height: 26 }}
            >
                <FaBuilding size={12} />
            </span>

            <div
                className="mt-[7px] w-full whitespace-normal break-words font-semibold leading-[1.3] text-[#1F1B2E]"
                style={{
                    fontSize: "11.5px",
                    minHeight: "30px",
                    overflowWrap: "anywhere",
                }}
            >
                {it.centre}
            </div>

            <div
                className="w-full whitespace-normal break-words"
                style={{
                    fontSize: "10px",
                    color: SUB,
                    marginTop: "2px",
                    minHeight: "14px",
                }}
            >
                {it.state}
            </div>

            <div
                className="tabular-nums"
                style={{
                    fontSize: "18px",
                    fontWeight: 700,
                    color: INK,
                    marginTop: "7px",
                    lineHeight: 1,
                }}
            >
                {it.completion}
                <span style={{ fontSize: "10px", fontWeight: 500, color: SUB }}>%</span>
            </div>

            <div className="mt-[9px] h-[3px] w-full bg-[#F3EEF4]">
                <div
                    style={{
                        width: `${Math.min(100, it.completion)}%`,
                        height: "100%",
                        background: BRAND,
                    }}
                />
            </div>

            <div
                className="mt-auto flex w-full items-center justify-between gap-[3px] pt-[8px]"
                style={{ fontSize: "9.5px", color: SUB }}
            >
                <span className="whitespace-nowrap">{it.active} active</span>
                <span className="whitespace-nowrap font-semibold text-[#2E8F66]">
                    +{Math.max(0, 100 - it.completion)}% to top
                </span>
            </div>
        </div>
    );

    const medals = {
        1: { m: "#C79A3A", d: "#8C6A1E", tint: "#FFF7E6", bar: "#E8C26E" },
        2: { m: "#8E99A4", d: "#55606B", tint: "#F3F5F7", bar: "#B8C1CA" },
        3: { m: "#B07A4B", d: "#7A4E27", tint: "#FAF0E6", bar: "#D4A377" },
    };

    const first = at(1);
    const second = at(2);
    const third = at(3);
    const others = items.filter((x) => x.rank > 3);

    return (
        <SectionCard
            title="Performance of Centres"
            className="!rounded-none !rounded-t-none !rounded-b-none"
            style={{ borderRadius: 0 }}
        >
            <div className="relative overflow-hidden">
                <svg className="pointer-events-none absolute left-0 top-0 hidden w-[520px] md:block" height="50" viewBox="0 0 520 70" fill="none" aria-hidden="true">
                    {CONF.map((c, i) => (
                        c.t ? (
                            <polygon key={i} points={`${c.x},${c.y - 4} ${c.x + 4},${c.y + 4} ${c.x - 4},${c.y + 4}`} fill={c.c} opacity="0.65" transform={`rotate(${c.r} ${c.x} ${c.y})`} />
                        ) : (
                            <rect key={i} x={c.x} y={c.y} width={c.w} height={c.h} fill={c.c} opacity="0.75" transform={`rotate(${c.r} ${c.x + c.w / 2} ${c.y + c.h / 2})`} />
                        )
                    ))}
                </svg>

                <div className="grid grid-cols-1 items-end gap-3 lg:grid-cols-[auto_1fr] lg:gap-0">
                    <div className="relative flex items-end justify-center pt-[10px] lg:pr-4">
                        <div style={{ width: 118, flex: "none" }}><Col it={second} rank={2} m={medals[2]} ped={44} winner={false} /></div>
                        <div style={{ width: 136, flex: "none" }}><Col it={first} rank={1} m={medals[1]} ped={68} winner={true} /></div>
                        <div style={{ width: 118, flex: "none" }}><Col it={third} rank={3} m={medals[3]} ped={32} winner={false} /></div>
                    </div>

                    <div className="flex flex-col border-t border-[#F0EAF0] pt-[14px] lg:border-l lg:border-t-0 lg:pl-4 lg:pt-0">
                        {others.length > 0 && (
                            <>
                                <div className="mb-2.5 pt-[2px] text-center lg:text-left">
                                    <div style={{ fontFamily: "Lora, serif", fontSize: "14px", fontWeight: 600, color: "#2E2340" }}>Centres working toward the top</div>
                                </div>
                                <div className="mt-[10px] flex flex-wrap items-end justify-center gap-x-[12px] gap-y-[14px] lg:justify-start">
                                    {others.map((o) => (
                                        <div key={o.centre_id || o.centre} style={{ width: 140, flex: "none" }}>
                                            <FloorCard it={o} />
                                        </div>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </SectionCard>
    );
}

/* ==================================================================
   DashboardCharts Component
================================================================== */
export default function DashboardCharts({ data = {}, filters = {} }) {
    const navigate = useNavigate();
    const navigatingRef = useRef(false);

    const handleLearnerClick = (row) => {
        const id = row?.participant_id || row?.id;
        if (!id || navigatingRef.current) return;
        navigatingRef.current = true;
        setDetail(null);
        navigate(`/participants/view/${id}`);
    };

    useEffect(() => {
        navigatingRef.current = false;
    }, []);

    const [states, setStates] = useState([]);
    const [statusRows, setStatusRows] = useState([]);
    const [centreRows, setCentreRows] = useState([]);
    const [detail, setDetail] = useState(null);
    const [tState, setTState] = useState(null);

    const [needAttentionCounts, setNeedAttentionCounts] = useState(null);
    const [leaderboardList, setLeaderboardList] = useState([]);
    const [, setLeaderboardLoading] = useState(true);
    const [topLearnersList, setTopLearnersList] = useState([]);
    const [topLearnersLoading, setTopLearnersLoading] = useState(true);

    useEffect(() => {
        let on = true;

        Promise.all([
            Promise.resolve(getStateWiseTrainees(filters)).catch(() => []),
            Promise.resolve(getStateWiseTraineeStatus(filters)).catch(() => []),
            Promise.resolve(getCentreWiseTrainees(filters)).catch(() => []),
        ]).then(([a, b, c]) => {
            if (!on) return;
            setStates(Array.isArray(a) ? a : Array.isArray(a?.data) ? a.data : []);
            setStatusRows(Array.isArray(b) ? b : Array.isArray(b?.data) ? b.data : []);
            setCentreRows(Array.isArray(c) ? c : Array.isArray(c?.data) ? c.data : []);
        });

        getNeedAttentionSummary(filters)
            .then((res) => {
                if (!on) return;
                const d = res?.data || res;
                if (d && (d.never_logged_in !== undefined || d.inactive_30d !== undefined)) {
                    setNeedAttentionCounts(d);
                }
            })
            .catch(() => { });

        setLeaderboardLoading(true);
        getCentreLeaderboard(filters)
            .then((res) => {
                if (!on) return;
                const list = res?.data || (Array.isArray(res) ? res : []);
                if (Array.isArray(list) && list.length > 0) {
                    setLeaderboardList(
                        list.map((r) => ({
                            rank: r.rank,
                            centre_id: r.centre_id,
                            centre: r.centre_name,
                            state: r.state_name,
                            completion: Math.round(r.completion_rate_pct ?? r.completion_rate ?? 0),
                            active: r.active_trainees ?? 0,
                        }))
                    );
                } else {
                    setLeaderboardList([]);
                }
            })
            .catch(() => {
                if (on) setLeaderboardList([]);
            })
            .finally(() => {
                if (on) setLeaderboardLoading(false);
            });

        setTopLearnersLoading(true);
        getTopLearners({ limit: 5, ...filters })
            .then((res) => {
                if (!on) return;
                const list = res?.data || (Array.isArray(res) ? res : []);
                if (Array.isArray(list) && list.length > 0) {
                    setTopLearnersList(
                        list.map((r, idx) => {
                            const totalSec = Number(r.learning_time_seconds ?? 0) || 0;
                            return {
                                rank: r.rank ?? (idx + 1),
                                participant_id: r.participant_id || r.id,
                                name: r.participant_name || r.name || `Learner ${idx + 1}`,
                                participant_name: r.participant_name || r.name,
                                centre: r.centre_name || r.centre || "—",
                                state: r.state_name || r.state || "",
                                image: r.image || r.participant_image || null,
                                assessment_percentage: Number(r.assessment_percentage ?? 0),
                                scorePct: Number(r.assessment_percentage ?? 0),
                                score: Number(r.score ?? r.assessment_percentage ?? 0),
                                total_score: Number(r.total_score ?? r.assessment_questions_correct ?? 0),
                                correct: Number(r.assessment_questions_correct ?? 0),
                                correct_questions: Number(r.correct_questions ?? r.assessment_questions_correct ?? 0),
                                assigned_questions: Number(r.assigned_questions ?? r.total_questions ?? 0),
                                attempted: Number(r.assessment_questions_attempted ?? 0),
                                combined_score: Number(r.combined_score ?? 0),
                                totalSec,
                                minutes: Math.round(totalSec / 60),
                                modules: Number(r.completed_modules_count ?? r.completed_modules ?? 0),
                                completed_modules: Number(r.completed_modules_count ?? r.completed_modules ?? 0),
                                assigned_modules: Number(r.total_assigned_modules ?? r.assigned_modules ?? 0),
                                total_assigned_modules: Number(r.total_assigned_modules ?? r.total_modules_count ?? r.assigned_modules ?? 0),
                                total_modules: Number(r.total_assigned_modules ?? r.total_modules_count ?? r.assigned_modules ?? 0),
                                module_completion_percentage: r.module_completion_percentage !== undefined ? Number(r.module_completion_percentage) : undefined,
                                obtained_marks: r.obtained_marks !== undefined ? Number(r.obtained_marks) : undefined,
                                total_marks: r.total_marks !== undefined ? Number(r.total_marks) : undefined,
                            };
                        })
                    );
                } else {
                    setTopLearnersList([]);
                }
            })
            .catch(() => {
                if (on) setTopLearnersList([]);
            })
            .finally(() => {
                if (on) setTopLearnersLoading(false);
            });

        return () => {
            on = false;
        };
    }, [filters]);

    const statesSorted = useMemo(
        () => states
            .map((r) => ({ name: r.state_name, total: Number(r.total_trainees ?? r.total) || 0 }))
            .sort((a, b) => b.total - a.total),
        [states]
    );

    const traineeTotal = data?.summary?.total_participants || statesSorted.reduce((s, r) => s + r.total, 0);

    // State click -> show only that state's centres; clicking a centre bar does nothing
    const tView = useMemo(() => {
        if (!tState) return { rows: statesSorted, total: traineeTotal, drillLabel: null };
        const rows = centreRows
            .filter((c) => isCentreInState(tState, c.centre_id, c.state_name))
            .map((c) => ({
                centre_id: c.centre_id,
                name: (c.centre_name || "").replace(/\s*(Centre|Center)$/i, ""),
                total: Number(c.total_trainees ?? c.total) || 0,
            }))
            .sort((a, b) => b.total - a.total);
        return {
            rows,
            total: rows.reduce((s, r) => s + r.total, 0),
            drillLabel: `${tState} — Centres`,
        };
    }, [tState, statesSorted, centreRows, traineeTotal]);

    const ageData = useMemo(() => {
        const order = { "18-25": 0, "26-35": 1, "36-45": 2 };
        return [...(data.age_group_distribution || [])]
            .filter((r) => String(r.age_group || "").toLowerCase() !== "under 18")
            .sort((a, b) => (order[a.age_group] ?? 9) - (order[b.age_group] ?? 9));
    }, [data.age_group_distribution]);
    const ageTotal = ageData.reduce((s, r) => s + (Number(r.total) || 0), 0);

    const perfByState = useMemo(() => {
        const m = new Map();
        statusRows.forEach((r) => {
            const st = r.state_name;
            if (!st) return;
            if (!m.has(st)) m.set(st, { state: st, Good: 0, Average: 0, Yet: 0, total: 0 });
            const o = m.get(st);
            const s = String(r.status || "").toLowerCase();
            const v = Number(r.total) || 0;
            if (s.includes("good")) o.Good += v;
            else if (s.includes("aver")) o.Average += v;
            else o.Yet += v;
            o.total += v;
        });
        return [...m.values()].sort((a, b) => b.total - a.total);
    }, [statusRows]);

    const centres = data.state_wise_centres || [];
    const att = needAttentionCounts || data.need_attention || { never_logged_in: 0, inactive_30d: 0 };
    const performers = leaderboardList;
    const topLearners = topLearnersList;

    const openTable = (title, rows, columns) => setDetail({ title, loading: false, rows, columns });

    const openAttention = async (kind) => {
        const isNever = kind === "never";
        const title = isNever
            ? `Never logged in since enrolment (${formatNumber(att.never_logged_in)})`
            : `No activity in the last 30 days (${formatNumber(att.inactive_30d)})`;
        const colDateKey = isNever ? "enrolled" : "last";
        const colDateLabel = isNever ? "Enrolled" : "Last active";

        const columns = [
            {
                key: "name",
                label: "Learner",
                render: nameCell,
                exportValue: (r) => (r.mobile ? `${r.name} (${r.mobile})` : r.name),
            },
            { key: "centre", label: "Centre" },
            { key: "state", label: "State" },
            { key: colDateKey, label: colDateLabel },
        ];

        const ExportButton = (
            <button
                type="button"
                onClick={async () => {
                    try {
                        const blob = await exportNeedAttentionLearners({
                            type: isNever ? "never_logged_in" : "inactive_30d",
                            ...filters,
                        });
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = `${isNever ? "never_logged_in" : "inactive_30d"}_learners.csv`;
                        a.click();
                        window.URL.revokeObjectURL(url);
                    } catch {
                        // fallback export handled by table CSV
                    }
                }}
                className="inline-flex items-center gap-[6px] border border-[#6B2D5B] px-[12px] py-[6px] text-[12px] font-semibold text-[#6B2D5B] transition-colors hover:bg-[#FAF4F9]"
            >
                <FiDownload size={13} /> Export CSV
            </button>
        );

        setDetail({
            title,
            loading: true,
            columns,
            rows: [],
            headerControls: ExportButton,
        });

        try {
            const res = await getNeedAttentionLearners({
                type: isNever ? "never_logged_in" : "inactive_30d",
                page: 1,
                page_size: 100,
                ...filters,
            });
            const items = res?.data || (Array.isArray(res) ? res : []);
            const apiRows = (Array.isArray(items) ? items : []).map((r) => ({
                participant_id: r.participant_id,
                name: r.participant_name || r.name,
                mobile: r.mobile_no || r.enrollment_no,
                centre: r.centre_name,
                state: r.state_name,
                image: r.image || null,
                enrolled: formatDateDisplay(r.registration_date),
                last: r.days_inactive != null
                    ? `${r.days_inactive} days ago`
                    : formatTimeDisplay(r.last_activity_time),
            }));
            setDetail({
                title,
                loading: false,
                columns,
                rows: apiRows,
                headerControls: ExportButton,
                onRowClick: handleLearnerClick,
            });
        } catch {
            setDetail({
                title,
                loading: false,
                columns,
                rows: [],
                headerControls: ExportButton,
                onRowClick: handleLearnerClick,
            });
        }
    };

    const openLearner = async (it) => {
        const participantId = it.participant_id || it.id;
        const columns = [
            { key: "date", label: "Date" },
            { key: "login", label: "Activity / Login" },
            { key: "spent", label: "Time spent" },
        ];
        setDetail({
            title: `Trainee Profile — ${it.name || "Learner"}`,
            loading: Boolean(participantId),
            headerControls: <LearnerProfile it={{
                ...it,
                completed_modules: Number(it.completed_modules ?? it.completed_modules_count ?? it.modules ?? 0),
                total_assigned_modules: Number(it.total_assigned_modules ?? it.assigned_modules ?? it.total_modules_count ?? it.total_modules ?? 0),
                module_completion_percentage: it.module_completion_percentage ?? it.course_progress,
            }} />,
            columns,
            rows: [],
        });

        if (participantId) {
            try {
                const detRes = await getLearnerActivityDetail(participantId).catch(() => null);
                const detData = detRes?.data || detRes;
                if (detData) {
                    const prof = detData.profile || detData;
                    const participantName = prof.participant_name || prof.name || it.name;
                    const totalSec = Number(
                        prof.total_time_spent_seconds ??
                        prof.time_spent_seconds ??
                        it.totalSec ??
                        ((it.minutes || 0) * 60)
                    ) || 0;

                    const enrichedIt = {
                        ...it,
                        rank: prof.rank ?? it.rank,
                        total_score: Number(prof.total_score ?? it.total_score ?? 0),
                        score: Number(prof.score ?? it.score ?? prof.total_score ?? it.total_score ?? 0),
                        assessment_percentage: prof.assessment_percentage != null && !isNaN(Number(prof.assessment_percentage)) && Number(prof.assessment_percentage) > 0
                            ? Number(prof.assessment_percentage)
                            : (it.assessment_percentage ?? 0),
                        scorePct: prof.assessment_percentage != null && !isNaN(Number(prof.assessment_percentage)) && Number(prof.assessment_percentage) > 0
                            ? Number(prof.assessment_percentage)
                            : (it.scorePct ?? it.assessment_percentage ?? 0),
                        obtained_marks: prof.obtained_marks !== undefined && prof.obtained_marks !== null && Number(prof.obtained_marks) > 0
                            ? Number(prof.obtained_marks)
                            : it.obtained_marks,
                        total_marks: prof.total_marks !== undefined && prof.total_marks !== null && Number(prof.total_marks) > 0
                            ? Number(prof.total_marks)
                            : it.total_marks,
                        assigned_modules: prof.total_assigned_modules ?? prof.assigned_modules ?? it.assigned_modules,
                        name: participantName,
                        centre: prof.centre_name || it.centre,
                        state: prof.state_name || it.state,
                        image: prof.image || it.image,
                        modules: Number(prof.completed_modules ?? it.completed_modules ?? prof.completed_modules_count ?? it.modules ?? 0),
                        completed_modules: Number(prof.completed_modules ?? it.completed_modules ?? prof.completed_modules_count ?? it.modules ?? 0),
                        total_assigned_modules: Number(prof.total_assigned_modules ?? it.total_assigned_modules ?? prof.total_modules_count ?? prof.assigned_modules ?? it.total_modules ?? 0),
                        total_modules: Number(prof.total_assigned_modules ?? it.total_assigned_modules ?? prof.total_modules_count ?? prof.assigned_modules ?? it.total_modules ?? 0),
                        module_completion_percentage: prof.module_completion_percentage !== undefined && !isNaN(Number(prof.module_completion_percentage))
                            ? Number(prof.module_completion_percentage)
                            : (it.module_completion_percentage !== undefined ? Number(it.module_completion_percentage) : undefined),
                        course_progress: prof.course_progress !== undefined ? Number(prof.course_progress) : it.course_progress,
                        time: formatTimeDisplay(prof.last_activity || prof.latest_activity_time || prof.last_activity_at) || it.time,
                        totalSec,
                        minutes: Math.round(totalSec / 60),
                    };

                    let sessions = [];
                    if (Array.isArray(prof.recent_sessions) && prof.recent_sessions.length > 0) {
                        sessions = prof.recent_sessions.map((s) => ({
                            date: formatDateDisplay(s.created_at || s.date || s.login_time),
                            login: (s.created_at || s.login_time)
                                ? formatTimeDisplay(s.created_at || s.login_time).split(" · ")[0]
                                : (s.login || "—"),
                            spent: formatTotalSpent(s.time_taken_seconds || s.time_spent_seconds || s.time_taken, s.time_spent_minutes),
                        }));
                    } else if (prof.last_login || prof.last_activity) {
                        const act = prof.last_activity || prof.last_login;
                        sessions = [{
                            date: formatDateDisplay(act),
                            login: formatTimeDisplay(act).split(" · ")[0],
                            spent: formatTotalSpent(totalSec, enrichedIt.minutes),
                        }];
                    }

                    setDetail({
                        title: `Trainee Profile — ${participantName}`,
                        loading: false,
                        headerControls: <LearnerProfile it={enrichedIt} />,
                        columns,
                        rows: sessions,
                    });
                } else {
                    setDetail((prev) => (prev ? { ...prev, loading: false } : null));
                }
            } catch {
                setDetail((prev) => (prev ? { ...prev, loading: false } : null));
            }
        }
    };

    // Clicking a state on the map shows only that state's centres in TraineesBars
    const handleMapStateClick = (stateName) => {
        if (!stateName) return;
        setTState(stateName);
    };

    const openPerfSeg = async (state, cat, val) => {
        const catLabel = (cat || "").toLowerCase().includes("good")
            ? "Good"
            : (cat || "").toLowerCase().includes("aver")
                ? "Average"
                : "Yet to Start";
        const initialTitle = state
            ? `${state} — ${catLabel} (${formatNumber(val || 0)})`
            : `${catLabel} Learners (${formatNumber(val || 0)})`;
        const columns = [
            {
                key: "name",
                label: "Learner",
                render: nameCell,
                exportValue: (r) => (r.mobile ? `${r.name} (${r.mobile})` : r.name),
            },
            { key: "centre", label: "Centre" },
            { key: "district", label: "District" },
            { key: "progress", label: "Progress" },
            { key: "status", label: "Status" },
        ];
        setDetail({
            title: initialTitle,
            loading: true,
            columns,
            rows: [],
            onRowClick: handleLearnerClick,
        });
        try {
            const list = await getTraineeStatusDetails(filters);
            const items = Array.isArray(list) ? list : (list?.data || []);
            const target = (cat || "").toLowerCase();
            const filtered = items.filter((r) => {
                const matchState = !state || (r.state_name && r.state_name.toLowerCase() === state.toLowerCase());
                const s = String(r.performance_status || "").toLowerCase();
                let matchCat = false;
                if (target.includes("good")) matchCat = s.includes("good");
                else if (target.includes("aver")) matchCat = s.includes("aver");
                else matchCat = s.includes("yet") || (!s.includes("good") && !s.includes("aver"));
                return matchState && matchCat;
            }).map((r) => ({
                participant_id: r.participant_id,
                name: r.participant_name,
                mobile: r.mobile_no || r.enrollment_no,
                centre: r.centre_name,
                district: r.district_name || "—",
                progress: `${Math.round(r.course_progress || 0)}%`,
                status: r.performance_status || catLabel,
                image: r.participant_image || r.image || null,
            }));
            const finalTitle = state
                ? `${state} — ${catLabel} (${formatNumber(filtered.length)})`
                : `${catLabel} Learners (${formatNumber(filtered.length)})`;
            setDetail({
                title: finalTitle,
                loading: false,
                columns,
                rows: filtered,
                onRowClick: handleLearnerClick,
            });
        } catch {
            setDetail({
                title: initialTitle,
                loading: false,
                columns,
                rows: [],
                onRowClick: handleLearnerClick,
            });
        }
    };

    return (
        <div className="w-full">
            <style>{`.recharts-wrapper:focus,.recharts-surface:focus,.recharts-sector,.recharts-rectangle{outline:none!important;}`}</style>

            {/* Row 1 - three analytic panels */}
            <div className="grid grid-cols-1 items-stretch gap-[14px] md:grid-cols-2 xl:grid-cols-3">
                <ChartPanel
                    title="Trainees at a Glance"
                    accent="purple"
                    rows={tView.rows}
                    columns={[{ key: "name", label: tState ? "Centre" : "State" }, { key: "total", label: "Trainees" }]}
                    onDetail={() => openTable(
                        tState ? `${tState} — Centres` : "Trainees by State",
                        tView.rows,
                        [{ key: "name", label: tState ? "Centre" : "State" }, { key: "total", label: "Trainees" }]
                    )}
                >
                    <TraineesBars
                        data={tView.rows}
                        total={tView.total}
                        drillLabel={tView.drillLabel}
                        onBack={() => setTState(null)}
                        onBar={tState ? undefined : (d) => setTState(d.name)}
                    />
                </ChartPanel>

                <ChartPanel
                    title="Age Group Distribution"
                    accent="orchid"
                    rows={ageData}
                    columns={[{ key: "age_group", label: "Age band" }, { key: "total", label: "Trainees" }]}
                    onDetail={() => openTable("Age Group Distribution", ageData, [{ key: "age_group", label: "Age band" }, { key: "total", label: "Trainees" }])}
                >
                    <AgeDonut data={ageData} total={ageTotal} />
                </ChartPanel>

                <ChartPanel
                    title="Performance Distribution"
                    accent="emerald"
                    rows={perfByState}
                    columns={[{ key: "state", label: "State" }, { key: "Good", label: "Good" }, { key: "Average", label: "Average" }, { key: "Yet", label: "Yet to start" }]}
                    onDetail={() => openTable("Performance by State", perfByState, [{ key: "state", label: "State" }, { key: "Good", label: "Good" }, { key: "Average", label: "Average" }, { key: "Yet", label: "Yet to start" }, { key: "total", label: "Total" }])}
                >
                    <PerfBars data={perfByState} onSeg={openPerfSeg} />
                </ChartPanel>
            </div>

            {/* Row 2 - map spans 2 columns; need attention / recent activity in column 3 */}
            <div className="mt-[14px] grid grid-cols-1 items-stretch gap-[14px] xl:grid-cols-3">
                <ChartPanel title="Centres across India" accent="emerald" className="h-full xl:col-span-2">
                    <div className="relative h-full min-h-[500px]">
                        <div className="absolute inset-0">
                            <Suspense fallback={<div className="h-full w-full animate-pulse !rounded-none bg-[#F4F8F5]" />}>
                                <StateWiseCentresMap centres={centres} height={500} onStateClick={handleMapStateClick} />
                            </Suspense>
                        </div>
                    </div>
                </ChartPanel>

                <div className="flex flex-col gap-[14px]">
                    <NeedAttention att={att} onOpen={openAttention} />
                    <TopLearners items={topLearners} onOpen={openLearner} loading={topLearnersLoading} />
                </div>
            </div>

            {/* Row 3 - top performing centres (non-clickable) */}
            <div className="mt-[14px]">
                <TopPerformers items={performers} />
            </div>

            {detail && (
                <ChartDetailModal
                    key="dashboard-chart-detail-modal"
                    title={detail.title}
                    columns={detail.columns}
                    rows={detail.rows}
                    loading={detail.loading}
                    headerControls={detail.headerControls}
                    onClose={() => {
                        navigatingRef.current = false;
                        setDetail(null);
                    }}
                    onRowClick={detail.onRowClick}
                />
            )}
        </div>
    );
}