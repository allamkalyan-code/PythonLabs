import React from 'react';
import { motion } from 'framer-motion';

interface ScoreGaugeProps {
    score: number;
    context?: string;
    size?: number;
    strokeWidth?: number;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({
    score,
    context,
    size = 200,
    strokeWidth = 16
}) => {
    const center = size / 2;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;

    // Apple Health-inspired colors
    const getScoreInfo = (s: number) => {
        if (s >= 90) return { color: '#34c759', bgColor: 'rgb(52, 199, 89)', label: 'Excellent' }; // iOS green
        if (s >= 70) return { color: '#30d158', bgColor: 'rgb(48, 209, 88)', label: 'Great' };
        if (s >= 50) return { color: '#ff9500', bgColor: 'rgb(255, 149, 0)', label: 'Good' }; // iOS orange
        return { color: '#ff3b30', bgColor: 'rgb(255, 59, 48)', label: 'Poor' }; // iOS red
    };

    const scoreInfo = getScoreInfo(score);

    return (
        <div className="flex flex-col items-center">
            <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
                {/* Background Circle */}
                <svg className="transform -rotate-90 w-full h-full">
                    {/* Track */}
                    <circle
                        cx={center}
                        cy={center}
                        r={radius}
                        fill="transparent"
                        stroke="#f5f5f7"
                        strokeWidth={strokeWidth}
                    />
                    {/* Progress */}
                    <motion.circle
                        cx={center}
                        cy={center}
                        r={radius}
                        fill="transparent"
                        stroke={scoreInfo.color}
                        strokeWidth={strokeWidth}
                        strokeDasharray={circumference}
                        initial={{ strokeDashoffset: circumference }}
                        animate={{ strokeDashoffset: offset }}
                        transition={{ duration: 2, ease: [0.16, 1, 0.3, 1] }}
                        strokeLinecap="round"
                        style={{
                            filter: `drop-shadow(0 0 8px ${scoreInfo.bgColor}40)`
                        }}
                    />
                </svg>

                {/* Score Text */}
                <div className="absolute flex flex-col items-center justify-center text-center">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                        className="flex flex-col items-center"
                    >
                        <span className="text-6xl font-bold text-[#1d1d1f] tracking-tight" style={{ fontVariantNumeric: 'tabular-nums' }}>
                            {Math.round(score)}
                        </span>
                        <span className="text-xs font-medium text-[#86868b] uppercase tracking-widest mt-1">
                            Health Score
                        </span>
                    </motion.div>
                </div>
            </div>

            {/* Label Badge - iOS Style */}
            <motion.div
                className="mt-6 px-4 py-2 rounded-full font-semibold text-sm"
                style={{
                    backgroundColor: `${scoreInfo.bgColor}15`,
                    color: scoreInfo.color
                }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.4 }}
            >
                {scoreInfo.label}
            </motion.div>

            {/* Context Text */}
            {context && (
                <motion.p
                    className="mt-4 text-sm text-[#86868b] text-center max-w-xs leading-relaxed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1, duration: 0.4 }}
                >
                    {context}
                </motion.p>
            )}
        </div>
    );
};
