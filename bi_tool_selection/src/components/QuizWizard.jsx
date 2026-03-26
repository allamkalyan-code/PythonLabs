import React, { useState } from 'react';
import QuestionCard from './QuestionCard';
import { QUESTIONS, calculateWinner } from '../logic/scoring';
import './QuizWizard.css';

const QuizWizard = ({ onComplete }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [answers, setAnswers] = useState({}); // { [questionId]: answerValue }

    const currentQuestion = QUESTIONS[currentIndex];
    const isLastQuestion = currentIndex === QUESTIONS.length - 1;

    // Calculate progress
    const progress = ((currentIndex + 1) / QUESTIONS.length) * 100;

    const handleAnswer = (answerValue) => {
        setAnswers(prev => ({
            ...prev,
            [currentQuestion.id]: answerValue
        }));
    };

    const handleNext = () => {
        if (isLastQuestion) {
            // Logic complete
            const result = calculateWinner(answers);
            onComplete(result);
        } else {
            setCurrentIndex(prev => prev + 1);
        }
    };

    const handleBack = () => {
        if (currentIndex > 0) {
            setCurrentIndex(prev => prev - 1);
        }
    };

    // Check if current question is answered validly to enable Next
    const isCurrentAnswered = () => {
        const ans = answers[currentQuestion.id];
        if (currentQuestion.type === 'matrix') {
            // Need all subquestions answered? Or at least one? Strict mode: All.
            // Current Matrix implementation: ans is { 0: opt, 1: opt, 2: opt }
            if (!ans) return false;
            const answeredCount = Object.keys(ans).length;
            return answeredCount === currentQuestion.subQuestions.length;
        }
        return !!ans;
    };

    return (
        <div className="quiz-container">
            <div className="progress-bar-container">
                <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>

            <QuestionCard
                key={currentQuestion.id}
                question={currentQuestion}
                currentAnswer={answers[currentQuestion.id]}
                onAnswer={handleAnswer}
            />

            <div className="quiz-controls">
                <button
                    className="btn-ghost"
                    onClick={handleBack}
                    disabled={currentIndex === 0}
                    style={{ visibility: currentIndex === 0 ? 'hidden' : 'visible' }}
                >
                    Back
                </button>
                <button
                    className="btn-primary"
                    onClick={handleNext}
                    disabled={!isCurrentAnswered()}
                >
                    {isLastQuestion ? 'Show Results' : 'Next Question'}
                </button>
            </div>
        </div>
    );
};

export default QuizWizard;
