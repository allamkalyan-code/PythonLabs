import React, { useEffect, useState } from 'react';
import { Bot, CheckCircle, AlertTriangle, ArrowRight, Activity, Database } from 'lucide-react';
import { detectSchema, suggestMapping, detectDrift } from '../utils/mockAgents';

const AIProcessing = ({ vendorAData, vendorBData, onComplete }) => {
    const [step, setStep] = useState(0); // 0: Start, 1: Schema Done, 2: Mapping Done, 3: Drift Done
    const [agentStatus, setAgentStatus] = useState('IDLE'); // IDLE, RUNNING
    const [results, setResults] = useState({ vendorA: [], vendorB: [] });

    // Helper to simulate delay
    const wait = (ms) => new Promise(r => setTimeout(r, ms));

    const runAgent1_Schema = async () => {
        setAgentStatus('RUNNING');
        await wait(1500);

        let schemaA = [];
        let schemaB = [];
        try {
            schemaA = detectSchema(JSON.parse(vendorAData), 'Vendor A');
            schemaB = detectSchema(JSON.parse(vendorBData), 'Vendor B');
        } catch (e) { console.error("Invalid JSON", e); }

        setResults(prev => ({ ...prev, schemaA, schemaB }));
        setStep(1);
        setAgentStatus('IDLE');
    };

    const runAgent2_Mapping = async () => {
        setAgentStatus('RUNNING');
        await wait(1500);

        const mapA = suggestMapping(results.schemaA);
        const mapB = suggestMapping(results.schemaB);

        setResults(prev => ({ ...prev, mapA, mapB }));
        setStep(2);
        setAgentStatus('IDLE');
    };

    const runAgent3_Drift = async () => {
        setAgentStatus('RUNNING');
        await wait(1500);

        const driftA = detectDrift(results.mapA);
        const driftB = detectDrift(results.mapB);

        setResults(prev => ({ ...prev, driftA, driftB }));
        setStep(3);
        setAgentStatus('IDLE');
    };

    const ConfidenceBadge = ({ score }) => {
        let color = 'bg-red-500/20 text-red-400';
        if (score > 0.9) color = 'bg-emerald-500/20 text-emerald-400';
        else if (score > 0.7) color = 'bg-amber-500/20 text-amber-400';
        return (
            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${color}`}>
                {(score * 100).toFixed(0)}%
            </span>
        );
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-12">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold flex items-center gap-3">
                    <Bot className="text-[--primary]" size={32} />
                    AI Analysis Operations
                </h2>

                {step === 3 && (
                    <button
                        onClick={() => onComplete(results)}
                        className="btn btn-primary shadow-lg shadow-indigo-500/50 animate-pulse"
                    >
                        Proceed to Human Review <ArrowRight size={18} />
                    </button>
                )}
            </div>

            {/* Agent 1: Schema Detection */}
            <div className="card border-l-4 border-l-blue-500">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <Database size={20} className="text-blue-400" />
                        Agent 1: Schema Detection
                    </h3>
                    {step === 0 && agentStatus === 'IDLE' && (
                        <button onClick={runAgent1_Schema} className="btn bg-blue-600 hover:bg-blue-500 text-white btn-sm">
                            Run Agent 1
                        </button>
                    )}
                    {step === 0 && agentStatus === 'RUNNING' && <Activity className="animate-spin text-blue-400" />}
                    {step >= 1 && <CheckCircle className="text-emerald-500" size={20} />}
                </div>

                {step >= 1 && (
                    <div className="grid grid-cols-2 gap-8 text-sm animate-in slide-in-from-top-4 fade-in duration-500">
                        <div>
                            <h4 className="font-semibold text-[--text-muted] mb-2 uppercase text-xs">Vendor A Detected Schema</h4>
                            <div className="bg-[--bg-app] rounded p-2 space-y-2">
                                {results.schemaA?.map((field, i) => (
                                    <div key={i} className="p-3 bg-[--bg-panel] rounded border border-[--border] text-base">
                                        <span className="font-mono text-blue-300 font-medium">{field.column}</span>
                                        <span className="text-[--text-muted] mx-2">-</span>
                                        <span className="text-[--text-main]">{field.inferred_semantic}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div>
                            <h4 className="font-semibold text-[--text-muted] mb-2 uppercase text-xs">Vendor B Detected Schema</h4>
                            <div className="bg-[--bg-app] rounded p-2 space-y-2">
                                {results.schemaB?.map((field, i) => (
                                    <div key={i} className="p-3 bg-[--bg-panel] rounded border border-[--border] text-base">
                                        <span className="font-mono text-cyan-300 font-medium">{field.column}</span>
                                        <span className="text-[--text-muted] mx-2">-</span>
                                        <span className="text-[--text-main]">{field.inferred_semantic}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Agent 2: Mapping Suggestions */}
            <div className={`transition-all duration-500 ${step >= 1 ? 'opacity-100' : 'opacity-40 grayscale'}`}>
                <div className="card border-l-4 border-l-purple-500">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <Activity size={20} className="text-purple-400" />
                            Agent 2: Mapping Suggestions
                        </h3>
                        {step === 1 && agentStatus === 'IDLE' && (
                            <button onClick={runAgent2_Mapping} className="btn bg-purple-600 hover:bg-purple-500 text-white btn-sm">
                                Run Agent 2
                            </button>
                        )}
                        {step === 1 && agentStatus === 'RUNNING' && <Activity className="animate-spin text-purple-400" />}
                        {step >= 2 && <CheckCircle className="text-emerald-500" size={20} />}
                    </div>

                    {step >= 2 && (
                        <div className="overflow-x-auto animate-in slide-in-from-top-4 fade-in duration-500">
                            <table className="w-full text-left text-sm border-separate border-spacing-y-2">
                                <thead>
                                    <tr className="text-[--text-muted] border-b border-[--border]">
                                        <th className="pb-3 pl-4">Source Field</th>
                                        <th className="pb-3 px-4">Suggested Canonical Field</th>
                                        <th className="pb-3">Confidence Score</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[--border]">
                                    {[...(results.mapA || []), ...(results.mapB || [])].map((m, i) => (
                                        <tr key={i} className="group hover:bg-[--bg-app] transition-colors bg-[--bg-panel] rounded border border-[--border]">
                                            <td className="py-3 pl-4 font-mono text-[--text-main] pr-6">
                                                <span className="opacity-50 mr-2">{m.vendor}.</span>
                                                <span className="font-bold">{m.column}</span>
                                            </td>
                                            <td className="py-3 px-4 font-mono text-[--primary] pr-6">{m.suggested_canonical || <span className="text-[--text-muted] italic">No Match</span>}</td>
                                            <td className="py-3"><ConfidenceBadge score={m.confidence} /></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Agent 3: Schema Drift / Canonical */}
            <div className={`transition-all duration-500 ${step >= 2 ? 'opacity-100' : 'opacity-40 grayscale'}`}>
                <div className="card border-l-4 border-l-orange-500">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <AlertTriangle size={20} className="text-orange-400" />
                            Agent 3: Canonical Schema & Drift
                        </h3>
                        {step === 2 && agentStatus === 'IDLE' && (
                            <button onClick={runAgent3_Drift} className="btn bg-orange-600 hover:bg-orange-500 text-white btn-sm">
                                Run Agent 3
                            </button>
                        )}
                        {step === 2 && agentStatus === 'RUNNING' && <Activity className="animate-spin text-orange-400" />}
                        {step >= 3 && <CheckCircle className="text-emerald-500" size={20} />}
                    </div>

                    {step >= 3 && (
                        <div className="animate-in slide-in-from-top-4 fade-in duration-500">
                            {results.driftA?.length === 0 && results.driftB?.length === 0 ? (
                                <p className="text-[--text-muted] flex items-center gap-2">
                                    <CheckCircle size={16} /> No schema drift detected. All fields mapped to Canonical Schema.
                                </p>
                            ) : (
                                <div className="space-y-3">
                                    {[...(results.driftA || []), ...(results.driftB || [])].map((d, i) => (
                                        <div key={i} className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded">
                                            <AlertTriangle size={16} className="text-red-400" />
                                            <span className="text-sm">
                                                New field detected in <strong>{d.vendor}</strong>: <span className="font-mono bg-black/20 px-1 rounded">{d.column}</span>
                                            </span>
                                            <span className="ml-auto text-xs bg-red-500 text-white px-2 py-0.5 rounded-full">New Schema</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AIProcessing;
