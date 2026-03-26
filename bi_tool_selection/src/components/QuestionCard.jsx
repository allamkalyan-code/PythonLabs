import React from 'react';
import './QuestionCard.css';

const QuestionCard = ({ question, currentAnswer, onAnswer }) => {
    const isMatrix = question.type === 'matrix';

    const handleSingleSelect = (option, index) => {
        onAnswer(option);
    };

    const handleMatrixSelect = (subIndex, option, optIndex) => {
        // currentAnswer for matrix is { subIndex: optionObject }
        const newAnswer = { ...(currentAnswer || {}) };
        newAnswer[subIndex] = option;
        onAnswer(newAnswer);
        // Note: Parent needs to know if this replaces the whole answer object or updates it.
        // We'll assume the parent passes the accumulated object for this question ID.
    };

    return (
        <div className="question-card glass-panel fade-in">
            <div className="question-header">
                <span className="question-section">{question.section}</span>
                <h3 className="question-text">{question.text}</h3>
            </div>

            <div className="options-container">
                {!isMatrix ? (
                    <div className="single-select-options">
                        {question.options.map((opt, idx) => {
                            const isSelected = currentAnswer && currentAnswer.text === opt.text;
                            return (
                                <button
                                    key={idx}
                                    className={`option-btn ${isSelected ? 'selected' : ''}`}
                                    onClick={() => handleSingleSelect(opt, idx)}
                                >
                                    <span className="option-indicator"></span>
                                    {opt.text}
                                </button>
                            );
                        })}
                    </div>
                ) : (
                    <div className="matrix-options">
                        <div className="matrix-header">
                            <div></div>
                            {question.options.map((opt, i) => (
                                <div key={i} className="matrix-col-header">{opt.text}</div>
                            ))}
                        </div>
                        {question.subQuestions.map((subQ, subIdx) => (
                            <div key={subIdx} className="matrix-row">
                                <div className="matrix-row-label">{subQ}</div>
                                {question.options.map((opt, optIdx) => {
                                    const isSelected = currentAnswer && currentAnswer[subIdx] && currentAnswer[subIdx].text === opt.text;
                                    return (
                                        <div key={optIdx} className="matrix-cell">
                                            <button
                                                className={`matrix-radio ${isSelected ? 'selected' : ''}`}
                                                onClick={() => handleMatrixSelect(subIdx, opt, optIdx)}
                                            >
                                                <div className="radio-dot"></div>
                                            </button>
                                        </div>
                                    );
                                })}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default QuestionCard;
