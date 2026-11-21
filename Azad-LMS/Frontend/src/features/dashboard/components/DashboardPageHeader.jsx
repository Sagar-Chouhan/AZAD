import { memo } from "react";
import { FiCalendar, FiDownload } from "react-icons/fi";

import { BRAND, INK, SUB } from "../hook/dashboardTheme";

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

const fmtDate = (value) => {
    if (!value) return "";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
};

function describeRange(filters = {}) {
    const from = fmtDate(filters.from_date);
    const to = fmtDate(filters.to_date);
    if (from && to) return `${from} – ${to}`;
    if (from) return `From ${from}`;
    if (to) return `Up to ${to}`;
    return "All Time";
}

function DashboardPageHeader({ filters = {}, onExport, exportDisabled = false }) {
    return (
        <header className="flex min-h-[42px] flex-col justify-between gap-[8px] border-b border-[#DDE2E8] pb-[8px] sm:flex-row sm:items-center">
            <div className="min-w-0">
                <h1 className="m-0 font-semibold tracking-[-0.02em]" style={{ color: INK, fontSize: "24px", lineHeight: "30px" }}>
                    LMS Dashboard
                </h1>
            </div>

            <div className="flex flex-wrap items-center gap-[6px]">
                <div
                    title="Date range currently applied by the filters below"
                    className="flex h-[34px] items-center gap-[7px] border border-[#DDE2E8] bg-white px-[9px]"
                    style={{ color: INK }}
                >
                    <FiCalendar size={14} style={{ color: BRAND }} aria-hidden="true" />
                    <div className="flex min-w-0 items-center gap-[5px]">
                        <span className="text-[9px] font-semibold uppercase tracking-[0.05em]" style={{ color: SUB }}>Date</span>
                        <span className="whitespace-nowrap text-[12px] font-medium" style={{ color: INK }}>{describeRange(filters)}</span>
                    </div>
                </div>

                <button
                    type="button"
                    onClick={onExport}
                    disabled={exportDisabled}
                    className="inline-flex h-[34px] items-center gap-[7px] border px-[12px] text-[11px] font-semibold text-white transition-colors disabled:cursor-not-allowed disabled:opacity-50 hover:brightness-95"
                    style={{ backgroundColor: BRAND, borderColor: BRAND }}
                >
                    <FiDownload size={14} aria-hidden="true" />
                    Export Report
                </button>
            </div>
        </header>
    );
}

export default memo(DashboardPageHeader);
