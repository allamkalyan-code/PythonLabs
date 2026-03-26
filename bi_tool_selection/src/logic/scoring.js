export const TOOLS = {
    POWER_BI: 'Power BI',
    TABLEAU: 'Tableau',
    METABASE: 'Metabase',
    SUPERSET: 'Apache Superset',
};

// Questions configuration
export const QUESTIONS = [
    // Section A: Users & Ownership
    {
        id: 1,
        section: 'Section A — Users & Ownership',
        text: 'Who primarily consumes dashboards?',
        options: [
            { text: 'Executives / Leadership', scores: { [TOOLS.POWER_BI]: 3, [TOOLS.TABLEAU]: 1 } },
            { text: 'Business / Operations teams', scores: { [TOOLS.POWER_BI]: 2, [TOOLS.METABASE]: 1 } },
            { text: 'Analysts / Product teams', scores: { [TOOLS.TABLEAU]: 2, [TOOLS.METABASE]: 2 } },
            { text: 'Engineers / Data teams', scores: { [TOOLS.SUPERSET]: 3, [TOOLS.METABASE]: 1 } }
        ]
    },
    {
        id: 2,
        section: 'Section A — Users & Ownership',
        text: 'Who primarily builds dashboards?',
        options: [
            { text: 'BI / Analytics team', scores: { [TOOLS.POWER_BI]: 2, [TOOLS.TABLEAU]: 2 } },
            { text: 'Engineering / Data team', scores: { [TOOLS.SUPERSET]: 3, [TOOLS.METABASE]: 1 } },
            { text: 'Business users', scores: { [TOOLS.POWER_BI]: 2, [TOOLS.TABLEAU]: 1 } }, // Self-service
            { text: 'Mixed / unclear', scores: {} } // Neutral
        ]
    },
    // Section B: Decision Style
    {
        id: 3,
        section: 'Section B — Decision Style',
        text: 'How are decisions usually made?',
        options: [
            { text: 'Standardized KPIs reviewed regularly', scores: { [TOOLS.POWER_BI]: 3 } },
            { text: 'Exploratory, ad-hoc questions', scores: { [TOOLS.METABASE]: 3, [TOOLS.TABLEAU]: 2 } },
            { text: 'Mix of both', scores: { [TOOLS.TABLEAU]: 1, [TOOLS.POWER_BI]: 1 } }
        ]
    },
    {
        id: 4,
        section: 'Section B — Decision Style',
        text: 'Do teams ever disagree on metric definitions?',
        options: [
            { text: 'Frequently', scores: { [TOOLS.POWER_BI]: 3 } }, // Needs single source of truth/governance
            { text: 'Occasionally', scores: { [TOOLS.TABLEAU]: 1, [TOOLS.POWER_BI]: 1 } },
            { text: 'Rarely / Never', scores: { [TOOLS.METABASE]: 2, [TOOLS.SUPERSET]: 1 } } // Low governance needed
        ]
    },
    // Section C: Scale & Distribution
    {
        id: 5,
        section: 'Section C — Scale & Distribution',
        text: 'How many people will regularly view dashboards?',
        options: [
            { text: '< 20', scores: { [TOOLS.METABASE]: 2, [TOOLS.SUPERSET]: 1 } },
            { text: '20–100', scores: { [TOOLS.METABASE]: 1, [TOOLS.TABLEAU]: 1 } },
            { text: '100–500', scores: { [TOOLS.POWER_BI]: 2, [TOOLS.TABLEAU]: 2 } },
            { text: '500+', scores: { [TOOLS.POWER_BI]: 3 } }
        ]
    },
    {
        id: 6,
        section: 'Section C — Scale & Distribution',
        text: 'How are insights typically shared today?',
        options: [
            { text: 'Live dashboards', scores: { [TOOLS.POWER_BI]: 1, [TOOLS.TABLEAU]: 1 } },
            { text: 'PDFs / screenshots', scores: { [TOOLS.TABLEAU]: 2 } }, // Pixel perfect reports
            { text: 'Email / Slack updates', scores: { [TOOLS.METABASE]: 2 } }, // Pulse features
            { text: 'Meetings', scores: { [TOOLS.POWER_BI]: 1 } }
        ]
    },
    // Section D: Governance (Matrix)
    // Logic: High Gov -> PBI, Low Gov -> Metabase/Superset
    {
        id: 7,
        section: 'Section D — Governance & Control',
        text: 'How important are the following?',
        type: 'matrix',
        subQuestions: ['Metric consistency', 'Access control & security', 'Auditability / compliance'],
        options: [
            { text: 'High', scores: { [TOOLS.POWER_BI]: 3, [TOOLS.TABLEAU]: 1 } },
            { text: 'Medium', scores: { [TOOLS.TABLEAU]: 2, [TOOLS.METABASE]: 1 } },
            { text: 'Low', scores: { [TOOLS.METABASE]: 3, [TOOLS.SUPERSET]: 2 } }
        ]
    },
    // Section E: Analytics Maturity
    {
        id: 8,
        section: 'Section D — Analytics Maturity',
        text: 'Which best describes your analytics stage?',
        options: [
            { text: 'Early: ad-hoc, moving fast', scores: { [TOOLS.METABASE]: 3, [TOOLS.SUPERSET]: 1 } },
            { text: 'Growing: balancing speed & structure', scores: { [TOOLS.METABASE]: 1, [TOOLS.TABLEAU]: 2 } },
            { text: 'Mature: enterprise KPIs, governance', scores: { [TOOLS.POWER_BI]: 3, [TOOLS.TABLEAU]: 2 } }
        ]
    },
    // Section F: Culture & Constraints
    {
        id: 9,
        section: 'Section F — Culture & Constraints',
        text: 'Which best describes your culture?',
        options: [
            { text: 'Engineering-led', scores: { [TOOLS.SUPERSET]: 3, [TOOLS.METABASE]: 2 } },
            { text: 'Business-led', scores: { [TOOLS.POWER_BI]: 3, [TOOLS.TABLEAU]: 2 } },
            { text: 'Balanced', scores: { [TOOLS.TABLEAU]: 1, [TOOLS.POWER_BI]: 1 } }
        ]
    },
    {
        id: 10,
        section: 'Section F — Culture & Constraints',
        text: 'Any strong preferences or constraints?',
        options: [
            { text: 'Open-source preferred', scores: { [TOOLS.SUPERSET]: 4, [TOOLS.METABASE]: 3 } }, // Strong weight
            { text: 'Avoid vendor lock-in', scores: { [TOOLS.SUPERSET]: 3, [TOOLS.METABASE]: 3 } },
            { text: 'Existing Microsoft ecosystem', scores: { [TOOLS.POWER_BI]: 5 } }, // Very strong weight
            { text: 'None', scores: {} }
        ]
    }
];

