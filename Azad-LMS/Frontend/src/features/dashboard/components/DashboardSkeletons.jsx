/*
 * Loading placeholders for the dashboard.
 *
 * Deliberately NOT part of the lazy DashboardCharts chunk: the skeleton has
 * to paint on the very first frame, before that chunk has finished
 * downloading. Keeping it here means there is never a blank gap where the
 * charts will be.
 */

import { CARD_CLASS } from "../hook/dashboardTheme";

/* Mirrors the real card shell (fixed heights, 44px header, filled body) so
   nothing jumps when data lands. */
function PanelSkeleton() {
    return (
        <div className={`${CARD_CLASS} flex h-[440px] flex-col overflow-hidden md:h-[470px] xl:h-[480px]`}>
            <div className="flex h-[44px] shrink-0 items-center gap-[9px] px-[16px] md:px-[20px]">
                <span className="h-[26px] w-[26px] shrink-0 animate-pulse rounded-none bg-[#EDE8F2]" />
                <span className="block h-[14px] w-[150px] animate-pulse rounded-none bg-[#EDE8F2]" />
            </div>
            <div className="mx-[16px] h-px shrink-0 bg-[#EDEAF2] md:mx-[20px]" />
            <div className="min-h-0 flex-1 p-[16px] md:p-[20px]">
                <div className="h-full w-full animate-pulse rounded-none bg-[#F6F4F9]" />
            </div>
        </div>
    );
}

export function ChartsGridSkeleton() {
    return (
        <div className="flex flex-col gap-[14px]">
            {/* Row 1: 3 chart panels */}
            <div className="grid w-full grid-cols-1 gap-[14px] md:grid-cols-2 xl:grid-cols-3">
                <PanelSkeleton />
                <PanelSkeleton />
                <PanelSkeleton />
            </div>
            {/* Row 2: map + sidebar */}
            <div className="grid w-full grid-cols-1 gap-[14px] xl:grid-cols-3">
                <div className={`${CARD_CLASS} xl:col-span-2 h-[360px] animate-pulse bg-[#F6F4F9]`} />
                <div className="flex flex-col gap-[14px]">
                    <PanelSkeleton />
                    <PanelSkeleton />
                </div>
            </div>
        </div>
    );
}

/* Spinner + caption shown over the page while the first payload is on its
   way, so an empty-looking dashboard is never mistaken for "no data". */
export function DashboardLoader({ label = "Loading dashboard…" }) {
    return (
        <div
            role="status"
            aria-live="polite"
            className="pointer-events-none absolute inset-x-0 top-[38%] z-[900] flex justify-center"
        >
            <span className="pointer-events-auto flex items-center gap-[12px] rounded-none border border-[#EDEAF2] bg-white px-[16px] py-[10px] shadow-[0_10px_28px_-16px_rgba(31,27,46,0.3)]">
                <span className="h-[18px] w-[18px] animate-spin rounded-full border-[2.5px] border-[#E7DCE6] border-t-[#732269]" />
                <span className="text-[13px] font-medium text-[#1F1B2E]">
                    {label}
                </span>
            </span>
        </div>
    );
}

/* Small pill shown while a filter refetch is in flight (the page stays
   readable underneath). */
export function UpdatingPill({ label = "Updating…" }) {
    return (
        <div
            role="status"
            aria-live="polite"
            className="pointer-events-none fixed inset-x-0 top-[128px] z-[900] flex justify-center"
        >
            <span className="flex items-center gap-[9px] rounded-none border border-[#EDEAF2] bg-white px-[14px] py-[7px] shadow-[0_10px_24px_-16px_rgba(31,27,46,0.3)]">
                <span className="h-[14px] w-[14px] animate-spin rounded-full border-[2px] border-[#E7DCE6] border-t-[#732269]" />
                <span className="text-[12.5px] font-medium text-[#1F1B2E]">
                    {label}
                </span>
            </span>
        </div>
    );
}
