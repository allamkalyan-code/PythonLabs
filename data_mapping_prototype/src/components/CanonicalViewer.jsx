import React from 'react';
import { Database, Plus } from 'lucide-react';
import { CANONICAL_SCHEMA } from '../utils/mockAgents';

const CanonicalViewer = () => {
    return (
        <div className="card h-full flex flex-col border-l-4 border-l-emerald-500">
            <div className="flex items-center justify-between mb-4 border-b border-[--border] pb-3">
                <h3 className="font-semibold flex items-center gap-2">
                    <Database size={18} className="text-emerald-500" />
                    Canonical Loan Model
                </h3>
                <button className="text-xs flex items-center gap-1 text-[--primary] hover:underline" disabled>
                    <Plus size={12} /> Add Field
                </button>
            </div>

            <div className="flex-1 overflow-auto custom-scrollbar">
                <table className="w-full text-sm text-left">
                    <thead className="text-[--text-muted] sticky top-0 bg-[--bg-panel]">
                        <tr>
                            <th className="pb-2 pl-2">Field Name</th>
                            <th className="pb-2">Type</th>
                            <th className="pb-2">Description</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[--border]">
                        {CANONICAL_SCHEMA.map((field, i) => (
                            <tr key={i} className="group hover:bg-[--bg-app] transition-colors">
                                <td className="py-2 pl-2 font-mono text-[--text-main]">{field.field}</td>
                                <td className="py-2 text-[--text-muted]">{field.type}</td>
                                <td className="py-2 text-[--text-muted] text-xs">{field.description}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default CanonicalViewer;
