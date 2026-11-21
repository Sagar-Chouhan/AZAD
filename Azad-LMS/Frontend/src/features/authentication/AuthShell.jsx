import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import slide1 from "@/assets/images/slide-banner-1.webp";
import slide2 from "@/assets/images/slide-banner-2.webp";
import slide3 from "@/assets/images/slide-banner-3.webp";

// The three hero images on the left panel. slide3 doubles as the mobile hero.
const SLIDES = [
    { src: slide1, pos: "50% 40%" },
    { src: slide2, pos: "50% 45%" },
    { src: slide3, pos: "50% 42%" },
];

const INTERVAL = 5500;

// Shared sign-in / forgot-password shell: image slider on the left (lg+),
// a tinted panel on the right that holds the mobile hero + the card, and the
// footer. `children` is the white card for the specific page.
export default function AuthShell({ rightBgClass, children }) {
    const [cur, setCur] = useState(0);
    const fitRef = useRef(null);
    const timerRef = useRef(null);
    const reduce =
        typeof window !== "undefined" &&
        window.matchMedia("(prefers-reduced-motion:reduce)").matches;

    const pause = () => {
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
    };
    const restart = () => {
        pause();
        if (!reduce) {
            timerRef.current = setInterval(
                () => setCur((c) => (c + 1) % SLIDES.length),
                INTERVAL
            );
        }
    };

    useEffect(() => {
        restart();
        return pause;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Scale-to-fit: keep the whole card visible at any zoom/height (lg+ only).
    useLayoutEffect(() => {
        const fitwrap = fitRef.current;
        if (!fitwrap) return undefined;
        const fit = () => {
            fitwrap.style.transform = "";
            if (window.innerWidth < 1024) return;
            const sec = fitwrap.parentElement;
            if (!sec) return;
            const cs = getComputedStyle(sec);
            const avail =
                sec.clientHeight -
                parseFloat(cs.paddingTop) -
                parseFloat(cs.paddingBottom) -
                6;
            const need = fitwrap.offsetHeight;
            if (need > avail && need > 0) {
                fitwrap.style.transform =
                    "scale(" + Math.max(avail / need, 0.9).toFixed(4) + ")";
            }
        };
        window.addEventListener("resize", fit);
        window.addEventListener("load", fit);
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(fit);
        }
        const t = setTimeout(fit, 80);
        fit();
        return () => {
            window.removeEventListener("resize", fit);
            window.removeEventListener("load", fit);
            clearTimeout(t);
        };
    }, []);

    return (
        <div className="auth-page h-screen w-full overflow-hidden lg:flex">
            {/* LEFT · 60% · slider */}
            <section
                className="relative hidden lg:block lg:w-[60%] h-full overflow-hidden bg-plum-900"
                aria-label="Azad Foundation in pictures"
                onMouseEnter={pause}
                onMouseLeave={restart}
            >
                <div className="absolute inset-0">
                    {SLIDES.map((s, i) => (
                        <div
                            key={i}
                            className={"slide absolute inset-0" + (i === cur ? " active" : "")}
                        >
                            <img
                                src={s.src}
                                alt="Azad Foundation - Women with Wheels"
                                className="absolute inset-0 h-full w-full object-cover"
                                style={{ objectPosition: s.pos }}
                            />
                        </div>
                    ))}
                </div>

                <div
                    className="pointer-events-none absolute inset-x-0 bottom-0 h-3/5"
                    style={{
                        background:
                            "linear-gradient(to top, rgba(24,5,17,.86) 0%, rgba(24,5,17,.46) 40%, rgba(24,5,17,0) 100%)",
                    }}
                />
                <div className="absolute left-12 xl:left-16 bottom-8 xl:bottom-10 max-w-lg">
                    <span
                        className="inline-flex items-center rounded-full px-3.5 py-1.5 text-[11.5px] font-bold uppercase tracking-[0.2em] text-white shadow-sm"
                        style={{ background: "#7e2081" }}
                    >
                        Learning Platform
                    </span>
                    <h2 className="ff-serif mt-3.5 text-white text-[42px] xl:text-[50px] font-medium leading-[1.04] tracking-tight [text-wrap:balance]">
                        Women with Wheels
                    </h2>
                    <p className="mt-2.5 max-w-md text-[16px] xl:text-[17px] leading-relaxed text-white/85">
                        Manage training, batches and trainee progress across every centre from one dashboard.
                    </p>
                </div>
                <div className="absolute bottom-10 xl:bottom-12 right-12 xl:right-16">
                    <div className="flex items-center gap-2.5">
                        {SLIDES.map((_, i) => (
                            <button
                                key={i}
                                type="button"
                                aria-label={"Go to image " + (i + 1)}
                                onClick={() => {
                                    setCur(i);
                                    restart();
                                }}
                                className={
                                    "dot h-2.5 rounded-full transition-all shadow-[0_1px_3px_rgba(0,0,0,.4)] " +
                                    (i === cur ? "w-8 bg-white" : "w-2.5 bg-white/60 hover:bg-white/80")
                                }
                            />
                        ))}
                    </div>
                </div>
            </section>

            {/* RIGHT · 40% */}
            <section
                className={
                    "flex flex-col h-full w-full lg:w-[40%] overflow-y-auto lg:overflow-hidden px-6 sm:px-10 " +
                    rightBgClass
                }
                style={{
                    paddingTop: "1rem",
                    paddingBottom: "1rem",
                    paddingLeft: "max(1.5rem,env(safe-area-inset-left,0px))",
                    paddingRight: "max(1.5rem,env(safe-area-inset-right,0px))",
                }}
            >
                <div className="flex w-full flex-1 items-center justify-center min-h-0">
                    <div
                        ref={fitRef}
                        className="w-full max-w-[452px] mx-auto my-5 lg:my-0"
                        style={{ transformOrigin: "center center" }}
                    >
                        {/* mobile hero */}
                        <div className="lg:hidden relative mb-8 h-40 overflow-hidden rounded-2xl bg-plum-900">
                            <img
                                src={slide3}
                                alt=""
                                className="absolute inset-0 h-full w-full object-cover"
                                style={{ objectPosition: "50% 48%" }}
                            />
                            <div className="absolute inset-0" style={{ background: "rgba(26,5,18,.34)" }} />
                            <div className="absolute inset-0 flex items-end p-5">
                                <h2
                                    className="ff-serif text-white text-[21px] font-medium leading-tight"
                                    style={{ textShadow: "0 2px 12px rgba(0,0,0,.55)" }}
                                >
                                    Livelihoods with <span className="italic">dignity</span> for women
                                </h2>
                            </div>
                        </div>

                        {children}
                    </div>
                </div>

                <footer className="mt-auto shrink-0 pt-4 pb-2 text-center text-[12px] text-muted">
                    <div className="flex items-center justify-center gap-4">
                        <Link to="/disclaimer" className="font-medium hover:text-plum-600">
                            Disclaimer
                        </Link>
                        <span className="h-3.5 w-px bg-ink/15" />
                        <Link to="/privacy-policy" className="font-medium hover:text-plum-600">
                            Privacy Policy
                        </Link>
                    </div>
                    <p className="mt-0.5">
                        Technology partner &middot;{" "}
                        <span className="font-semibold text-ink">Indev Consultancy Pvt. Ltd.</span>
                    </p>
                </footer>
            </section>
        </div>
    );
}

