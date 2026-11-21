import { useEffect, useState, useCallback } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { FiBox, FiArrowLeft, FiX } from "react-icons/fi";

import AppLayout from "@/components/layout/AppLayout";
import Breadcrumbs from "@/shared/components/breadcrumbs/Breadcrumbs";
import LanguageTabs from "@/shared/components/language/LanguageTabs";
import {
    getLanguageByKey,
} from "@/shared/constants/languageConstants";

import {
    getModuleById,
    getModuleTranslation,
} from "@/features/module/ListModule/services/ListService";

import {
    getMainContentList,
    getPostAssessments,
    getPreAssessments,
    deactivateMainContent,
    activateMainContent,
    getSelfPacedList,
    createSelfPacedContent,
} from "@/features/module/ListModule/services/ConfigurationService";

import { getDocument } from "@/features/document/services/DocumentServices";

import ConfigSection from "@/features/module/ListModule/components/configuration/ConfigSection";
import ContentTable from "@/features/module/ListModule/components/configuration/ContentTable";
import AssessmentSection from "@/features/module/ListModule/components/configuration/AssessmentSection";
import AddContentModal from "@/features/module/ListModule/components/configuration/AddContentModal";

const breadcrumbItems = [
    { label: "Home", path: "/dashboard" },
    { label: "Modules", path: "/modules" },
    { label: "Configuration" },
];

const MEDIA_URL = import.meta.env.VITE_API_URL;

