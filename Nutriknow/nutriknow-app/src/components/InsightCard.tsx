import React from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface InsightCardProps {
    title: string;
    value?: string | number;
    icon?: LucideIcon;
    color?: 'green' | 'blue' | 'yellow' | 'red' | 'gray';
    children?: React.ReactNode;
    className?: string;
    delay?: number;
}

export const InsightCard: React.FC<InsightCardProps> = ({
    title,
    value,
    icon: Icon,
    color = 'gray',
    children,
    className = '',
    delay = 0
}) => {
    const colorStyles = {
        green: 'bg-green-50 text-green-700 border-green-100',
        blue: 'bg-blue-50 text-blue-700 border-blue-100',
        yellow: 'bg-yellow-50 text-yellow-700 border-yellow-100',
        red: 'bg-red-50 text-red-700 border-red-100',
        gray: 'bg-white text-gray-700 border-gray-100',
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay }}
            className={`
        rounded-xl border p-5 shadow-sm hover:shadow-md transition-shadow duration-300
        ${colorStyles[color]}
        ${className}
      `}
        >
            <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm uppercase tracking-wide opacity-80">{title}</h4>
                {Icon && <Icon className="w-5 h-5 opacity-70" />}
            </div>

            {value && (
                <div className="text-2xl font-bold">
                    {value}
                </div>
            )}

            {children}
        </motion.div>
    );
};
