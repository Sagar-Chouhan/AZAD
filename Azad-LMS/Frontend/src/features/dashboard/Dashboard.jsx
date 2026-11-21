import { lazy, Suspense, useCallback, useEffect, useState } from "react";

import { FiAlertCircle, FiRefreshCw } from "react-icons/fi";

import AppLayout from "@/components/layout/AppLayout";

import DashboardFilter from "./components/DashboardFilter";
import StatsCards from "./components/DashboardStats";

import {
    ChartsGridSkeleton,
    DashboardLoader,
    UpdatingPill,
} from "./components/DashboardSkeletons";


import { getDashboardSummary } from "./services/DashboardService";

/*
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const fmtDate = (value) => {
    if (!value) return "";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
};

const describeRange = (f = {}) => {
    const from = fmtDate(f.from_date);
    const to = fmtDate(f.to_date);
    if (from && to) return `${from} – ${to}`;
    if (from) return `From ${from}`;
    if (to) return `Up to ${to}`;
    return "All time";
};
*/


// ---------------------------------------------------------
// Lazy Load Dashboard Charts
// ---------------------------------------------------------

const loadDashboardCharts = () => import("./components/DashboardCharts");

const DashboardCharts = lazy(loadDashboardCharts);

// Start loading the charts chunk while the summary API is in flight.
loadDashboardCharts();


// ---------------------------------------------------------
// Dashboard Component
// ---------------------------------------------------------

