import { useState } from 'react';
import { Layers, ArrowRight, Database } from 'lucide-react';
import VendorInput from './components/VendorInput';
import AIProcessing from './components/AIProcessing';
import ReviewDashboard from './components/ReviewDashboard';

// Default Sample Data (to be moved to constants later)

const DEFAULT_VENDOR_A = [
  { "loan_id": "L001", "amount": 5000, "rate": 5.5, "sts": "Active" },
  { "loan_id": "L002", "amount": 12000, "rate": 4.2, "sts": "Closed" }
];

const DEFAULT_VENDOR_B = [
  { "acct_n": "998877", "bal": 5000.00, "int_rt": 0.055, "state": "A" },
  { "acct_n": "998866", "bal": 12000.50, "int_rt": 0.042, "state": "C" }
];


function App() {
  const [vendorAData, setVendorAData] = useState(JSON.stringify(DEFAULT_VENDOR_A, null, 2));
  const [vendorBData, setVendorBData] = useState(JSON.stringify(DEFAULT_VENDOR_B, null, 2));

  const [analysisResults, setAnalysisResults] = useState(null);
  const [appState, setAppState] = useState('INPUT'); // INPUT, PROCESSING, REVIEW, APPROVED

  const handleAnalysisComplete = (results) => {
    setAnalysisResults(results);
    setAppState('REVIEW');
  };

  return (
    <div className="min-h-screen bg-[--bg-app] text-[--text-main]">
      {/* ... (Header) ... */}
      <header className="border-b border-[--border] bg-[--bg-panel] sticky top-0 z-10">
        <div className="container h-[--header-height] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[--primary] rounded-lg">
              <Database size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">CU Data Mapper</h1>
              <p className="text-xs text-[--text-muted]">AI-Assisted Standardization Prototype</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <span className={`px-2 py-1 rounded ${appState === 'INPUT' ? 'bg-[--primary] text-white' : 'text-[--text-muted]'}`}>1. Input</span>
              <ArrowRight size={14} className="text-[--border]" />
              <span className={`px-2 py-1 rounded ${appState === 'PROCESSING' ? 'bg-[--primary] text-white' : 'text-[--text-muted]'}`}>2. Analysis</span>
              <ArrowRight size={14} className="text-[--border]" />
              <span className={`px-2 py-1 rounded ${appState === 'REVIEW' || appState === 'APPROVED' ? 'bg-[--primary] text-white' : 'text-[--text-muted]'}`}>3. Review</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-8">

        {/* Phase 1: Input Section */}
        {appState === 'INPUT' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-semibold mb-2">Vendor Data Ingestion</h2>
                <p className="text-[--text-muted]">Paste raw JSON samples from your vendor feeds below. The AI will analyze schema structure and content.</p>
              </div>
              <button
                onClick={() => setAppState('PROCESSING')}
                className="btn btn-primary px-6 py-3 text-lg shadow-lg shadow-indigo-500/20"
              >
                <Layers size={20} />
                Run AI Schema Analysis
              </button>
            </div>

            <div className="grid-2">
              <VendorInput
                label="Vendor A (e.g., MeridianLink)"
                value={vendorAData}
                onChange={setVendorAData}
                color="border-l-4 border-l-blue-500"
              />
              <VendorInput
                label="Vendor B (e.g., Symitar)"
                value={vendorBData}
                onChange={setVendorBData}
                color="border-l-4 border-l-cyan-500"
              />
            </div>
          </div>
        )}

        {/* Phase 2: AI Processing */}
        {appState === 'PROCESSING' && (
          <AIProcessing
            vendorAData={vendorAData}
            vendorBData={vendorBData}
            onComplete={handleAnalysisComplete}
          />
        )}


        {/* Phase 3 & 4: Review Dashboard */}
        {(appState === 'REVIEW' || appState === 'APPROVED') && analysisResults && (
          <ReviewDashboard
            analysisResults={analysisResults}
            onReset={() => setAppState('INPUT')}
          />
        )}
      </main>
    </div>
  );
}

export default App;

