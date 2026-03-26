import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, X } from 'lucide-react';
import nutritionDefinitionsService from '@/services/nutritionDefinitionsService';
import { NutritionAnalysis } from '@/types/nutrition';

interface InteractiveNutritionImageProps {
    imageUrl: string;
    analysis: NutritionAnalysis;
    imageName?: string;
}

export const InteractiveNutritionImage: React.FC<InteractiveNutritionImageProps> = ({
    imageUrl,
    analysis,
    imageName = "Uploaded Label"
}) => {
    const [selectedTerm, setSelectedTerm] = useState<string | null>(null);
    const allDefs = nutritionDefinitionsService.getAllDefinitions();

    // Mapping of extracted field names to definition keys
    const fieldToDefinitionMap: Record<string, string> = {
        servingSize: 'servingSize',
        servingsPerContainer: 'servingsPerContainer',
        calories: 'calories',
        totalFat: 'totalFat',
        saturatedFat: 'saturatedFat',
        transFat: 'transFat',
        cholesterol: 'cholesterol',
        sodium: 'sodium',
        totalCarbohydrates: 'totalCarbohydrates',
        dietaryFiber: 'dietaryFiber',
        sugars: 'sugars',
        addedSugars: 'addedSugars',
        protein: 'protein',
    };

    // Dynamically extract available terms from the nutrition data
    const getAvailableTerms = (): string[] => {
        const nutritionData = (analysis as any).nutritionData || analysis.servingNormalized;
        if (!nutritionData) return [];

        const availableTerms: string[] = [];

        // Always show these if they exist
        if (nutritionData.servingSize) availableTerms.push('servingSize');
        if (nutritionData.servingsPerContainer) availableTerms.push('servingsPerContainer');

        // Check each nutrition field
        Object.keys(fieldToDefinitionMap).forEach(field => {
            if (field === 'servingSize' || field === 'servingsPerContainer') return; // Already added

            const value = nutritionData[field];
            // Include if value exists and is not zero/null/undefined
            if (value !== undefined && value !== null && value !== 0) {
                availableTerms.push(field);
            }
        });

        // Add % Daily Value if we have any values
        if (availableTerms.length > 0) {
            availableTerms.push('percentDailyValue');
        }

        return availableTerms;
    };

    const availableTerms = getAvailableTerms();

    return (
        <div className="w-full">
            <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-gray-800">Interactive Label Guide</h3>
                    <div className="flex items-center text-sm text-green-600 font-medium">
                        <Info className="w-4 h-4 mr-1" />
                        Click terms below to learn more
                    </div>
                </div>

                {/* Image Display */}
                <div className="relative w-full rounded-xl overflow-hidden bg-gray-100 mb-6">
                    <img
                        src={imageUrl}
                        alt={imageName}
                        className="w-full h-auto object-contain max-h-[500px]"
                        draggable={false}
                    />
                </div>

                {/* Dynamically Generated Nutrition Terms */}
                {availableTerms.length > 0 ? (
                    <div className="space-y-4">
                        <p className="text-sm font-semibold text-gray-700">
                            Tap any nutrition term detected on your label to learn what it means:
                        </p>

                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                            {availableTerms.map((termKey) => {
                                const defKey = fieldToDefinitionMap[termKey] || termKey;
                                const def = allDefs[defKey];
                                if (!def) return null;

                                return (
                                    <button
                                        key={termKey}
                                        onClick={() => setSelectedTerm(selectedTerm === termKey ? null : termKey)}
                                        className={`
                      px-3 py-2 rounded-lg text-sm font-medium text-left transition-all duration-200
                      ${selectedTerm === termKey
                                                ? 'bg-green-500 text-white shadow-lg ring-2 ring-green-400'
                                                : 'bg-gray-100 text-gray-700 hover:bg-green-100 hover:text-green-700'
                                            }
                    `}
                                    >
                                        {def.term}
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        <p>No nutrition terms detected on this label.</p>
                    </div>
                )}

                {/* Selected Term Definition Card */}
                <AnimatePresence>
                    {selectedTerm && (
                        <motion.div
                            initial={{ opacity: 0, height: 0, marginTop: 0 }}
                            animate={{ opacity: 1, height: 'auto', marginTop: 16 }}
                            exit={{ opacity: 0, height: 0, marginTop: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="bg-gradient-to-br from-green-50 to-blue-50 border-2 border-green-200 rounded-xl p-5 relative">
                                <button
                                    onClick={() => setSelectedTerm(null)}
                                    className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 transition-colors"
                                    aria-label="Close"
                                >
                                    <X className="w-5 h-5" />
                                </button>

                                <div className="pr-8">
                                    {(() => {
                                        const defKey = fieldToDefinitionMap[selectedTerm] || selectedTerm;
                                        const def = allDefs[defKey];
                                        return def ? (
                                            <>
                                                <h4 className="text-lg font-bold text-green-700 mb-2">
                                                    {def.term}
                                                </h4>
                                                <p className="text-sm text-gray-700 leading-relaxed">
                                                    {def.definition}
                                                </p>
                                            </>
                                        ) : null;
                                    })()}
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Helper Text */}
                <div className="mt-6 pt-4 border-t border-gray-100">
                    <p className="text-xs text-gray-500 text-center">
                        💡 Reference this guide while looking at your nutrition label to understand what each value means for your health
                    </p>
                </div>
            </div>
        </div>
    );
};