export default function Dashboard() {
    // -------------------------------------------------------
    // State
    // -------------------------------------------------------

    const [loading, setLoading] = useState(true);

    const [filters, setFilters] = useState({});

    const [dashboardSummary, setDashboardSummary] = useState(null);

    const [error, setError] = useState(null);

    // Used by "Try again" to re-run the dashboard request.
    const [reloadToken, setReloadToken] = useState(0);


    // -------------------------------------------------------
    // Fetch Dashboard Data
    // -------------------------------------------------------

    useEffect(() => {
        let isCurrentRequest = true;


        const fetchDashboard = async () => {
            try {
                setLoading(true);


                const response = await getDashboardSummary(filters);


                if (isCurrentRequest) {
                    setDashboardSummary(response);
                    setError(null);
                }
            } catch (err) {
                console.error("Dashboard load error:", err);


                if (isCurrentRequest) {
                    setError(
                        err?.response?.data?.detail ||
                        err?.message ||
                        "We couldn't load the dashboard data."
                    );
                }
            } finally {
                if (isCurrentRequest) {
                    setLoading(false);
                }
            }
        };


        fetchDashboard();


        return () => {
            isCurrentRequest = false;
        };
    }, [filters, reloadToken]);


    // -------------------------------------------------------
    // Retry
    // -------------------------------------------------------

    const retry = useCallback(() => {
        setReloadToken((n) => n + 1);
    }, []);


    /*
    const handleExport = useCallback(() => {
        if (!dashboardSummary) {
            return;
        }

        downloadDashboardReport(dashboardSummary, filters);
    }, [dashboardSummary, filters]);
    */


    // -------------------------------------------------------
    // Loading / Error States
    // -------------------------------------------------------
    // -------------------------------------------------------

    const firstLoad = !dashboardSummary && loading;

    const failedWithNoData = !dashboardSummary && !loading && error;


    // -------------------------------------------------------
    // Render
    // -------------------------------------------------------

    return (
        <AppLayout>
            <main
                className="dashboard-page w-full relative min-h-screen bg-[#F5F6F8] flex-1 min-w-0"
                style={{ backgroundColor: "#F5F6F8", width: "100%", maxWidth: "none", minWidth: 0 }}
            >
                <style>{`
                    .dashboard-page .dashboard-progress {
                        animation: dashboard-progress 1.25s ease-in-out infinite;
                        transform-origin: left center;
                    }
                    @keyframes dashboard-progress {
                        0% { transform: translateX(-110%) scaleX(.65); }
                        55% { transform: translateX(95%) scaleX(1); }
                        100% { transform: translateX(310%) scaleX(.7); }
                    }
                    @media (prefers-reduced-motion: reduce) {
                        .dashboard-page .dashboard-progress { animation: none; }
                    }
                `}</style>
                {/* -------------------------------------------------
                    First Load
                ------------------------------------------------- */}

                {firstLoad && <DashboardLoader />}


                {/* -------------------------------------------------
                    Updating Indicator
                ------------------------------------------------- */}

                {loading && dashboardSummary && <UpdatingPill />}


                {/* -------------------------------------------------
                    Top Progress Bar
                ------------------------------------------------- */}

                {loading && dashboardSummary && (
                    <div className="pointer-events-none absolute inset-x-0 top-0 z-[1000] h-[2px] overflow-hidden bg-transparent">
                        <span className="dashboard-progress block h-full w-1/3 bg-[#732269]" />
                    </div>
                )}


                {/* -------------------------------------------------
                    Dashboard Content
                ------------------------------------------------- */}

                <div
                    className={`relative w-full min-w-0 max-w-none px-3 pt-2 pb-2.5 sm:px-4 sm:pt-2.5 sm:pb-3 transition-opacity duration-300 ${loading && dashboardSummary
                        ? "opacity-75"
                        : "opacity-100"
                        }`}
                >
                    {/* -------------------------------------------------
                        Filters
                    ------------------------------------------------- */}

                    <section className="mb-2.5">
                        <DashboardFilter
                            setFilters={setFilters}
                            loading={loading}
                        />
                    </section>


                    {/* -------------------------------------------------
                        Refresh Error
                    ------------------------------------------------- */}

                    {error && dashboardSummary && (
                        <div role="alert" className="mb-4 flex flex-wrap items-start gap-2 rounded-none border border-[#F3D9D6] bg-[#FDF3F2] px-3 py-3 sm:items-center sm:px-4">
                            <FiAlertCircle
                                size={15}
                                className="shrink-0 text-[#C0392B]"
                            />

                            <span className="text-[12px] leading-[18px] text-[#8C3A32]">
                                Couldn&apos;t refresh the dashboard — showing
                                the last loaded data. {error}
                            </span>

                            <button
                                type="button"
                                onClick={retry}
                                className="ml-auto inline-flex shrink-0 items-center justify-center gap-1.5 rounded-none border border-[#C0392B] px-3 py-2 text-xs font-semibold text-[#C0392B] transition-colors duration-200 hover:bg-[#FBE9E7] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C0392B] focus-visible:ring-offset-2"
                            >
                                <FiRefreshCw size={12} />
                                Try again
                            </button>
                        </div>
                    )}


                    {/* -------------------------------------------------
                        No Data / First Load Error
                    ------------------------------------------------- */}

                    {failedWithNoData ? (
                        <div className="flex min-h-[300px] flex-col items-center justify-center gap-3 rounded-none border border-[#E4E0E9] bg-white px-5 py-10 text-center shadow-sm sm:min-h-[340px] sm:px-8">
                            <span className="flex h-12 w-12 items-center justify-center rounded-none bg-[#FDF3F2]">
                                <FiAlertCircle
                                    size={20}
                                    className="text-[#C0392B]"
                                />
                            </span>

                            <h2
                                className="m-0 font-semibold text-[#1F1B2E]"
                                style={{
                                    fontSize: "16px",
                                    lineHeight: "22px",
                                }}
                            >
                                Dashboard data unavailable
                            </h2>

                            <p
                                className="m-0 max-w-[440px] text-[#6B6478]"
                                style={{
                                    fontSize: "13px",
                                    lineHeight: "19px",
                                }}
                            >
                                {error}
                            </p>

                            <button
                                type="button"
                                onClick={retry}
                                className="mt-1 inline-flex items-center justify-center gap-2 rounded-none bg-[#732269] px-4 py-2.5 text-[13px] font-semibold text-white shadow-sm transition-colors duration-200 hover:bg-[#63205A] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#732269] focus-visible:ring-offset-2"
                            >
                                <FiRefreshCw size={13} />
                                Try again
                            </button>
                        </div>
                    ) : (
                        <>
                            {/* -------------------------------------------------
                                Stats Cards
                            ------------------------------------------------- */}

                            <section className="mb-2.5">
                                <StatsCards
                                    loading={firstLoad}
                                    centres={
                                        dashboardSummary?.summary
                                            ?.total_centres ?? 0
                                    }
                                    trainees={
                                        dashboardSummary?.summary
                                            ?.total_participants ?? 0
                                    }
                                    active={
                                        dashboardSummary?.summary
                                            ?.active_participants ??
                                        dashboardSummary?.summary
                                            ?.total_active_participants ?? 0
                                    }
                                    modules={
                                        dashboardSummary?.summary
                                            ?.total_modules ?? 0
                                    }
                                    batches={
                                        dashboardSummary?.summary
                                            ?.total_batches ?? 0
                                    }
                                    documents={
                                        dashboardSummary?.summary
                                            ?.total_documents ?? 0
                                    }
                                />
                            </section>


                            {/* -------------------------------------------------
                                Charts
                            ------------------------------------------------- */}

                            <section className="min-w-0 mt-0" aria-label="Dashboard analytics charts">
                                {firstLoad ? (
                                    <ChartsGridSkeleton />
                                ) : (
                                    <Suspense
                                        fallback={<ChartsGridSkeleton />}
                                    >
                                        <DashboardCharts
                                            data={dashboardSummary || {}}
                                            loading={loading}
                                            filters={filters}
                                        />
                                    </Suspense>
                                )}
                            </section>
                        </>
                    )}
                </div>
            </main>
        </AppLayout>
    );
}