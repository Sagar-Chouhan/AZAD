import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import AuthShell from "./AuthShell";
import logo from "@/assets/logos/logo.svg";
import { getCaptcha, loginUser } from "@/api/AuthApi";

export default function Login() {
    const navigate = useNavigate();

    useEffect(() => {
        document.title = "Azad Learner Portal";
    }, []);

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [showPw, setShowPw] = useState(false);
    const [answer, setAnswer] = useState("");
    const [captchaQuestion, setCaptchaQuestion] = useState("");
    const [captchaToken, setCaptchaToken] = useState("");
    const [captchaLoading, setCaptchaLoading] = useState(true);
    const [note, setNote] = useState(null); // { text, ok }
    const [busy, setBusy] = useState(false);

    const loadCaptcha = async () => {
        try {
            setCaptchaLoading(true);
            const response = await getCaptcha();
            setCaptchaQuestion(response?.question || "");
            setCaptchaToken(response?.captcha_token || "");
            setAnswer("");
        } catch (error) {
            console.error("Failed to load captcha:", error);
            setNote({ text: "Failed to load captcha. Please try again.", ok: false });
        } finally {
            setCaptchaLoading(false);
        }
    };

    useEffect(() => {
        loadCaptcha();
    }, []);

    // Auto-dismiss note after 6 seconds
    useEffect(() => {
        if (!note) return undefined;
        const timer = setTimeout(() => setNote(null), 6000);
        return () => clearTimeout(timer);
    }, [note]);

    const handleSubmit = async (e) => {
        if (e && e.preventDefault) e.preventDefault();

        if (!username.trim()) {
            setNote({ text: "Please enter your username or email.", ok: false });
            return;
        }
        if (!password) {
            setNote({ text: "Please enter your password.", ok: false });
            return;
        }
        if (!answer.trim()) {
            setNote({ text: "Please enter the security answer.", ok: false });
            return;
        }
        if (!captchaToken) {
            setNote({ text: "Captcha expired. Please reload captcha.", ok: false });
            await loadCaptcha();
            return;
        }

        setNote(null);
        setBusy(true);

        try {
            const payload = {
                email: username.trim(),
                password: password,
                captcha_answer: Number(answer.trim()),
                captcha_token: captchaToken,
            };

            const response = await loginUser(payload);

            if (response?.access_token) {
                localStorage.setItem("access_token", response.access_token);
                localStorage.setItem("refresh_token", response.refresh_token);
                localStorage.setItem("user", JSON.stringify(response.user));
                localStorage.setItem("userRole", response.user?.role || "");
            }

            navigate("/dashboard");
        } catch (error) {
            const detail = error.response?.data?.detail;
            let errMsg = "Login failed. Please check your credentials.";

            if (typeof detail === "string") {
                errMsg = detail;
            } else if (Array.isArray(detail) && detail.length > 0) {
                errMsg = detail[0]?.msg || "Login failed";
            } else if (detail && typeof detail === "object") {
                errMsg = JSON.stringify(detail);
            }

            setNote({ text: errMsg, ok: false });
            setAnswer("");
            await loadCaptcha();
        } finally {
            setBusy(false);
        }
    };

    // Clean up "= ?" if present in question (e.g. "4 + 7 = ?" -> "4 + 7")
    const displayQuestion = captchaQuestion
        ? captchaQuestion.replace(/\s*=\s*\?*\s*$/, "")
        : "";

    return (
        <AuthShell rightBgClass="bg-[#e7d2e2]">
            <div className="mt-4 rounded-lg border border-ink/10 bg-white px-6 py-5 shadow-[0_16px_36px_-24px_rgba(56,10,40,.32)]">
                <img src={logo} alt="Azad Foundation" className="mx-auto mb-5 block h-[52px] w-auto" />
                <h1 className="ff-serif text-center text-ink text-[26px] font-medium leading-[1.12] tracking-tight">
                    Welcome &amp; sign in
                </h1>

                <form className="mt-5 space-y-3" noValidate onSubmit={handleSubmit}>
                    {/* Username */}
                    <div>
                        <label htmlFor="username" className="lbl mb-1.5 block">
                            Username or Email
                        </label>
                        <div className="relative">
                            <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted">
                                <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M20 21a8 8 0 0 0-16 0" />
                                    <circle cx="12" cy="8" r="4" />
                                </svg>
                            </span>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                autoComplete="username"
                                required
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Enter your username or email"
                                className="field h-10 w-full rounded-lg pl-12 pr-4 text-[15px] text-ink"
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div>
                        <label htmlFor="password" className="lbl mb-1.5 block">
                            Password
                        </label>
                        <div className="relative">
                            <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted">
                                <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                                    <rect x="4" y="11" width="16" height="9" rx="2" />
                                    <path d="M8 11V7a4 4 0 0 1 8 0v4" />
                                </svg>
                            </span>
                            <input
                                id="password"
                                name="password"
                                type={showPw ? "text" : "password"}
                                autoComplete="current-password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                className="field h-10 w-full rounded-lg pl-12 pr-12 text-[15px] text-ink"
                            />
                            <button
                                type="button"
                                aria-label={showPw ? "Hide password" : "Show password"}
                                aria-pressed={showPw}
                                onClick={() => setShowPw((v) => !v)}
                                className="absolute right-2 top-2 bottom-2 flex w-10 items-center justify-center rounded-lg text-muted hover:text-plum-600 hover:bg-plum-50"
                            >
                                <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                                    {showPw ? (
                                        <>
                                            <path d="M3 3l18 18" />
                                            <path d="M10.6 10.6a3 3 0 0 0 4.2 4.2" />
                                            <path d="M9.9 4.6A10.9 10.9 0 0 1 12 4.5c6.5 0 10 7 10 7a18 18 0 0 1-3.2 4" />
                                            <path d="M6.6 6.6A18 18 0 0 0 2 12s3.5 7 10 7a10.8 10.8 0 0 0 2.4-.3" />
                                        </>
                                    ) : (
                                        <>
                                            <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
                                            <circle cx="12" cy="12" r="3" />
                                        </>
                                    )}
                                </svg>
                            </button>
                        </div>
                    </div>

                    {/* Security answer (Dynamic Captcha) */}
                    <div>
                        <label htmlFor="answer" className="lbl mb-1.5 block">
                            Security answer
                        </label>
                        <div className="flex items-stretch gap-3">
                            <div className="flex h-10 shrink-0 items-center gap-3 rounded-lg bg-plum-50 px-4">
                                <span className="ff-serif text-[19px] font-medium text-ink tabular-nums">
                                    {captchaLoading ? "..." : (displayQuestion || "—")} <span className="text-muted">=</span>
                                </span>
                                <button
                                    type="button"
                                    aria-label="New question"
                                    onClick={loadCaptcha}
                                    disabled={captchaLoading}
                                    title="Reload captcha"
                                    className="grid h-8 w-8 place-items-center rounded-lg text-plum-600 hover:bg-plum-100 disabled:opacity-50"
                                >
                                    <svg
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        className={captchaLoading ? "animate-spin" : ""}
                                    >
                                        <path d="M21 12a9 9 0 1 1-2.6-6.4" />
                                        <path d="M21 3v5h-5" />
                                    </svg>
                                </button>
                            </div>
                            <input
                                id="answer"
                                name="answer"
                                type="text"
                                inputMode="numeric"
                                required
                                aria-label="Type the answer"
                                value={answer}
                                onChange={(e) => setAnswer(e.target.value.replace(/\D/g, ""))}
                                placeholder="Answer"
                                className="field h-10 w-full rounded-lg px-4 text-[15px] text-ink tabular-nums"
                            />
                        </div>
                    </div>

                    <div className="flex justify-end">
                        <Link to="/forgot-password" className="ulink text-[14.5px] font-semibold">
                            Forgot password?
                        </Link>
                    </div>

                    <button
                        type="submit"
                        disabled={busy}
                        className="cta mt-1 flex h-11 w-full items-center justify-center gap-2.5 rounded-lg text-[15.5px] font-semibold text-white disabled:opacity-60"
                    >
                        <span
                            className={
                                "spin h-[18px] w-[18px] rounded-full border-[2.4px] border-white/40 border-t-white" +
                                (busy ? "" : " hidden")
                            }
                        />
                        <span>{busy ? "Signing in…" : "Sign in"}</span>
                    </button>

                    {note && (
                        <p
                            role="status"
                            aria-live="polite"
                            className="text-center text-[13px] font-medium"
                            style={{ color: note.ok ? "#2f8a6b" : "#c0365a" }}
                        >
                            {note.text}
                        </p>
                    )}
                </form>
            </div>
        </AuthShell>
    );
}
