import { useState } from 'react';
import QuizWizard from './components/QuizWizard';
import ResultsView from './components/ResultsView';
import './App.css';

function App() {
  const [appState, setAppState] = useState('welcome'); // welcome, quiz, result
  const [results, setResults] = useState(null);

  const handleStart = () => {
    setAppState('quiz');
  };

  const handleComplete = (resultData) => {
    setResults(resultData);
    setAppState('result');
  };

  const handleRestart = () => {
    setResults(null);
    setAppState('welcome');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>BI Tool Selector</h1>
      </header>

      <main className="app-main">
        {appState === 'welcome' && (
          <div className="welcome-card glass-panel">
            <h2>Find Your Perfect BI Match</h2>
            <p>Answer a few questions about your team, data, and culture to get a tailored recommendation.</p>
            <button className="btn-primary" onClick={handleStart}>Start Assessment</button>
          </div>
        )}

        {appState === 'quiz' && (
          <QuizWizard onComplete={handleComplete} />
        )}

        {appState === 'result' && results && (
          <ResultsView resultData={results} onRestart={handleRestart} />
        )}
      </main>

      <footer className="app-footer">
        <p>AI-Powered BI Tool Recommendations</p>
      </footer>
    </div>
  );
}

export default App;
