import DocLayout, { DocSection, DocList, DocHr } from "./DocLayout";

const ICON = (id) => `https://cdn-icons-png.flaticon.com/512/${id}.png`;

const TOC = [
    { id: "info-collect", label: "Information We Collect" },
    { id: "purpose", label: "Purpose of Data Collection" },
    { id: "sharing", label: "Data Sharing" },
    { id: "security", label: "Data Security" },
    { id: "responsibilities", label: "User Responsibilities" },
    { id: "retention", label: "Data Retention" },
    { id: "rights", label: "User Rights" },
];

const P1 = "mt-3 text-[15.5px] leading-relaxed text-ink2";
const P2 = "mt-4 text-[15.5px] leading-relaxed text-ink2";

export default function PrivacyPolicy() {
    return (
        <DocLayout
            badge="Your Data, Our Responsibility"
            title="Privacy Policy"
            intro="Azad Foundation respects the privacy of all users of its Learning Management System. This policy outlines how your information is collected, used, and protected."
            toc={TOC}
            current="privacy"
        >
            <DocSection id="info-collect" icon={ICON("3270/3270865")} heading="Information We Collect">
                <p className={P1}>
                    We collect the following information solely for training, learning management, and program monitoring purposes:
                </p>
                <DocList
                    items={[
                        "Personal information including name, contact details, age group, and location",
                        "Login credentials (username and password)",
                        "Training records such as course enrollment, progress tracking, assessments, attendance, and certification details",
                        "Usage data including device type, login activity, and content engagement for internal analytics",
                    ]}
                />
                <p className={P2}>No financial or commercially sensitive personal information is collected through the LMS.</p>
            </DocSection>

            <DocHr />

            <DocSection id="purpose" icon={ICON("2775/2775034")} heading="Purpose of Data Collection">
                <p className={P1}>Information is collected and used for:</p>
                <DocList
                    items={[
                        "User authentication and access management",
                        "Delivering learning content and tracking progress",
                        "Program monitoring and evaluation",
                        "Issuing training certificates",
                        "Internal reporting to measure training outcomes and improve content delivery",
                        "System security and troubleshooting",
                    ]}
                />
                <p className={P2}>
                    Personal data is strictly used for educational and administrative purposes related to Azad Foundation programs.
                </p>
            </DocSection>

            <DocHr />

            <DocSection id="sharing" icon={ICON("4170/4170568")} heading="Data Sharing">
                <p className={P1}>User information is:</p>
                <DocList
                    items={[
                        "Not sold, traded, or shared with any external third parties for marketing or commercial purposes",
                        "Shared only on a need-to-know basis with authorized Azad Foundation staff or contracted service providers involved in LMS hosting, maintenance, or analytics strictly for operational support",
                    ]}
                />
                <p className={P2}>
                    All vendors and partners are contractually obligated to maintain confidentiality and data protection standards.
                </p>
            </DocSection>

            <DocHr />

            <DocSection id="security" icon={ICON("2592/2592317")} heading="Data Security">
                <p className={P1}>
                    Appropriate technical and organizational safeguards are implemented to protect user information, including:
                </p>
                <DocList
                    items={[
                        "Secure authentication and role-based access",
                        "Encrypted data storage and secure hosting infrastructure",
                        "Periodic security audits and system monitoring",
                        "Regular backups to prevent data loss",
                    ]}
                />
                <p className={P2}>Only authorized personnel have access to LMS data.</p>
            </DocSection>

            <DocHr />

            <DocSection id="responsibilities" icon={ICON("7246/7246748")} heading="User Responsibilities">
                <p className={P1}>All users are responsible for:</p>
                <DocList
                    items={[
                        "Maintaining confidentiality of login credentials",
                        "Ensuring information provided is accurate and up to date",
                        "Using the LMS solely for lawful educational purposes",
                        "Respecting the privacy and dignity of other learners and staff",
                    ]}
                />
                <p className={P2}>Users must not share accounts or misuse platform content.</p>
            </DocSection>

            <DocHr />

            <DocSection id="retention" icon={ICON("2906/2906274")} heading="Data Retention">
                <p className={P1}>
                    Personal data is retained only for as long as necessary to fulfill program objectives and reporting requirements or as mandated by law. Upon course completion or exit from the program, data may be archived or anonymized for internal records and impact reporting.
                </p>
            </DocSection>

            <DocHr />

            <DocSection id="rights" icon={ICON("10823/10823068")} heading="User Rights">
                <p className={P1}>Users may:</p>
                <DocList
                    items={[
                        "Request access to their personal data",
                        "Request correction of inaccurate records",
                        "Raise concerns regarding privacy or data use",
                    ]}
                />
                <p className={P2}>
                    All requests should be addressed to Azad Foundation through the official program contact channels.
                </p>
            </DocSection>
        </DocLayout>
    );
}
