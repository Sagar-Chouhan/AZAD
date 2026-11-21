import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import logo from "@/assets/logos/logo.svg";

// Shared layout for the Privacy Policy and Disclaimer pages: sticky header,
// plum hero, a sticky table-of-contents that scroll-spies the sections, the
// white content card (passed as children), the closing note and the footer.
export default function DocLayout({ badge, title, intro, toc, current, children }) {
    const [active, setActive] = useState(toc[0] ? toc[0].id : null);

    useEffect(() => {
        document.title = title + " — Azad Foundation LMS";
        window.scrollTo(0, 0);
    }, [title]);

    useEffect(() => {
        const spy = new IntersectionObserver(
            (entries) => {
                entries.forEach((e) => {
                    if (e.isIntersecting) setActive(e.target.id);
                });
            },
            { rootMargin: "-20% 0px -60% 0px", threshold: 0 }
        );
        document.querySelectorAll("section[id]").forEach((s) => spy.observe(s));
        return () => spy.disconnect();
    }, []);

    const scrollTo = (e, id) => {
        e.preventDefault();
        const el = document.getElementById(id);
        if (el) {
            const top = el.getBoundingClientRect().top + window.pageYOffset - 85;
            window.scrollTo({ top, behavior: "smooth" });
            setActive(id);
        }
    };

    return (
        <div className="doc-page">
            {/* Header */}
            <header className="sticky top-0 z-50 border-b border-ink/10 bg-white/90 backdrop-blur-md">
                <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3.5 sm:px-8">
                    <Link to="/" className="flex items-center no-underline" aria-label="Azad Foundation home" style={{ textDecoration: "none" }}>
                        <img src={logo} alt="Azad Foundation" className="h-10 sm:h-11 w-auto" />
                    </Link>
                    <Link
                        to="/login"
                        style={{ textDecoration: "none" }}
                        className="group inline-flex items-center gap-2 rounded-full border border-ink/12 bg-white px-4 py-2 text-[13.5px] font-medium text-ink2 no-underline transition hover:border-plum-600 hover:text-plum-600 shadow-2xs"
                    >
                        <i className="fi fi-rr-angle-small-left text-[15px] transition-transform group-hover:-translate-x-0.5" />
                        Back to sign in
                    </Link>
                </div>
            </header>

            {/* Hero */}
            <section className="relative overflow-hidden border-b border-plum-900/40 bg-plum-800">
                <div className="pointer-events-none absolute -right-16 -top-20 h-72 w-72 rounded-full bg-white/5" />
                <div className="pointer-events-none absolute -left-10 bottom-[-60px] h-48 w-48 rotate-45 rounded-[2rem] bg-white/5" />
                <div className="relative mx-auto max-w-6xl px-5 py-12 sm:px-8 sm:py-16">
                    <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3.5 py-1.5 text-[11.5px] font-semibold uppercase tracking-[0.18em] text-white ring-1 ring-white/20">
                        {badge}
                    </span>
                    <h1 className="ff-serif mt-5 text-[38px] sm:text-[50px] font-semibold leading-[1.05] tracking-tight text-white">
                        {title}
                    </h1>
                    <p className="mt-4 max-w-2xl text-[15.5px] sm:text-[17px] leading-relaxed text-white/80">
                        {intro}
                    </p>
                </div>
            </section>

            {/* Body */}
            <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 lg:grid lg:grid-cols-[260px_1fr] lg:gap-10 lg:py-14">
                <aside className="mb-8 lg:mb-0 w-full lg:w-[260px] shrink-0">
                    <nav className="rounded-2xl border border-ink/8 bg-white p-3.5 sm:p-4 shadow-[0_16px_40px_-32px_rgba(42,8,32,.35)] lg:sticky lg:top-24">
                        <p className="mb-3 flex items-center gap-2 px-1 text-[11px] font-bold uppercase tracking-[0.16em] text-muted">
                            <span className="inline-block h-1.5 w-1.5 rotate-45 rounded-[1px] bg-plum-600" />
                            What&rsquo;s Covered
                        </p>
                        <ul className="flex flex-col gap-1 text-[13.5px] p-0 m-0 list-none">
                            {toc.map((t) => {
                                const isAct = active === t.id;
                                return (
                                    <li key={t.id} className="list-none p-0 m-0">
                                        <a
                                            href={"#" + t.id}
                                            onClick={(e) => scrollTo(e, t.id)}
                                            style={{
                                                textDecoration: "none",
                                                color: isAct ? "#671a6a" : "#4b3340",
                                                backgroundColor: isAct ? "#f6e3ef" : "transparent",
                                                fontWeight: isAct ? 600 : 400,
                                            }}
                                            className={
                                                "toc-link block rounded-xl px-3.5 py-2 leading-snug no-underline transition-all " +
                                                (isAct
                                                    ? "is-active bg-[#f6e3ef] font-semibold text-[#671a6a]"
                                                    : "text-[#4b3340] hover:bg-[#fbf1f7] hover:text-[#7e2081]")
                                            }
                                        >
                                            {t.label}
                                        </a>
                                    </li>
                                );
                            })}
                        </ul>
                    </nav>
                </aside>

                <main className="min-w-0">
                    <div className="rounded-2xl border border-ink/8 bg-white p-6 shadow-[0_24px_60px_-40px_rgba(42,8,32,.4)] sm:p-9 lg:p-11">
                        {children}
                    </div>

                    <div className="mt-6 rounded-xl border border-ink/8 bg-white/60 px-6 py-4 text-center">
                        <p className="text-[13px] leading-relaxed text-muted m-0">
                            This platform is designed exclusively for authorized Azad Foundation staff, trainers, and registered trainees participating in foundation programs.
                        </p>
                    </div>
                </main>
            </div>

            {/* Footer */}
            <footer className="border-t border-ink/10 bg-white">
                <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 px-5 py-6 text-center sm:flex-row sm:justify-between sm:px-8 sm:text-left">
                    <img src={logo} alt="Azad Foundation" className="h-8 sm:h-9 w-auto" />
                    <div className="flex items-center gap-4 text-[13.5px] text-muted">
                        <Link
                            to="/disclaimer"
                            style={{ textDecoration: "none" }}
                            className={"font-medium no-underline transition " + (current === "disclaimer" ? "text-plum-600 font-semibold" : "text-muted hover:text-plum-600")}
                        >
                            Disclaimer
                        </Link>
                        <span className="h-3.5 w-px bg-ink/15" />
                        <Link
                            to="/privacy-policy"
                            style={{ textDecoration: "none" }}
                            className={"font-medium no-underline transition " + (current === "privacy" ? "text-plum-600 font-semibold" : "text-muted hover:text-plum-600")}
                        >
                            Privacy Policy
                        </Link>
                    </div>
                    <p className="text-[12.5px] text-muted m-0">
                        Technology partner &middot;{" "}
                        <span className="font-semibold text-ink">Indev Consultancy Pvt. Ltd.</span>
                    </p>
                </div>
            </footer>
        </div>
    );
}

// Small helpers to keep the section markup identical across the two pages.
export function DocSection({ id, icon, heading, children }) {
    return (
        <section id={id} className="scroll-mt-24">
            <h2 className="ff-serif flex items-center gap-3 text-[22px] sm:text-[25px] font-semibold tracking-tight text-ink">
                <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white p-2 ring-1 ring-ink/8 shadow-sm">
                    <img src={icon} alt="" className="h-full w-full object-contain" />
                </span>
                {heading}
            </h2>
            {children}
        </section>
    );
}

export function DocList({ items }) {
    return (
        <ul className="doc-list mt-5 space-y-3.5 text-[14.5px] sm:text-[15px] leading-relaxed text-ink2">
            {items.map((it, i) => (
                <li key={i}>{it}</li>
            ))}
        </ul>
    );
}

export function DocHr() {
    return <hr className="my-8 sm:my-9 border-ink/8" />;
}
