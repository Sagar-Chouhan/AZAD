import DocLayout, { DocSection, DocList, DocHr } from "./DocLayout";

const ICON = (id) => `https://cdn-icons-png.flaticon.com/512/${id}.png`;

const TOC = [
    { id: "general", label: "General Disclaimer" },
    { id: "liability", label: "Limitation of Liability" },
    { id: "access", label: "Platform Access" },
    { id: "updates", label: "Policy Updates" },
    { id: "contact", label: "Contact Information" },
];

const P1 = "mt-3 text-[15.5px] leading-relaxed text-ink2";

export default function Disclaimer() {
    return (
        <DocLayout
            badge="Terms of Use"
            title="Disclaimer"
            intro="The Azad Foundation LMS is an internal educational platform exclusively designed for registered trainees, trainers, and authorized staff members."
            toc={TOC}
            current="disclaimer"
        >
            <DocSection id="general" icon={ICON("9746/9746243")} heading="General Disclaimer">
                <p className={P1}>
                    Please be aware of the following terms governing the use of educational content on this platform:
                </p>
                <DocList
                    items={[
                        "All educational content provided on the LMS is intended for training and knowledge-building purposes only.",
                        "Content must not be copied, reproduced, distributed, or used for commercial purposes without prior written approval from Azad Foundation.",
                        "While efforts are made to ensure accuracy and relevance of materials, Azad Foundation does not guarantee that all content is error-free or applicable to every learner’s personal context.",
                        "Completion of courses or certifications through the LMS does not constitute formal employment or a legally binding qualification unless explicitly stated by Azad Foundation.",
                    ]}
                />
            </DocSection>

            <DocHr />

            <DocSection id="liability" icon={ICON("2592/2592317")} heading="Limitation of Liability">
                <p className={P1}>Azad Foundation shall not be liable for:</p>
                <DocList
                    items={[
                        "Technical issues, access interruptions, or data loss due to unforeseen circumstances.",
                        "User misuse of the platform or non-compliance with platform guidelines.",
                        "Any indirect or incidental damages resulting from LMS use or content interpretation.",
                    ]}
                />
            </DocSection>

            <DocHr />

            <DocSection id="access" icon={ICON("807/807241")} heading="Platform Access">
                <p className={P1}>Azad Foundation reserves the right to:</p>
                <DocList
                    items={[
                        "Modify or discontinue any content or service on the LMS without prior notice.",
                        "Restrict, suspend, or terminate access for any user violating platform policies or guidelines.",
                    ]}
                />
            </DocSection>

            <DocHr />

            <DocSection id="updates" icon={ICON("10695/10695869")} heading="Policy Updates">
                <p className={P1}>
                    This policy may be updated periodically to reflect operational, legal, or technical changes. Updated versions will be posted directly on the LMS platform.
                </p>
                <p className={P1}>Continued use of the LMS signifies acceptance of the revised policy.</p>
            </DocSection>

            <DocHr />

            <DocSection id="contact" icon={ICON("8756/8756542")} heading="Contact Information">
                <p className={P1}>
                    For questions related to this Privacy Policy or Disclaimer, please reach out to us:
                </p>

                <div className="relative mt-6 overflow-hidden rounded-2xl bg-plum-800 shadow-[0_28px_70px_-40px_rgba(88,16,63,.85)]">
                    <div className="pointer-events-none absolute -right-10 -top-12 h-44 w-44 rotate-45 rounded-[2.5rem] bg-white/5" />
                    <div className="pointer-events-none absolute -left-8 -bottom-12 h-36 w-36 rounded-full bg-white/5" />
                    <div className="relative flex flex-col gap-5 p-7 sm:flex-row sm:items-center sm:justify-between sm:p-8">
                        <div>
                            <p className="ff-serif text-[21px] font-semibold leading-snug text-white">
                                Have questions? We&rsquo;re here to help.
                            </p>
                        </div>
                        <a
                            href="mailto:support@azadfoundation.com"
                            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-5 py-3.5 text-[14.5px] font-semibold text-plum-700 shadow-sm transition hover:bg-plum-50"
                        >
                            <i className="fi fi-rr-envelope text-[16px]" />
                            support@azadfoundation.com
                        </a>
                    </div>
                </div>
            </DocSection>
        </DocLayout>
    );
}
