import { useEffect, useState } from "react";
import { FaRedo, FaSearch } from "react-icons/fa";

import {
    getDashboardCentres,
    getDashboardDistricts,
    getDashboardStates,
} from "@/features/dashboard/services/DashboardFilterService";
import { CARD_CLASS } from "@/features/dashboard/hook/dashboardTheme";

// ============================================================
// Constants
// ============================================================

const EMPTY_FILTERS = Object.freeze({});

const CONTROL_STYLE = {
    width: "100%",
    height: "36px",
    padding: "0 10px",
    fontSize: "13px",
    color: "#1F1B2E",
    backgroundColor: "#FFFFFF",
    border: "1px solid #D9D3E0",
    borderRadius: "0",
    outline: "none",
    boxShadow: "none",
    transition: "border-color 160ms ease",
};

const SELECT_STYLE = {
    ...CONTROL_STYLE,
    paddingRight: "30px",
    appearance: "none",
    backgroundImage:
        "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%236B6478' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3e%3c/svg%3e\")",
    backgroundRepeat: "no-repeat",
    backgroundPosition: "right 10px center",
    backgroundSize: "11px 8px",
};

const DISABLED_STYLE = {
    backgroundColor: "#F7F6F9",
    color: "#B0AABB",
    cursor: "not-allowed",
    borderColor: "#E8E5EC",
};

const BTN_BASE = {
    height: "36px",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "6px",
    padding: "0 16px",
    fontSize: "13px",
    fontWeight: 600,
    whiteSpace: "nowrap",
    cursor: "pointer",
    transition: "all 160ms ease",
    borderRadius: "0",
};

const SEARCH_STYLE = {
    ...BTN_BASE,
    backgroundColor: "#732269",
    border: "1px solid #732269",
    color: "#FFFFFF",
};

const RESET_STYLE = {
    ...BTN_BASE,
    backgroundColor: "#FFFFFF",
    border: "1px solid #D9D3E0",
    color: "#514A5D",
};

const LABEL_CLASS =
    "mb-[4px] block text-[10.5px] font-semibold uppercase leading-[14px] tracking-[0.06em] text-[#8080A0]";

// ============================================================
// Helpers
// ============================================================

const areFiltersEqual = (current, next) => {
    const ck = Object.keys(current);
    const nk = Object.keys(next);
    if (ck.length !== nk.length) return false;
    return ck.every((k) => current[k] === next[k]);
};

const createFilters = ({ stateId, districtId, centreId, fromDate, toDate }) =>
    Object.fromEntries(
        Object.entries({
            state_id: stateId,
            district_id: districtId,
            centre_id: centreId,
            from_date: fromDate,
            to_date: toDate,
        }).filter(([, v]) => v)
    );

// ============================================================
// Component
// ============================================================

