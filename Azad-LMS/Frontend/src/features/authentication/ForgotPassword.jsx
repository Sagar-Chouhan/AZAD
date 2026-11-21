import React, { useState } from "react";
import { Link } from "react-router-dom";
import AuthShell from "./AuthShell";
import logo from "@/assets/logos/logo.svg";

export default function ForgotPassword() {
    const [email, setEmail] = useState("");
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (email.trim()) {
            setSubmitted(true);
        }
    };

    return (
        <AuthShell rightBgClass="bg-[#e7d2e2]">
            <div className="mt-4 rounded-lg border border-ink/10 bg-white px-6 py-5 shadow-[0_16px_36px_-24px_rgba(56,10,40,.32)]">
                <img src={logo} alt="Azad Foundation" className="mx-auto mb-5 block h-[52px] w-auto" />
                <h1 className="ff-serif text-center text-ink text-[26px] font-medium leading-[1.12] tracking-tight">
                    Reset your password
                </h1>
                <p className="mt-1 text-center text-[14px] text-muted">
                    Enter your email to receive a password recovery link.
                </p>

                {submitted ? (
                    <div className="mt-6 text-center space-y-4">
                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <p className="text-[14.5px] text-ink font-medium">
                            If an account exists for <span className="font-semibold text-plum-700">{email}</span>, a reset link has been sent.
                        </p>
                        <Link
                            to="/login"
                            className="cta flex h-10 w-full items-center justify-center rounded-lg text-[14.5px] font-semibold text-white"
                        >
                            Back to Sign in
                        </Link>
                    </div>
                ) : (
                    <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
                        <div>
                            <label htmlFor="email" className="lbl mb-1.5 block">
                                Email Address
                            </label>
                            <div className="relative">
                                <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted">
                                    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                                        <rect width="20" height="16" x="2" y="4" rx="2" />
                                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                                    </svg>
                                </span>
                                <input
                                    id="email"
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="Enter your registered email"
                                    className="field h-10 w-full rounded-lg pl-12 pr-4 text-[15px] text-ink"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="cta mt-2 flex h-11 w-full items-center justify-center rounded-lg text-[15.5px] font-semibold text-white"
                        >
                            Send reset link
                        </button>

                        <div className="text-center pt-2">
                            <Link to="/login" className="ulink text-[14px] font-semibold">
                                &larr; Back to sign in
                            </Link>
                        </div>
                    </form>
                )}
            </div>
        </AuthShell>
    );
}
