import React from 'react';
import { FileJson } from 'lucide-react';

const VendorInput = ({ label, value, onChange, color }) => {
    return (
        <div className={`card h-[600px] flex flex-col ${color}`}>
            <div className="flex items-center justify-between mb-4 border-b border-[--border] pb-3">
                <div className="flex items-center gap-2">
                    <FileJson size={18} className="text-[--text-muted]" />
                    <h3 className="font-semibold text-[--text-main]">{label}</h3>
                </div>
                <span className="text-xs px-2 py-1 bg-[--bg-app] rounded text-[--text-muted]">JSON Format</span>
            </div>

            <textarea
                className="flex-1 w-full bg-[--bg-app] text-[--text-main] p-4 font-mono text-sm resize-none focus:outline-none focus:ring-1 focus:ring-[--primary] rounded-md custom-scrollbar"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                spellCheck="false"
            />

            <div className="mt-3 text-xs text-[--text-muted] flex justify-between">
                <span>{value.split('\n').length} lines</span>
                <span>{(new TextEncoder().encode(value).length / 1024).toFixed(2)} KB</span>
            </div>
        </div>
    );
};

export default VendorInput;
