import React from 'react';
import { Code, Copy } from 'lucide-react';

const MetadataStore = ({ mappings, schema }) => {
    const metadata = {
        canonical_model: "Loan",
        version: "v1.0",
        mappings: mappings.map(m => ({
            source_system: m.vendor,
            source_column: m.column,
            canonical_column: m.suggested_canonical,
            status: m.status,
            confidence: m.confidence
        })),
        detected_new_fields: mappings.filter(m => m.status === 'UNMAPPED' || m.confidence < 0.5).map(m => ({
            source_system: m.vendor,
            field: m.column,
            suggested_action: "ADD_TO_CANONICAL"
        }))
    };

    return (
        <div className="card h-full flex flex-col border-l-4 border-l-slate-500 bg-[#0f1219]"> {/* Slightly darker bg for code */}
            <div className="flex items-center justify-between mb-4 border-b border-[--border] pb-3">
                <h3 className="font-semibold flex items-center gap-2">
                    <Code size={18} className="text-slate-400" />
                    Mapping Metadata Store
                </h3>
                <button className="text-xs flex items-center gap-1 text-[--text-muted] hover:text-white transition-colors">
                    <Copy size={12} /> Copy JSON
                </button>
            </div>

            <pre className="flex-1 overflow-auto custom-scrollbar font-mono text-xs text-blue-300">
                {JSON.stringify(metadata, null, 2)}
            </pre>

            <div className="mt-2 text-xs text-[--text-muted] flex justify-between">
                <span>Updates Live</span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    Active
                </span>
            </div>
        </div>
    );
};

export default MetadataStore;
