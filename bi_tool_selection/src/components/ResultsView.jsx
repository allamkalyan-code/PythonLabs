import React from 'react';
import { TOOLS } from '../logic/scoring';
import './ResultsView.css';

const TOOL_DETAILS = {
    [TOOLS.POWER_BI]: {
        description: 'Microsoft Power BI is best for organizations that need deep integration with the MS ecosystem, robust governance, and wide distribution.',
        quote: '“We need one version of truth across the organization.”',
        color: '#F2C811' // Power BI Yellow/Gold
    },
    [TOOLS.TABLEAU]: {
        description: 'Tableau Key is the gold standard for visual analytics and data storytelling. Ideal for analysts who need flexibility and beauty.',
        quote: '“We want to explore and explain insights visually.”',
        color: '#E97627' // Tableau Orange? Or Blue. Let's use Blue 
    },
    [TOOLS.METABASE]: {
        description: 'Metabase is fantastic for self-service, speed, and democratizing data. Perfect for engineering/product teams and startups.',
        quote: '“We need fast answers, not heavy reporting.”',
        color: '#509EE3' // Metabase Blue
    },
    [TOOLS.SUPERSET]: {
        description: 'Apache Superset is a powerful open-source platform. Best for data-mature organizations who want control and can manage complexity.',
        quote: '“Analytics is part of our data platform, not a business tool.”',
        color: '#20A7C9' // Superset Teal
    }
};

// Override Tableau color to official-ish blue
TOOL_DETAILS[TOOLS.TABLEAU].color = '#E97627'; // Actually their orange is recognizable, but blue is primary. Using Orange for contrast.

const ResultsView = ({ resultData, onRestart }) => {
    const { winner, ranking, isMixed, runnerUp } = resultData;
    const winnerDetails = TOOL_DETAILS[winner];

    return (
        <div className="results-container glass-panel fade-in">
            <div className="results-header">
                <span className="results-label">Our Recommendation</span>
                <h2 className="winner-name" style={{ color: winnerDetails.color }}>{winner}</h2>
            </div>

            <div className="quote-box">
                <p>{winnerDetails.quote}</p>
            </div>

            <p className="winner-description">{winnerDetails.description}</p>

            {isMixed && (
                <div className="mixed-signals-card">
                    <div className="mixed-header">
                        <span className="icon">⚠️</span>
                        <h3>Mixed Signals Detected</h3>
                    </div>
                    <p>
                        Your answers suggest a split between <strong>{winner}</strong> and <strong>{runnerUp}</strong>.
                    </p>
                    <div className="consulting-tip">
                        <strong>Consulting Recommendation:</strong>
                        <p>“Design the data & semantic layer so BI tools can evolve.”</p>
                        <p className="example-text">e.g., {runnerUp} now → {winner} later.</p>
                    </div>
                </div>
            )}

            <div className="scores-breakdown">
                <h4>Score Breakdown</h4>
                {ranking.map(([tool, score]) => (
                    <div key={tool} className="score-row">
                        <span className="tool-name">{tool}</span>
                        <div className="score-bar-bg">
                            <div
                                className="score-bar-fill"
                                style={{ width: `${(score / ranking[0][1]) * 100}%`, backgroundColor: TOOL_DETAILS[tool].color || '#ccc' }}
                            ></div>
                        </div>
                        <span className="score-val">{score}</span>
                    </div>
                ))}
            </div>

            <button className="btn-primary restart-btn" onClick={onRestart}>Start Over</button>
        </div>
    );
};

export default ResultsView;
