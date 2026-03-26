import { calculateWinner, TOOLS, QUESTIONS } from './scoring.js';

// Helper to simulate answers based on text matching
// answers structure: { questionId: optionIndex (Single) OR { subIndex: option } (Matrix) }
// Wait, my scoring logic expects { questionId: OptionObject } or { questionId: { subIndex: OptionObject } }
// I need to reconstruct the Option Objects from the QUESTIONS array.

function findOption(qId, text) {
    const q = QUESTIONS.find(q => q.id === qId);
    if (!q) throw new Error(`Question ${qId} not found`);
    return q.options.find(o => o.text.includes(text));
}

function runTest(name, answersMap, expectedWinner, expectedMixed = false) {
    console.log(`Running Test: ${name}`);

    const answers = {};

    Object.entries(answersMap).forEach(([qId, val]) => {
        const q = QUESTIONS.find(q => q.id == qId);
        if (q.type === 'matrix') {
            // value is array of texts for each subquestion
            const subAnswers = {};
            val.forEach((text, subIdx) => {
                subAnswers[subIdx] = findOption(parseInt(qId), text);
            });
            answers[qId] = subAnswers;
        } else {
            answers[qId] = findOption(parseInt(qId), val);
        }
    });

    const result = calculateWinner(answers);

    const winnerMatch = result.winner === expectedWinner;
    const mixedMatch = result.isMixed === expectedMixed;

    if (winnerMatch && mixedMatch) {
        console.log(`✅ PASS. Winner: ${result.winner}. Mixed: ${result.isMixed}`);
    } else {
        console.error(`❌ FAIL.`);
        console.error(`   Expected Winner: ${expectedWinner}, Got: ${result.winner}`);
        console.error(`   Expected Mixed: ${expectedMixed}, Got: ${result.isMixed}`);
        console.log('   Scores:', result.scores);
    }
    console.log('---');
}

// 1. Power BI Strong Indicators
// Execs (Q1), Standardized KPIs (Q3), 500+ (Q5), High Gov (Q7), Mature (Q8), MS Eco (Q10)
runTest('Power BI Strong', {
    1: 'Executives',
    3: 'Standardized KPIs',
    5: '500+',
    7: ['High', 'High', 'High'], // Matrix
    8: 'Mature',
    10: 'Existing Microsoft'
}, TOOLS.POWER_BI);

// 2. Tableau Strong Indicators
// Analysts (Q1), Visually (Q6 logic? Q2 builds? prompt says: Analysts + leadership consumption, Insight storytelling)
// Let's use: Analysts (Q1), Mixed/Unclear builds or BI Team (Q2), Exploratory (Q3), 100-500 (Q5), Moderate Gov (Q7), Mature (Q8)
runTest('Tableau Strong', {
    1: 'Analysts',
    3: 'Exploratory', // actually Tablue is Exploratory/Mix
    6: 'PDFs', // visual
    7: ['Medium', 'Medium', 'Medium'],
    8: 'Growing', // or Mature
}, TOOLS.TABLEAU); // Note: Tableau logic in scoring might need adjustment if this fails, let's see.

// 3. Metabase Strong Indicators
runTest('Metabase Strong', {
    1: 'Engineers', // or Product
    3: 'Exploratory',
    5: '< 20',
    7: ['Low', 'Low', 'Low'],
    8: 'Early',
    9: 'Engineering-led'
}, TOOLS.METABASE);

// 4. Superset Strong Indicators
runTest('Superset Strong', {
    1: 'Engineers',
    2: 'Engineering',
    9: 'Engineering-led',
    10: 'Open-source preferred',
    7: ['Low', 'Low', 'Low']
}, TOOLS.SUPERSET);

// 5. Mixed Signals
// Engineering + Business critical. Speed now, Governance later.
runTest('Mixed Signals', {
    1: 'Business', // PBI +2
    2: 'Engineering', // Superset +3
    3: 'Exploratory', // Metabase +3
    9: 'Balanced', // Tab/PBI
    7: ['Medium', 'Medium', 'Medium']
}, TOOLS.TABLEAU, true); // Likely messy, checking for Mixed=true

