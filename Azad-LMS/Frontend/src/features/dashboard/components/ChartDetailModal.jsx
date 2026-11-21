
import { useEffect, useRef } from "react";
import { FiX, FiDownload } from "react-icons/fi";

const PURPLE = "#6B2D5B";

export default function ChartDetailModal({
    title,
    columns = [],
    rows = [],
    loading = false,
    onClose,
    headerControls = null,
    onRowClick = null,
}) {
    const tableScrollRef = useRef(null);

    // Prevent background scrolling while modal is open
    useEffect(() => {
        const previousOverflow = document.body.style.overflow;

        document.body.style.overflow = "hidden";

        return () => {
            document.body.style.overflow = previousOverflow;
        };
    }, []);

    // Reset table scroll when chart data changes
    useEffect(() => {
        tableScrollRef.current?.scrollTo({
            top: 0,
            behavior: "auto",
        });
    }, [title, rows]);

    // Close modal using Escape key
    useEffect(() => {
        const handleEscape = (event) => {
            if (event.key === "Escape") {
                onClose?.();
            }
        };

        window.addEventListener("keydown", handleEscape);

        return () => {
            window.removeEventListener("keydown", handleEscape);
        };
    }, [onClose]);

    // CSV Export
    const handleExport = () => {
        if (loading || !rows.length) return;

        const escapeCSV = (value) => {
            const text = String(value ?? "");
            return `"${text.replace(/"/g, '""')}"`;
        };

        const headers = [
            "#",
            ...columns.map((column) => column.label),
        ];

        const csvRows = rows.map((row, index) => {
            const values = [
                index + 1,
                ...columns.map((column) => {
                    if (column.exportValue) {
                        return column.exportValue(row, index) ?? "";
                    }

                    if (
                        row[column.key] !== undefined &&
                        row[column.key] !== null
                    ) {
                        return row[column.key];
                    }

                    return "";
                }),
            ];

            return values.map(escapeCSV).join(",");
        });

        // UTF-8 BOM for proper Excel compatibility
        const csvContent =
            "\uFEFF" +
            [
                headers.map(escapeCSV).join(","),
                ...csvRows,
            ].join("\r\n");

        const blob = new Blob(
            [csvContent],
            { type: "text/csv;charset=utf-8;" }
        );

        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");

        const fileName = (title || "chart-detail")
            .replace(/[<>:"/\\|?*]/g, "")
            .trim()
            .replace(/\s+/g, "-")
            .toLowerCase();

        link.href = url;
        link.download = `${fileName}.csv`;

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        setTimeout(() => {
            URL.revokeObjectURL(url);
        }, 1000);
    };

    const th =
        "px-4 py-3 text-left text-[13px] font-semibold text-white whitespace-nowrap";

    const td =
        "px-4 py-3 text-[13px] text-[#344050] border-b border-[#EEF0F3] align-top";

    return (
        <div
            className="fixed inset-0 z-[1100] overflow-y-auto bg-black/35"
            onMouseDown={(event) => {
                if (event.target === event.currentTarget) {
                    onClose?.();
                }
            }}
        >
            <div className="flex min-h-full items-center justify-center p-4 sm:p-8">

                <div className="flex max-h-[calc(100vh-2rem)] w-full max-w-6xl flex-col overflow-hidden rounded-lg bg-white shadow-2xl">

                    {/* Header */}
                    <div
                        className="flex flex-none items-center justify-between px-6 py-3"
                        style={{ backgroundColor: PURPLE }}
                    >
                        <div className="text-[18px] font-semibold text-white">
                            {title}
                        </div>

                        <button
                            type="button"
                            onClick={onClose}
                            className="rounded-md p-1 text-white/90 hover:bg-white/15"
                            aria-label="Close"
                        >
                            <FiX size={22} />
                        </button>
                    </div>

                    {/* Modal Content */}
                    <div className="flex min-h-0 flex-1 flex-col p-4">

                        {/* Optional Header Controls */}
                        {headerControls && (
                            <div className="mb-4 flex-none">
                                {headerControls}
                            </div>
                        )}

                        {/* Loading State */}
                        {loading ? (
                            <div className="flex min-h-[250px] flex-1 flex-col items-center justify-center gap-4">

                                <span className="h-12 w-12 animate-spin rounded-full border-4 border-[#E7D5E3] border-t-[#6B2D5B]" />

                                <span className="text-[15px] font-medium text-[#6B2D5B]">
                                    Loading detailed data...
                                </span>

                            </div>
                        ) : (

                            /* Data Table */
                            <div className="min-h-0 flex-1 overflow-hidden rounded-md border border-[#E3E6ED]">

                                <div
                                    ref={tableScrollRef}
                                    className="max-h-[calc(100vh-27rem)] min-h-[160px] overflow-auto"
                                >

                                    <table className="w-full border-collapse">

                                        <thead className="sticky top-0 z-20">
                                            <tr style={{ backgroundColor: PURPLE }}>

                                                <th className={th}>
                                                    #
                                                </th>

                                                {columns.map((column) => (
                                                    <th
                                                        key={column.key}
                                                        className={th}
                                                    >
                                                        {column.label}
                                                    </th>
                                                ))}

                                            </tr>
                                        </thead>

                                        <tbody>

                                            {/* Empty State */}
                                            {rows.length === 0 && (
                                                <tr>
                                                    <td
                                                        className={`${td} py-8 text-center text-[#8A94A6]`}
                                                        colSpan={columns.length + 1}
                                                    >
                                                        No records found.
                                                    </td>
                                                </tr>
                                            )}

                                            {/* Data Rows */}
                                            {rows.map((row, index) => (
                                                <tr
                                                    key={
                                                        row.participant_id ??
                                                        row.id ??
                                                        index
                                                    }
                                                    onClick={() =>
                                                        onRowClick?.(row, index)
                                                    }
                                                    className={`group transition-colors ${onRowClick
                                                        ? "cursor-pointer hover:bg-[#F8F4F8]"
                                                        : "hover:bg-[#FAFBFD]"
                                                        }`}
                                                    title={
                                                        onRowClick
                                                            ? `View profile of ${row.name || "learner"}`
                                                            : undefined
                                                    }
                                                >

                                                    <td className={td}>
                                                        {index + 1}
                                                    </td>

                                                    {columns.map((column) => (
                                                        <td
                                                            key={column.key}
                                                            className={td}
                                                        >
                                                            {column.render
                                                                ? column.render(row, index)
                                                                : row[column.key] ?? "-"
                                                            }
                                                        </td>
                                                    ))}

                                                </tr>
                                            ))}

                                        </tbody>

                                    </table>

                                </div>

                            </div>
                        )}

                        {/* Footer */}

                        {/* Footer */}
                        <div className="mt-3 flex flex-none items-center justify-between gap-3 border-t border-[#E8E1E7] bg-transparent px-1 pt-3">

                            {/* Showing Records */}
                            <span className="text-[12px] font-medium text-[#647084]">
                                {loading
                                    ? "Loading..."
                                    : `Showing ${rows.length} of ${rows.length} records`
                                }
                            </span>

                            {/* Footer Actions */}
                            <div className="flex shrink-0 items-center gap-2">

                                <button
                                    type="button"
                                    onClick={handleExport}
                                    disabled={loading || rows.length === 0}
                                    className="inline-flex items-center justify-center gap-2 rounded-md border border-[#6B2D5B] bg-transparent px-4 py-2 text-[12px] font-semibold text-[#6B2D5B] transition-all hover:bg-[#F7EFF5] disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    <FiDownload size={15} />
                                    Export Data
                                </button>

                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="inline-flex items-center justify-center rounded-md border border-[#DDE1E7] bg-transparent px-5 py-2 text-[12px] font-medium text-[#344050] transition-all hover:bg-[#F2EFF2]"
                                >
                                    Close
                                </button>

                            </div>
                        </div>

                    </div>

                </div>

            </div>
        </div>
    );
}
