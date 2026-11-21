import { useEffect, useRef, useState } from "react";
import { FiMoreVertical } from "react-icons/fi";

import { ACCENTS, CARD_CLASS, SUB } from "../hook/dashboardTheme";

/* ------------------------------------------------------------------
   Chart export helpers — dependency-free (no chart/export library).
   Work off the panel's rendered <svg> for images/print/pdf, and off the
   passed rows/columns for CSV/XLS/data-table.
------------------------------------------------------------------- */
const slug = (t) => (t || "chart").replace(/\s+/g, "-").toLowerCase();

function getPanelSvg(node) {
    const panel = node && node.closest("[data-chart-panel]");
    return panel ? panel.querySelector("svg") : null;
}

function serializeSvg(svg) {
    const clone = svg.cloneNode(true);
    const rect = svg.getBoundingClientRect();
    clone.setAttribute("width", rect.width);
    clone.setAttribute("height", rect.height);
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    const xml = new XMLSerializer().serializeToString(clone);
    return {
        xml: '<?xml version="1.0" encoding="UTF-8"?>\n' + xml,
        width: rect.width,
        height: rect.height,
    };
}

function downloadBlob(data, type, filename) {
    const blob = data instanceof Blob ? data : new Blob([data], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function svgToCanvas(svg) {
    return new Promise((resolve, reject) => {
        const { xml, width, height } = serializeSvg(svg);
        const src =
            "data:image/svg+xml;base64," +
            btoa(unescape(encodeURIComponent(xml)));
        const img = new Image();
        img.onload = () => {
            const scale = 2;
            const canvas = document.createElement("canvas");
            canvas.width = width * scale;
            canvas.height = height * scale;
            const ctx = canvas.getContext("2d");
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.setTransform(scale, 0, 0, scale, 0, 0);
            ctx.drawImage(img, 0, 0, width, height);
            resolve(canvas);
        };
        img.onerror = reject;
        img.src = src;
    });
}

async function downloadRaster(svg, title, type) {
    const canvas = await svgToCanvas(svg);
    const mime = type === "jpeg" ? "image/jpeg" : "image/png";
    const ext = type === "jpeg" ? "jpg" : "png";
    canvas.toBlob(
        (blob) => blob && downloadBlob(blob, mime, `${slug(title)}.${ext}`),
        mime,
        0.95
    );
}

function downloadSvgFile(svg, title) {
    const { xml } = serializeSvg(svg);
    downloadBlob(xml, "image/svg+xml;charset=utf-8", `${slug(title)}.svg`);
}

/* Print / PDF both go through the browser print dialog (choose
   "Save as PDF" to get a PDF file) — no external library needed. */
async function printChart(svg, title) {
    const canvas = await svgToCanvas(svg);
    const dataUrl = canvas.toDataURL("image/png");
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(
        `<html><head><title>${title}</title>` +
        "<style>html,body{margin:0;height:100%}body{display:flex;align-items:center;justify-content:center}img{max-width:100%;max-height:100%}</style>" +
        "</head><body>" +
        `<img src="${dataUrl}" onload="setTimeout(function(){window.focus();window.print();},200)"/>` +
        "</body></html>"
    );
    w.document.close();
}

function toCsv(columns, rows) {
    const esc = (v) => {
        const s = v == null ? "" : String(v);
        return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    };
    const head = columns.map((c) => esc(c.label)).join(",");
    const body = rows
        .map((r) => columns.map((c) => esc(r[c.key])).join(","))
        .join("\n");
    return head + "\n" + body;
}

function toXlsHtml(columns, rows) {
    const th = columns.map((c) => `<th>${c.label}</th>`).join("");
    const trs = rows
        .map(
            (r) =>
                "<tr>" +
                columns
                    .map((c) => `<td>${r[c.key] == null ? "" : r[c.key]}</td>`)
                    .join("") +
                "</tr>"
        )
        .join("");
    return (
        '<html><head><meta charset="utf-8"></head><body>' +
        `<table border="1"><thead><tr>${th}</tr></thead><tbody>${trs}</tbody></table>` +
        "</body></html>"
    );
}

function viewFullScreen(node) {
    const panel = node && node.closest("[data-chart-panel]");
    if (panel && panel.requestFullscreen) panel.requestFullscreen();
}

/* Export / context menu opened from the panel's ⋮ icon. */
function ChartExportMenu({ title, rows = [], columns = [], onViewTable, whiteIcon = false }) {
    const [open, setOpen] = useState(false);
    const [pos, setPos] = useState({ top: 0, right: 0 });
    const wrapRef = useRef(null);

    useEffect(() => {
        if (!open) return;
        const onDoc = (e) => {
            if (wrapRef.current && !wrapRef.current.contains(e.target)) {
                setOpen(false);
            }
        };
        const onScroll = () => setOpen(false);
        document.addEventListener("mousedown", onDoc);
        window.addEventListener("scroll", onScroll, true);
        return () => {
            document.removeEventListener("mousedown", onDoc);
            window.removeEventListener("scroll", onScroll, true);
        };
    }, [open]);

    const toggle = () => {
        const r = wrapRef.current.getBoundingClientRect();
        setPos({
            top: r.bottom + 6,
            right: Math.max(8, window.innerWidth - r.right),
        });
        setOpen((o) => !o);
    };

    const svg = () => getPanelSvg(wrapRef.current);
    const run = (fn) => {
        setOpen(false);
        try {
            fn();
        } catch {
            // no-op: keep the dashboard stable if an export fails
        }
    };

    const Item = ({ children, onClick, divider }) => (
        <>
            {divider && <div className="my-[4px] h-px bg-[#EDEAF2]" />}
            <button
                type="button"
                onClick={onClick}
                className="block w-full whitespace-nowrap !rounded-none px-[14px] !py-[6px] text-left !text-[13px] !font-normal !leading-[1.25] text-[#1F1B2E] transition-colors hover:bg-[#F6F2F7]"
            >
                {children}
            </button>
        </>
    );

    return (
        <span ref={wrapRef} className="relative z-[3] shrink-0">
            <button
                type="button"
                onClick={toggle}
                title="Chart menu"
                aria-label="Chart menu"
                className="flex h-[24px] w-[24px] items-center justify-center rounded-none transition-colors duration-150 hover:bg-[rgba(255,255,255,0.15)]"
                style={{ color: whiteIcon ? "rgba(255,255,255,0.85)" : SUB }}
            >
                <FiMoreVertical size={15} />
            </button>

            {open && (
                <div
                    style={{
                        position: "fixed",
                        top: pos.top,
                        right: pos.right,
                        zIndex: 1000,
                        width: 236,
                        maxHeight: "82vh",
                        overflowX: "hidden",
                        overflowY: "auto",
                        fontSize: "13px",
                        background: "#ffffff",
                        border: "1px solid #E8E3EC",
                        boxShadow:
                            "0 18px 42px -14px rgba(31,27,46,0.30), 0 2px 6px -2px rgba(31,27,46,0.10)",
                    }}
                    className="rounded-none py-[4px]"
                >
                    <Item onClick={() => run(() => viewFullScreen(wrapRef.current))}>
                        View in full screen
                    </Item>
                    <Item
                        onClick={() =>
                            run(() => {
                                const s = svg();
                                if (s) printChart(s, title);
                            })
                        }
                    >
                        Print chart
                    </Item>

                    <Item
                        divider
                        onClick={() =>
                            run(() => {
                                const s = svg();
                                if (s) downloadRaster(s, title, "png");
                            })
                        }
                    >
                        Download PNG image
                    </Item>
                    <Item
                        onClick={() =>
                            run(() => {
                                const s = svg();
                                if (s) downloadRaster(s, title, "jpeg");
                            })
                        }
                    >
                        Download JPEG image
                    </Item>
                    <Item
                        onClick={() =>
                            run(() => {
                                const s = svg();
                                if (s) printChart(s, title);
                            })
                        }
                    >
                        Download PDF document
                    </Item>
                    <Item
                        onClick={() =>
                            run(() => {
                                const s = svg();
                                if (s) downloadSvgFile(s, title);
                            })
                        }
                    >
                        Download SVG vector image
                    </Item>

                    <Item
                        divider
                        onClick={() =>
                            run(() =>
                                downloadBlob(
                                    "﻿" + toCsv(columns, rows),
                                    "text/csv;charset=utf-8",
                                    `${slug(title)}.csv`
                                )
                            )
                        }
                    >
                        Download CSV
                    </Item>
                    <Item
                        onClick={() =>
                            run(() =>
                                downloadBlob(
                                    toXlsHtml(columns, rows),
                                    "application/vnd.ms-excel",
                                    `${slug(title)}.xls`
                                )
                            )
                        }
                    >
                        Download XLS
                    </Item>

                    <Item
                        divider
                        onClick={() => run(() => onViewTable && onViewTable())}
                    >
                        View data table
                    </Item>
                </div>
            )}
        </span>
    );
}

/* ------------------------------------------------------------------
   Flat chart card: clean square dashboard panel with compact spacing,
   accent-matched icon/title, and the chart export menu.
------------------------------------------------------------------- */
export default function ChartPanel({
    title,
    sub,
    icon,
    accent = "purple",
    onDetail,
    rows = [],
    columns = [],
    className = "",
    children,
}) {
    const tone = ACCENTS[accent] || ACCENTS.purple;

    return (
        <div
            data-chart-panel
            className={`${CARD_CLASS} relative flex flex-col overflow-hidden ${className}`}
        >
            {/* Panel header */}
            <div className="flex shrink-0 items-center justify-between gap-[8px] px-[14px] py-[5px] min-h-[34px]" style={{ backgroundColor: "#732269" }}>
                <div className="flex min-w-0 flex-col">
                    <h3
                        className="m-0 min-w-0 truncate"
                        style={{
                            fontFamily: "Lora, serif",
                            color: "#FFFFFF",
                            fontSize: "13.5px",
                            lineHeight: "18px",
                            fontWeight: 600,
                        }}
                    >
                        {title}
                    </h3>
                    {sub && (
                        <span
                            style={{
                                fontSize: "10.5px",
                                color: "rgba(255,255,255,0.75)",
                                marginTop: "1px",
                                lineHeight: "13px",
                            }}
                        >
                            {sub}
                        </span>
                    )}
                </div>

                <ChartExportMenu
                    title={title}
                    rows={rows}
                    columns={columns}
                    onViewTable={onDetail}
                    whiteIcon
                />
            </div>

            <div className="relative min-h-0 min-w-0 flex-1 px-[14px] pb-[12px] pt-[10px]">
                {children}
            </div>
        </div>
    );
}
