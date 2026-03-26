import React, { useState, useEffect } from 'react';
import { Check, X, Edit2, ArrowRight, Save, RotateCcw } from 'lucide-react';
import CanonicalViewer from './CanonicalViewer';
import MetadataStore from './MetadataStore';
import { CANONICAL_SCHEMA } from '../utils/mockAgents';

const ReviewDashboard = ({ analysisResults, onReset }) => {
    // Combine all mappings into a single editable state
    const [mappings, setMappings] = useState([]);

    useEffect(() => {
        if (analysisResults) {
            const allMappings = [
                ...(analysisResults.mapA || []).map(m => ({ ...m, id: `A-${m.column}` })),
                ...(analysisResults.mapB || []).map(m => ({ ...m, id: `B-${m.column}` }))
            ];
            setMappings(allMappings);
        }
    }, [analysisResults]);

    const handleAction = (id, action, newValue = null) => {
        setMappings(prev => prev.map(m => {
            if (m.id !== id) return m;

            if (action === 'APPROVE') {
                return { ...m, status: 'APPROVED' };
            }
            if (action === 'REJECT') {
                return { ...m, status: 'REJECTED' };
            }
            if (action === 'EDIT') {
                // Just toggle edit mode or save directly if newValue provided
                return { ...m, suggested_canonical: newValue, status: 'MODIFIED_BY_HUMAN' };
            }
            return m;
        }));
    };

    return (
        <div className="h-[calc(100vh-140px)] flex flex-col gap-6 animate-in fade-in duration-500">

            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold">Human-in-the-Loop Review</h2>
                    <p className="text-[--text-muted]">Review AI suggestions, resolve conflicts, and finalize the mapping.</p>
                </div>
                <div className="flex gap-3">
                    <button onClick={onReset} className="btn btn-ghost hover:bg-slate-700">
                        <RotateCcw size={18} /> Reset Prototype
                    </button>
                    <button className="btn btn-primary shadow-lg shadow-indigo-500/20">
                        <Save size={18} /> Finalize Mappings
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6 flex-1 overflow-hidden">

                {/* Left Panel: Mapping Editor (7 cols) */}
                <div className="col-span-7 flex flex-col card p-0 overflow-hidden border-t-4 border-t-[--primary]">
                    <div className="p-4 border-b border-[--border] bg-[--bg-panel] flex justify-between items-center">
                        <h3 className="font-semibold">Detected Field Mappings</h3>
                        <span className="text-xs px-2 py-1 bg-[--bg-app] rounded text-[--text-muted]">
                            {mappings.filter(m => m.status === 'APPROVED').length} / {mappings.length} Approved
                        </span>
                    </div>

                    <div className="flex-1 overflow-auto custom-scrollbar">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-[--bg-app] text-[--text-muted] sticky top-0">
                                <tr>
                                    <th className="py-3 pl-4">Source System</th>
                                    <th className="py-3">Source Field</th>
                                    <th className="py-3">Canonical Field</th>
                                    <th className="py-3">Confidence</th>
                                    <th className="py-3 pr-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[--border]">
                                {mappings.map((m) => (
                                    <tr key={m.id} className={`group transition-colors ${m.status === 'APPROVED' ? 'bg-emerald-500/5' : ''}`}>
                                        <td className="py-3 pl-4 text-[--text-muted] text-xs uppercase font-semibold">{m.vendor}</td>
                                        <td className="py-3 font-mono">{m.column}</td>

                                        <td className="py-3">
                                            {/* Dropdown for editing/viewing */}
                                            <select
                                                className={`bg-[--bg-app] border border-[--border] rounded px-2 py-1 text-sm focus:outline-none focus:border-[--primary] ${m.status === 'MODIFIED_BY_HUMAN' ? 'text-[--warning]' : ''}`}
                                                value={m.suggested_canonical || ''}
                                                onChange={(e) => handleAction(m.id, 'EDIT', e.target.value)}
                                            >
                                                <option value="" disabled>Select Field...</option>
                                                {CANONICAL_SCHEMA.map(f => (
                                                    <option key={f.field} value={f.field}>{f.field}</option>
                                                ))}
                                            </select>
                                        </td>

                                        <td className="py-3">
                                            <span className={`text-xs px-1.5 py-0.5 rounded ${m.confidence > 0.8 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                                                {(m.confidence * 100).toFixed(0)}%
                                            </span>
                                        </td>

                                        <td className="py-3 pr-4 text-right">
                                            {m.status === 'APPROVED' ? (
                                                <span className="flex items-center justify-end gap-1 text-emerald-500 text-xs font-semibold">
                                                    <Check size={14} /> Approved
                                                    <button onClick={() => handleAction(m.id, 'REJECT')} className="text-[--text-muted] hover:text-[--text-main] ml-2 underline">Undo</button>
                                                </span>
                                            ) : m.status === 'REJECTED' ? (
                                                <span className="flex items-center justify-end gap-1 text-[--text-muted] text-xs">
                                                    Rejected
                                                    <button onClick={() => handleAction(m.id, 'APPROVE')} className="text-[--text-muted] hover:text-[--text-main] ml-2 underline">Undo</button>
                                                </span>
                                            ) : (
                                                <div className="flex items-center justify-end gap-2">
                                                    <button
                                                        onClick={() => handleAction(m.id, 'APPROVE')}
                                                        className="p-1.5 hover:bg-emerald-500/20 text-[--text-muted] hover:text-emerald-500 rounded transition-colors"
                                                        title="Approve"
                                                    >
                                                        <Check size={16} />
                                                    </button>
                                                    <button
                                                        onClick={() => handleAction(m.id, 'REJECT')}
                                                        className="p-1.5 hover:bg-red-500/20 text-[--text-muted] hover:text-red-500 rounded transition-colors"
                                                        title="Reject / Ignore"
                                                    >
                                                        <X size={16} />
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Right Panel: Output Store & Schema (5 cols) */}
                <div className="col-span-5 flex flex-col gap-6">
                    <div className="flex-1 min-h-0">
                        <CanonicalViewer />
                    </div>
                    <div className="flex-1 min-h-0">
                        <MetadataStore mappings={mappings} />
                    </div>
                </div>

            </div>
        </div>
    );
};

export default ReviewDashboard;
