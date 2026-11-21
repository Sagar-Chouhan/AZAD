import { memo, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
    FaBuilding,
    FaBookOpen,
    FaChalkboardTeacher,
    FaFileAlt,
    FaFemale,
    FaUserCheck,
} from "react-icons/fa";

import { FiInfo } from "react-icons/fi";

import * as dashboardTheme from "../hook/dashboardTheme";

// ============================================================
// KPI Cards Configuration
// ============================================================

const STATS_CONFIG = [
    {
        key: "centres",
        label: "Total Centres",
        icon: FaBuilding,
        accent: "#732269",
        info: "Total number of training centres across all states.",
        path: "/centres/list",
    },
    {
        key: "trainees",
        label: "Trainees enrolled",
        icon: FaFemale,
        accent: "#2C8FE0",
        info: "Total women enrolled in the programme.",
        path: "/participants/list",
    },
    {
        key: "active",
        label: "Active trainees",
        icon: FaUserCheck,
        accent: "#0E8C7E",
        info: "Active trainees only who login atleast 1 time",
        path: null,
    },
    {
        key: "batches",
        label: "Active Batches",
        icon: FaChalkboardTeacher,
        accent: "#A93FBF",
        info: "Training batches currently running.",
        path: "/batches/list",
    },
    {
        key: "modules",
        label: "Modules",
        icon: FaBookOpen,
        accent: "#22A957",
        info: "Learning modules available in the curriculum.",
        path: "/modules",
    },
    {
        key: "documents",
        label: "Documents",
        icon: FaFileAlt,
        accent: "#E74C3C",
        info: "Documents uploaded across all centres.",
        path: "/documents",
    },
];

const GRID_CLASS =
    "grid w-full grid-cols-2 items-stretch gap-2.5 sm:gap-3 lg:grid-cols-3 xl:grid-cols-6";

const BASE_CARD_SHELL = `${dashboardTheme.CARD_CLASS} group relative flex min-h-[72px] items-center gap-[10px] px-[12px] py-[10px] transition-[transform,box-shadow,border-color] duration-150`;

const CLICKABLE_CARD_SHELL = `${BASE_CARD_SHELL} cursor-pointer hover:-translate-y-[2px] hover:border-[#D9C7D4] hover:shadow-[0_1px_2px_rgba(36,27,43,0.05),0_14px_24px_-16px_rgba(36,27,43,0.34)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#732269]`;

const STATIC_CARD_SHELL = `${BASE_CARD_SHELL} cursor-default`;

// ============================================================
// Loading Skeleton
// ============================================================

function StatsCardsSkeleton() {
    return (
        <section className="w-full">
            <div className={GRID_CLASS}>
                {STATS_CONFIG.map(({ key }) => (
                    <div key={key} className={BASE_CARD_SHELL}>
                        <span className="h-[40px] w-[40px] shrink-0 animate-pulse bg-[#F0EDF4]" />

                        <div className="flex flex-1 flex-col items-center">
                            <span className="block h-[22px] w-[48px] animate-pulse bg-[#EBE7F1]" />
                            <span className="mt-[5px] block h-[11px] w-[80px] animate-pulse rounded bg-[#F4F2F7]" />
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}

// ============================================================
// Component
// ============================================================

function StatsCards({
    centres = 0,
    trainees = 0,
    modules = 0,
    batches = 0,
    documents = 0,
    active = 0,
    loading = false,
}) {
    const navigate = useNavigate();

    const [openKey, setOpenKey] = useState(null);
    const [hoverKey, setHoverKey] = useState(null);

    useEffect(() => {
        if (!openKey) return undefined;

        const close = () => setOpenKey(null);
        document.addEventListener("click", close);

        return () => {
            document.removeEventListener("click", close);
        };
    }, [openKey]);

    if (loading) {
        return <StatsCardsSkeleton />;
    }

    const values = {
        centres,
        trainees,
        modules,
        batches,
        documents,
        active,
    };

    const handleCardClick = (path) => {
        if (!path) return;
        setOpenKey(null);
        setHoverKey(null);
        navigate(path);
    };

    const handleCardKeyDown = (event, path) => {
        if (path && (event.key === "Enter" || event.key === " ")) {
            event.preventDefault();
            handleCardClick(path);
        }
    };

    return (
        <section className="w-full">
            <div className={GRID_CLASS}>
                {STATS_CONFIG.map(
                    ({ key, label, icon: Icon, accent, info, path }) => {
                        const isClickable = Boolean(path);
                        const isTooltipVisible = hoverKey === key || openKey === key;

                        return (
                            <div
                                key={key}
                                role={isClickable ? "link" : "group"}
                                tabIndex={isClickable ? 0 : -1}
                                aria-label={isClickable ? `View ${label}` : label}
                                onClick={() => handleCardClick(path)}
                                onKeyDown={(event) =>
                                    handleCardKeyDown(event, path)
                                }
                                className={
                                    isClickable
                                        ? CLICKABLE_CARD_SHELL
                                        : STATIC_CARD_SHELL
                                }
                            >
                                {/* Info Tooltip */}
                                {info && (
                                    <>
                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setOpenKey(
                                                    openKey === key ? null : key
                                                );
                                            }}
                                            onMouseEnter={() => setHoverKey(key)}
                                            onMouseLeave={() => setHoverKey(null)}
                                            className="absolute right-[5px] top-[5px] z-10 grid h-[18px] w-[18px] place-items-center rounded-full text-[#B6AEC0] transition-colors hover:bg-[#F3EEF4] hover:text-[#732269]"
                                            aria-label={`About ${label}`}
                                            title={info}
                                        >
                                            <FiInfo size={12} />
                                        </button>

                                        {isTooltipVisible && (
                                            <div
                                                onClick={(e) => e.stopPropagation()}
                                                onMouseEnter={() => setHoverKey(key)}
                                                onMouseLeave={() => setHoverKey(null)}
                                                className="absolute right-[4px] top-[26px] z-30 border border-[#ECE6EF] bg-white px-[10px] py-[8px] text-left pointer-events-auto"
                                                style={{
                                                    width: 190,
                                                    fontSize: "11px",
                                                    lineHeight: "15px",
                                                    color: "#4A4356",
                                                    boxShadow:
                                                        "0 12px 26px -8px rgba(36,27,43,0.35)",
                                                }}
                                            >
                                                {info}
                                            </div>
                                        )}
                                    </>
                                )}

                                {/* Icon */}
                                <span
                                    className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-none"
                                    style={{
                                        backgroundColor: accent + "22",
                                        color: accent,
                                    }}
                                >
                                    <Icon size={20} aria-hidden="true" />
                                </span>

                                {/* Value + Label */}
                                <div className="min-w-0 flex-1 text-center">
                                    <span
                                        className="block tabular-nums"
                                        style={{
                                            color: dashboardTheme.INK,
                                            fontSize: "24px",
                                            lineHeight: "28px",
                                            letterSpacing: "-0.01em",
                                            fontWeight: 700,
                                        }}
                                    >
                                        {dashboardTheme.formatNumber(
                                            Number(values[key]) || 0
                                        )}
                                    </span>

                                    <span
                                        className="mt-[2px] block truncate"
                                        style={{
                                            color: "#6B6478",
                                            fontSize: "12px",
                                            lineHeight: "16px",
                                            fontWeight: 500,
                                        }}
                                    >
                                        {label}
                                    </span>
                                </div>
                            </div>
                        );
                    }
                )}
            </div>
        </section>
    );
}

export default memo(StatsCards);