export default function DashboardFilter({ setFilters, loading = false }) {
    const [states, setStates] = useState([]);
    const [districts, setDistricts] = useState([]);
    const [centres, setCentres] = useState([]);

    const [stateId, setStateId] = useState("");
    const [districtId, setDistrictId] = useState("");
    const [centreId, setCentreId] = useState("");
    const [fromDate, setFromDate] = useState("");
    const [toDate, setToDate] = useState("");

    /* Load states on mount */
    useEffect(() => {
        let live = true;
        getDashboardStates()
            .then((r) => { if (live) setStates(Array.isArray(r) ? r : []); })
            .catch(() => { if (live) setStates([]); });
        return () => { live = false; };
    }, []);

    /* Load districts when state changes */
    useEffect(() => {
        let live = true;
        if (!stateId) { setDistricts([]); setCentres([]); return () => { live = false; }; }
        getDashboardDistricts(stateId)
            .then((r) => { if (live) setDistricts(Array.isArray(r) ? r : []); })
            .catch(() => { if (live) setDistricts([]); });
        return () => { live = false; };
    }, [stateId]);

    /* Load centres when district changes */
    useEffect(() => {
        let live = true;
        if (!stateId || !districtId) { setCentres([]); return () => { live = false; }; }
        getDashboardCentres(stateId, districtId)
            .then((r) => { if (live) setCentres(Array.isArray(r) ? r : []); })
            .catch(() => { if (live) setCentres([]); });
        return () => { live = false; };
    }, [stateId, districtId]);

    const handleSearch = () => {
        const next = createFilters({ stateId, districtId, centreId, fromDate, toDate });
        setFilters((cur) => areFiltersEqual(cur, next) ? cur : next);
    };

    const handleReset = () => {
        setStateId(""); setDistrictId(""); setCentreId("");
        setFromDate(""); setToDate("");
        setDistricts([]); setCentres([]);
        setFilters((cur) => areFiltersEqual(cur, EMPTY_FILTERS) ? cur : EMPTY_FILTERS);
    };

    /* Invisible label spacer to keep buttons level with inputs */
    const Spacer = () => (
        <span aria-hidden="true" className="mb-[4px] block select-none text-[10.5px] leading-[14px] text-transparent">
            &nbsp;
        </span>
    );

    return (
        <div className="w-full">
            <div className={`${CARD_CLASS} w-full px-[16px] py-[12px]`}>
                <div className="flex flex-wrap items-end gap-[10px]">

                    {/* STATE */}
                    <div className="min-w-[120px] flex-1">
                        <label className={LABEL_CLASS} htmlFor="df-state">State</label>
                        <select
                            id="df-state"
                            value={stateId}
                            style={SELECT_STYLE}
                            onFocus={(e) => { e.currentTarget.style.borderColor = "#732269"; }}
                            onBlur={(e) => { e.currentTarget.style.borderColor = "#D9D3E0"; }}
                            onChange={(e) => { setStateId(e.target.value); setDistrictId(""); setCentreId(""); }}
                        >
                            <option value="">All States</option>
                            {states.map((s) => (
                                <option key={s.state_lgd_code} value={s.state_lgd_code}>{s.state_name}</option>
                            ))}
                        </select>
                    </div>

                    {/* DISTRICT */}
                    <div className="min-w-[120px] flex-1">
                        <label className={LABEL_CLASS} htmlFor="df-district">District</label>
                        <select
                            id="df-district"
                            value={districtId}
                            style={stateId ? SELECT_STYLE : { ...SELECT_STYLE, ...DISABLED_STYLE }}
                            disabled={!stateId}
                            onFocus={(e) => { if (stateId) e.currentTarget.style.borderColor = "#732269"; }}
                            onBlur={(e) => { if (stateId) e.currentTarget.style.borderColor = "#D9D3E0"; }}
                            onChange={(e) => { setDistrictId(e.target.value); setCentreId(""); }}
                        >
                            <option value="">All Districts</option>
                            {districts.map((d) => (
                                <option key={d.district_lgd_code} value={d.district_lgd_code}>{d.district_name}</option>
                            ))}
                        </select>
                    </div>

                    {/* CENTRE */}
                    <div className="min-w-[120px] flex-1">
                        <label className={LABEL_CLASS} htmlFor="df-centre">Centre</label>
                        <select
                            id="df-centre"
                            value={centreId}
                            style={districtId ? SELECT_STYLE : { ...SELECT_STYLE, ...DISABLED_STYLE }}
                            disabled={!districtId}
                            onFocus={(e) => { if (districtId) e.currentTarget.style.borderColor = "#732269"; }}
                            onBlur={(e) => { if (districtId) e.currentTarget.style.borderColor = "#D9D3E0"; }}
                            onChange={(e) => setCentreId(e.target.value)}
                        >
                            <option value="">All Centres</option>
                            {centres.map((c) => (
                                <option key={c.centre_id} value={c.centre_id}>{c.centre_name}</option>
                            ))}
                        </select>
                    </div>

                    {/* FROM DATE */}
                    <div className="min-w-[130px] flex-1">
                        <label className={LABEL_CLASS} htmlFor="df-from">From Date</label>
                        <input
                            id="df-from"
                            type="date"
                            value={fromDate}
                            max={toDate || undefined}
                            style={CONTROL_STYLE}
                            placeholder="mm/dd/yyyy"
                            onFocus={(e) => { e.currentTarget.style.borderColor = "#732269"; }}
                            onBlur={(e) => { e.currentTarget.style.borderColor = "#D9D3E0"; }}
                            onChange={(e) => setFromDate(e.target.value)}
                        />
                    </div>

                    {/* TO DATE */}
                    <div className="min-w-[130px] flex-1">
                        <label className={LABEL_CLASS} htmlFor="df-to">To Date</label>
                        <input
                            id="df-to"
                            type="date"
                            value={toDate}
                            min={fromDate || undefined}
                            style={CONTROL_STYLE}
                            placeholder="mm/dd/yyyy"
                            onFocus={(e) => { e.currentTarget.style.borderColor = "#732269"; }}
                            onBlur={(e) => { e.currentTarget.style.borderColor = "#D9D3E0"; }}
                            onChange={(e) => setToDate(e.target.value)}
                        />
                    </div>

                    {/* SEARCH */}
                    <div className="shrink-0">
                        <Spacer />
                        <button
                            type="button"
                            disabled={loading}
                            style={loading ? { ...SEARCH_STYLE, opacity: 0.65, cursor: "wait" } : SEARCH_STYLE}
                            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.backgroundColor = "#64205C"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "#732269"; }}
                            onClick={handleSearch}
                        >
                            {loading
                                ? <span aria-hidden="true" className="h-[11px] w-[11px] animate-spin rounded-full border-[2px] border-white/45 border-t-white" />
                                : <FaSearch size={12} />
                            }
                            {loading ? "Searching…" : "Search"}
                        </button>
                    </div>

                    {/* RESET */}
                    <div className="shrink-0">
                        <Spacer />
                        <button
                            type="button"
                            disabled={loading}
                            style={loading ? { ...RESET_STYLE, opacity: 0.6, cursor: "wait" } : RESET_STYLE}
                            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.backgroundColor = "#F7F5F8"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "#FFFFFF"; }}
                            onClick={handleReset}
                        >
                            <FaRedo size={11} />
                            Reset
                        </button>
                    </div>

                </div>
            </div>
        </div>
    );
}