export function calculateWinner(answers) {
    const scores = {
        [TOOLS.POWER_BI]: 0,
        [TOOLS.TABLEAU]: 0,
        [TOOLS.METABASE]: 0,
        [TOOLS.SUPERSET]: 0,
    };

    // answers is an object: { questionId: optionIndex }
    // For matrix (id 7), it might be { 7: { 0: 'High', 1: 'Medium'... } } or similar mapping.
    // Actually, to simplify, let's assume 'answers' is an object where key is question ID.
    // For single choice: value is the chosen Option Object.
    // For matrix: value is an array of Option Objects (one for each row).

    Object.entries(answers).forEach(([qId, answerData]) => {
        // Handle Matrix Question (ID 7)
        if (String(qId) === '7') {
            // answerData should be an object/array of selected options for each sub-row
            Object.values(answerData).forEach((selectedOption) => {
                if (!selectedOption) return;
                Object.entries(selectedOption.scores).forEach(([tool, score]) => {
                    scores[tool] += score;
                });
            });
        } else {
            // Single select
            if (!answerData) return;
            Object.entries(answerData.scores).forEach(([tool, score]) => {
                scores[tool] += score;
            });
        }
    });

    // Find max
    let maxScore = -1;
    let winner = null;
    const sortedTools = Object.entries(scores).sort((a, b) => b[1] - a[1]);

    const [firstTool, secondTool] = sortedTools;

    // Mixed signals check: if gap is small (e.g., < 3 points)
    const isMixed = (firstTool[1] - secondTool[1]) < 3;

    return {
        winner: firstTool[0],
        scores,
        ranking: sortedTools,
        isMixed,
        runnerUp: secondTool[0]
    };
}
