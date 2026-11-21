import { FaClipboardCheck, FaCheckCircle, FaBook } from "react-icons/fa";

import ResultStats from "./ResultStats";

const PASS_THRESHOLD = 40;

const fmt = (n) => {
    const num = Number(n || 0);
    return Number.isInteger(num) ? String(num) : num.toFixed(2);
};

/**
 * "Post Assessment Result (Module-Wise)" — the overall summary card that sits
 * directly under the participant profile.
 */
export default function AssessmentSummary({ summary }) {
    if (!summary) return null;

    const percentage = Number(summary.percentage || 0);
    const passed = percentage >= PASS_THRESHOLD;

    const completedMods = Number(summary.completed_modules || 0);
    const totalMods = Number(summary.total_assigned_modules || 0);
    const modPct = totalMods > 0 ? Math.round((completedMods / totalMods) * 100) : 0;

    return (
        <div className="overflow-hidden rounded-[6px] border border-[#D8E2EF] bg-white">
            {/* Purple header */}
            <div className="flex items-center justify-between bg-[#732269] px-4 py-3 text-white">
                <div className="flex items-center gap-2">
                    <FaClipboardCheck size={15} />
                    <span className="text-[15px] font-semibold">
                        Post Assessment Result (Module-Wise)
                    </span>
                </div>
                {totalMods > 0 && (
                    <div className="flex items-center gap-2 text-[13px]">
                        <FaBook size={12} />
                        <span>
                            Overall Module Completion:{" "}
                            <span className="font-semibold">
                                {completedMods} of {totalMods}
                            </span>{" "}
                            ({modPct}%)
                        </span>
                    </div>
                )}
            </div>

            <div className="p-4">
                {/* Success / status banner */}
                <div
                    className={`mb-4 flex items-center gap-2 rounded-[4px] border px-3 py-2 text-[13px] ${
                        passed
                            ? "border-[#C3E6CB] bg-[#EAF7EE] text-[#2E7D32]"
                            : "border-[#F5C2C7] bg-[#FDECEA] text-[#D74D43]"
                    }`}
                >
                    <FaCheckCircle size={13} />
                    <span>
                        Overall post assessment score is {fmt(percentage)}%.{" "}
                        {passed
                            ? "Assessment passed successfully."
                            : "Assessment not passed."}
                    </span>
                </div>

                <ResultStats
                    variant="overall"
                    totalQuestions={summary.total_questions}
                    completed={summary.completed_questions}
                    correct={summary.correct}
                    wrong={summary.wrong}
                    score={summary.score}
                    totalMarks={summary.total_marks}
                    percentage={summary.percentage}
                    progress={summary.progress}
                />
            </div>
        </div>
    );
}
