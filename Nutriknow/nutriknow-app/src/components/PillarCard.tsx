import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LucideIcon, ChevronDown, ChevronUp } from 'lucide-react';

interface PillarCardProps {
    title: string;
    score: number;
    icon: LucideIcon;
    delay: number;
    explanation?: {
        factors: { label: string; status: 'good' | 'bad' | 'neutral' }[];
    };
}

export const PillarCard: React.FC<PillarCardProps> = ({
    title,
    score,
    icon: Icon,
    delay,
    explanation
}) => {
    const [showExplanation, setShowExplanation] = useState(false);

    const getColor = (s: number) => {
        if (s >= 70) return { bg: 'bg-green-500', text: 'text-green-600', light: 'bg-green-100' };
        if (s >= 40) return { bg: 'bg-yellow-500', text: 'text-yellow-600', light: 'bg-yellow-100' };
        return { bg: 'bg-red-500', text: 'text-red-600', light: 'bg-red-100' };
    };

    const color = getColor(score);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
            className="bg-white border border-gray-100 rounded-xl shadow-sm overflow-hidden"
        >
            <button
                onClick={() => explanation && setShowExplanation(!showExplanation)}
                className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
            >
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <div className={`p-1.5 rounded-lg ${color.light}`}>
                            <Icon className={`w-4 h-4 ${color.text}`} />
                        </div>
                        <h5 className="text-xs font-bold text-gray-700 uppercase tracking-wide">{title}</h5>
                    </div>
                    {explanation && (
                        <div className="text-gray-400">
                            {showExplanation ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </div>
                    )}
                </div>

                <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl font-extrabold text-gray-900">{score}</span>
                    <span className="text-xs text-gray-400 font-medium">/100</span>
                </div>

                {/* Horizontal Progress Bar */}
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div
                        className={`h-full ${color.bg}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${score}%` }}
                        transition={{ duration: 1.2, delay: delay + 0.3, ease: "easeOut" }}
                    />
                </div>
            </button>

            {/* Explanation Dropdown */}
            <AnimatePresence>
                {showExplanation && explanation && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="border-t border-gray-100 bg-gray-50 px-4 py-3"
                    >
                        <p className="text-xs font-semibold text-gray-600 mb-2">Why this score?</p>
                        <div className="space-y-1.5">
                            {explanation.factors.map((factor, idx) => (
                                <div key={idx} className="flex items-center text-xs">
                                    <span className={`mr-2 ${factor.status === 'good' ? 'text-green-600' :
                                            factor.status === 'bad' ? 'text-red-600' :
                                                'text-gray-500'
                                        }`}>
                                        {factor.status === 'good' ? '✔' : factor.status === 'bad' ? '❌' : '●'}
                                    </span>
                                    <span className="text-gray-700">{factor.label}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};