const toMediaUrl = (path) => {
    if (!path || typeof path !== "string") return "";
    if (/^https?:\/\//i.test(path)) return path;
    return `${MEDIA_URL}/${path.replace(/^app\//, "").replace(/^\/+/, "")}`;
};

const toYoutubeEmbedUrl = (url) => {
    if (!url) return "";
    if (url.includes("/embed/")) return url;
    return url.replace("watch?v=", "embed/");
};

export default function ConfigureModule() {
    const { moduleId } = useParams();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [videoPreview, setVideoPreview] = useState(null);
    const [videoLoading, setVideoLoading] = useState(false);

    /* ================= LANGUAGE ================= */

    const [languageKey, setLanguageKey] = useState(
        (searchParams.get("tab") || "english").toLowerCase()
    );

    const language = getLanguageByKey(languageKey);
    const languageId = language?.id;

    /*
     * Configuration is stored against the English/base module.
     *
     * Example:
     * Hindi module   = 46
     * English module = 49
     *
     * URL:
     * /configure/46?tab=hindi
     *
     * We must use 49 for configuration APIs,
     * but use languageId = 2 for Hindi content.
     */

    const [configModuleId, setConfigModuleId] = useState(null);

    const isEnglish = languageId === 1;

    /* ================= RESOLVE CONFIG MODULE ================= */

    useEffect(() => {
        let cancelled = false;

        const resolveConfigModule = async () => {
            if (!moduleId || !languageId) {
                if (!cancelled) {
                    setConfigModuleId(null);
                }
                return;
            }

            try {
                /*
                 * English:
                 * The current module itself is the configuration module.
                 */
                if (languageId === 1) {
                    if (!cancelled) {
                        setConfigModuleId(Number(moduleId));
                    }

                    return;
                }

                /*
                 * Hindi / Bangla / Tamil:
                 *
                 * Find the English translation belonging
                 * to the same module family.
                 */
                const englishModule = await getModuleTranslation(
                    moduleId,
                    1
                );

                console.log(
                    "English module resolved from translation:",
                    englishModule
                );

                const englishId =
                    englishModule?.module_id ??
                    englishModule?.id ??
                    englishModule?.data?.module_id ??
                    englishModule?.data?.id;

                if (!cancelled) {
                    if (englishId) {
                        setConfigModuleId(Number(englishId));
                    } else {
                        console.error(
                            "English module ID not found:",
                            englishModule
                        );

                        setConfigModuleId(null);
                    }
                }
            } catch (error) {
                console.error(
                    "Failed to resolve configuration module:",
                    error?.response?.data ?? error
                );

                if (!cancelled) {
                    setConfigModuleId(null);
                }
            }
        };

        resolveConfigModule();

        return () => {
            cancelled = true;
        };
    }, [moduleId, languageId]);

    /* ================= MODULE NAME ================= */

    const [moduleName, setModuleName] = useState("");

    const loadModuleName = useCallback(async () => {
        if (!moduleId || !languageId) {
            setModuleName("");
            return;
        }

        try {
            const res =
                languageId === 1
                    ? await getModuleById(moduleId)
                    : await getModuleTranslation(
                        moduleId,
                        languageId
                    );

            const data = res?.data ?? res;

            setModuleName(
                data?.module_name ||
                data?.name ||
                ""
            );
        } catch (error) {
            console.error(
                "Error loading module name:",
                error?.response?.data ?? error
            );

            setModuleName("");
        }
    }, [moduleId, languageId]);

    useEffect(() => {
        loadModuleName();
    }, [loadModuleName]);

    /* ================= MAIN CONTENT ================= */

    const [mainRows, setMainRows] = useState([]);
    const [mainLoading, setMainLoading] = useState(false);
    const [addContentOpen, setAddContentOpen] = useState(false);

    const loadMainContent = useCallback(async () => {
        if (!configModuleId || !languageId) {
            setMainRows([]);
            return;
        }

        try {
            setMainLoading(true);

            /*
             * IMPORTANT:
             *
             * Configuration belongs to configModuleId.
             * languageId controls the localized document data.
             */
            const result = await getMainContentList(
                configModuleId,
                languageId
            );

            console.log(
                "Main content:",
                {
                    configModuleId,
                    languageId,
                    result,
                }
            );

            const data = Array.isArray(result)
                ? result
                : [];

            const rows = data.map((item) => ({
                id: item.self_paced_learning_id,
                document: item.doc_title,
                contentType: item.doc_type,
                docId: item.doc_id,
                docRefId: item.doc_ref_id,
                isActive:
                    String(item.is_active) === "1",
            }));

            setMainRows(rows);
        } catch (error) {
            console.error(
                "Error loading main content:",
                error?.response?.data ?? error
            );

            setMainRows([]);
        } finally {
            setMainLoading(false);
        }
    }, [configModuleId, languageId]);

    useEffect(() => {
        loadMainContent();
    }, [loadMainContent]);

    /* ================= MAIN CONTENT TOGGLE ================= */

    const handleToggleMain = async (row) => {
        const nextAction = row.isActive
            ? "deactivate"
            : "activate";

        const confirmed = window.confirm(
            `${row.isActive ? "Deactivate" : "Activate"} "${row.document}"?`
        );

        if (!confirmed) return;

        try {
            if (row.isActive) {
                await deactivateMainContent(row.id);

                toast.success(
                    "Content deactivated."
                );
            } else {
                await activateMainContent(row.id);

                toast.success(
                    "Content activated."
                );
            }

            loadMainContent();
        } catch (error) {
            toast.error(
                error?.response?.data?.detail ||
                `Unable to ${nextAction} content.`
            );
        }
    };

    /* ================= SELF-PACED LEARNING ================= */

    const [selfRows, setSelfRows] = useState([]);
    const [selfLoading, setSelfLoading] = useState(false);
    const [addSelfOpen, setAddSelfOpen] = useState(false);

    const loadSelfContent = useCallback(async () => {
        if (!configModuleId || !languageId) {
            setSelfRows([]);
            return;
        }

        try {
            setSelfLoading(true);

            /*
             * Use the configuration/base module ID.
             * languageId decides which language is displayed.
             */
            const result = await getSelfPacedList(
                configModuleId,
                languageId
            );

            console.log(
                "Self paced content:",
                {
                    configModuleId,
                    languageId,
                    result,
                }
            );

            const data = Array.isArray(result)
                ? result
                : [];

            const rows = data.map((item) => ({
                id: item.self_paced_learning_id,
                document: item.doc_title,
                contentType: item.doc_type,
                docId: item.doc_id,
                docRefId: item.doc_ref_id,
                isActive:
                    String(item.is_active) === "1",
            }));

            setSelfRows(rows);
        } catch (error) {
            console.error(
                "Error loading self-paced content:",
                error?.response?.data ?? error
            );

            setSelfRows([]);
        } finally {
            setSelfLoading(false);
        }
    }, [configModuleId, languageId]);

    useEffect(() => {
        loadSelfContent();
    }, [loadSelfContent]);

    /* ================= SELF-PACED TOGGLE ================= */

    const handleToggleSelf = async (row) => {
        const nextAction = row.isActive
            ? "deactivate"
            : "activate";

        const confirmed = window.confirm(
            `${row.isActive ? "Deactivate" : "Activate"} "${row.document}"?`
        );

        if (!confirmed) return;

        try {
            if (row.isActive) {
                await deactivateMainContent(row.id);

                toast.success(
                    "Content deactivated."
                );
            } else {
                await activateMainContent(row.id);

                toast.success(
                    "Content activated."
                );
            }

            loadSelfContent();
        } catch (error) {
            toast.error(
                error?.response?.data?.detail ||
                `Unable to ${nextAction} content.`
            );
        }
    };

    /* ================= VIEW CONTENT ================= */

    const TYPE_ROUTE = {
        PDF: "/pdf-masters",
        PPT: "/ppt-masters",
        VIDEO: "/video-masters",
    };

    const handleViewContent = async (row) => {
        const type = String(
            row.contentType
        ).toUpperCase();

        const base = TYPE_ROUTE[type];

        if (type === "VIDEO") {
            setVideoLoading(true);

            try {
                const res = row.docId
                    ? await getDocument(row.docId)
                    : null;
                const doc = res?.document ?? res?.data ?? res ?? {};
                const videoUrl = toMediaUrl(doc.video_url);
                const youtubeUrl = toYoutubeEmbedUrl(doc.youtube_url);

                if (videoUrl || youtubeUrl) {
                    setVideoPreview({
                        title: doc.doc_title || row.document || "Video Preview",
                        videoUrl,
                        youtubeUrl,
                    });
                } else if (row.docRefId) {
                    navigate(`${base}/${row.docRefId}`);
                } else {
                    toast.error("Video preview is not available.");
                }
            } catch (error) {
                toast.error(
                    error?.response?.data?.detail ||
                    "Unable to load video preview."
                );
            } finally {
                setVideoLoading(false);
            }

            return;
        }

        if (base) {
            let refId = row.docRefId;

            if (!refId && row.docId) {
                try {
                    const res = await getDocument(
                        row.docId
                    );

                    const doc =
                        res?.document ??
                        res?.data ??
                        res;

                    refId = doc?.doc_ref_id;
                } catch (error) {
                    console.error(
                        "Error resolving document:",
                        error
                    );

                    refId = null;
                }
            }

            if (refId) {
                navigate(`${base}/${refId}`);
                return;
            }
        }

        navigate(
            `/module-master/configure/${configModuleId || moduleId
            }?tab=${languageKey}`
        );
    };

    /* ================= POST-SESSION ASSESSMENT ================= */

    const [
        postAssessmentId,
        setPostAssessmentId,
    ] = useState(null);

    const [
        preAssessmentId,
        setPreAssessmentId,
    ] = useState(null);

    useEffect(() => {
        const load = async () => {
            if (!configModuleId) {
                setPostAssessmentId(null);
                return;
            }

            try {
                const res =
                    await getPostAssessments(
                        configModuleId
                    );

                const first =
                    res?.assessments?.[0]
                        ?.assessment_id ?? null;

                setPostAssessmentId(first);
            } catch (error) {
                console.error(
                    "Error loading post assessment:",
                    error?.response?.data ?? error
                );

                setPostAssessmentId(null);
            }
        };

        load();
    }, [configModuleId]);

    /* ================= PRE-SESSION ASSESSMENT ================= */

    useEffect(() => {
        const load = async () => {
            if (!configModuleId) {
                setPreAssessmentId(null);
                return;
            }

            try {
                const res =
                    await getPreAssessments(
                        configModuleId
                    );

                const first =
                    res?.assessments?.[0]
                        ?.assessment_id ?? null;

                setPreAssessmentId(first);
            } catch (error) {
                console.error(
                    "Error loading pre assessment:",
                    error?.response?.data ?? error
                );

                setPreAssessmentId(null);
            }
        };

        load();
    }, [configModuleId]);

    /* ================= RENDER ================= */

    return (
        <AppLayout>

            {/* ================= HEADER ================= */}

            <div className="mb-3 flex items-center justify-between">
                <span className="text-[20px] font-medium text-[#344050]">
                    Module Configuration
                </span>

                <Breadcrumbs
                    items={breadcrumbItems}
                />
            </div>

            {/* ================= LANGUAGE TABS ================= */}

            <LanguageTabs
                activeTab={languageKey}
                onChange={setLanguageKey}
            />

            {/* ================= MODULE NAME ================= */}

            <div className="mb-[24px] flex items-center gap-[10px] rounded-b-[6px] border border-t-0 border-[#D8E2EF] bg-white px-[16px] py-[14px]">

                <span className="flex h-[26px] w-[26px] items-center justify-center rounded-full bg-[#732269] text-white">
                    <FiBox size={14} />
                </span>

                <span className="text-[15px] font-semibold text-[#732269]">
                    Module Name ({language?.label}):{" "}
                    {moduleName || "-"}
                </span>

            </div>

            {/* ================= 1. SELF-PACED LEARNING ================= */}

            <ConfigSection
                title="Self-Paced Learning (Optional)"
                addTitle="Add self-paced content"
                onAdd={() =>
                    setAddSelfOpen(true)
                }
                showAdd={isEnglish}
            >
                <ContentTable
                    rows={selfRows}
                    loading={selfLoading}
                    emptyMessage="No data available in table"
                    renderAction={(row) => (
                        <div className="flex items-center gap-[8px]">

                            {row.isActive && (
                                <button
                                    type="button"
                                    onClick={() =>
                                        handleViewContent(
                                            row
                                        )
                                    }
                                    className="h-[30px] rounded-[4px] border border-[#732269] bg-white px-[12px] text-[12px] font-medium text-[#732269] hover:bg-[#f7edf5]"
                                >
                                    View Content
                                </button>
                            )}

                            <button
                                type="button"
                                onClick={() =>
                                    handleToggleSelf(
                                        row
                                    )
                                }
                                className={`h-[30px] rounded-[4px] px-[14px] text-[12px] font-medium text-white ${row.isActive
                                        ? "bg-[#732269] hover:bg-[#611c58]"
                                        : "bg-[#2E7D32] hover:bg-[#256628]"
                                    }`}
                            >
                                {row.isActive
                                    ? "Deactivate"
                                    : "Activate"}
                            </button>

                        </div>
                    )}
                />
            </ConfigSection>

            {/* ================= 2. PRE-SESSION ASSESSMENT ================= */}

            <AssessmentSection
                title="Pre-Session Assessment (Optional)"
                assessmentId={preAssessmentId}
                available={Boolean(
                    preAssessmentId
                )}
                languageId={languageId}
                moduleName={moduleName}
                canAdd={isEnglish}
            />

            {/* ================= 3. MAIN CONTENT ================= */}

            <ConfigSection
                title="Main Content of the Module (Compulsory)"
                addTitle="Add content"
                onAdd={() =>
                    setAddContentOpen(true)
                }
                showAdd={isEnglish}
            >
                <ContentTable
                    rows={mainRows}
                    loading={mainLoading}
                    emptyMessage="No data available in table"
                    renderAction={(row) => (
                        <div className="flex items-center gap-[8px]">

                            {row.isActive && (
                                <button
                                    type="button"
                                    onClick={() =>
                                        handleViewContent(
                                            row
                                        )
                                    }
                                    className="h-[30px] rounded-[4px] border border-[#732269] bg-white px-[12px] text-[12px] font-medium text-[#732269] hover:bg-[#f7edf5]"
                                >
                                    View Content
                                </button>
                            )}

                            <button
                                type="button"
                                onClick={() =>
                                    handleToggleMain(
                                        row
                                    )
                                }
                                className={`h-[30px] rounded-[4px] px-[14px] text-[12px] font-medium text-white ${row.isActive
                                        ? "bg-[#732269] hover:bg-[#611c58]"
                                        : "bg-[#2E7D32] hover:bg-[#256628]"
                                    }`}
                            >
                                {row.isActive
                                    ? "Deactivate"
                                    : "Activate"}
                            </button>

                        </div>
                    )}
                />
            </ConfigSection>

            {/* ================= 4. POST-SESSION ASSESSMENT ================= */}

            <AssessmentSection
                title="Post-Session Assessment (Compulsory)"
                assessmentId={postAssessmentId}
                available={true}
                languageId={languageId}
                moduleName={moduleName}
                canAdd={isEnglish}
            />

            {/* ================= BACK TO LIST ================= */}

            <div className="mt-[6px]">
                <button
                    type="button"
                    onClick={() =>
                        navigate("/modules")
                    }
                    className="inline-flex h-[38px] items-center gap-[8px] rounded-[4px] border border-[#344050] bg-white px-[16px] text-[14px] font-medium text-[#344050] hover:bg-[#f8f9fa]"
                >
                    <FiArrowLeft size={16} />
                    Back to Module List
                </button>
            </div>

            {/* ================= MODALS ================= */}

            <AddContentModal
                open={addContentOpen}
                onClose={() =>
                    setAddContentOpen(false)
                }
                moduleId={
                    configModuleId || moduleId
                }
                languageId={languageId}
                onSaved={loadMainContent}
            />

            <AddContentModal
                open={addSelfOpen}
                onClose={() =>
                    setAddSelfOpen(false)
                }
                moduleId={
                    configModuleId || moduleId
                }
                languageId={languageId}
                onSaved={loadSelfContent}
                title="Add Self-Paced Learning Content"
                createContent={
                    createSelfPacedContent
                }
            />

            {videoLoading && (
                <div className="fixed inset-0 z-[1100] flex items-center justify-center bg-black/60">
                    <div className="border border-[#D8E2EF] bg-white px-6 py-5 text-[13px] text-[#344050]">
                        Loading video...
                    </div>
                </div>
            )}

            {videoPreview && (
                <div
                    className="fixed inset-0 z-[1100] flex items-center justify-center bg-black/70 p-4"
                    role="dialog"
                    aria-modal="true"
                    aria-label="Video preview"
                    onMouseDown={(event) => {
                        if (event.target === event.currentTarget) {
                            setVideoPreview(null);
                        }
                    }}
                >
                    <div className="w-full max-w-4xl border border-[#D8E2EF] bg-white shadow-2xl">
                        <div className="flex items-center justify-between border-b border-[#E5E7EB] px-4 py-3">
                            <h2 className="m-0 truncate pr-4 text-[15px] font-semibold text-[#344050]">
                                {videoPreview.title}
                            </h2>
                            <button
                                type="button"
                                onClick={() => setVideoPreview(null)}
                                aria-label="Close video preview"
                                title="Close video preview"
                                className="flex h-8 w-8 items-center justify-center border border-[#D8E2EF] text-[#344050] transition-colors hover:bg-[#F5F6F8] hover:text-[#732269]"
                            >
                                <FiX size={18} aria-hidden="true" />
                            </button>
                        </div>

                        <div className="bg-black p-3">
                            {videoPreview.youtubeUrl ? (
                                <iframe
                                    title={videoPreview.title}
                                    src={videoPreview.youtubeUrl}
                                    className="aspect-video w-full border-0"
                                    allow="autoplay; encrypted-media; picture-in-picture"
                                    allowFullScreen
                                />
                            ) : (
                                <video
                                    src={videoPreview.videoUrl}
                                    className="max-h-[75vh] w-full"
                                    controls
                                    autoPlay
                                    playsInline
                                />
                            )}
                        </div>
                    </div>
                </div>
            )}

        </AppLayout>
    );
}