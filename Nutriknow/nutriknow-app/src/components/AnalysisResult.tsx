import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { NutritionAnalysis } from '@/types/nutrition';
import { ScoreGauge } from './ScoreGauge';
import { PillarCard } from './PillarCard';
import { InteractiveNutritionImage } from './InteractiveNutritionImage';
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Flame,
  Heart,
  Leaf,
  Scale,
  Activity,
  Wheat,
  Droplet,
  Candy,
  Beef
} from 'lucide-react';

interface AnalysisResultProps {
  analysis: NutritionAnalysis;
  uploadedImageUrl?: string | null;
}

export const AnalysisResult: React.FC<AnalysisResultProps> = ({ analysis, uploadedImageUrl }) => {
  const [showNutritionDetails, setShowNutritionDetails] = useState(false);

  // Generate context text for the score
  const getScoreContext = () => {
    const warnings = analysis.warnings || [];
    if (warnings.length > 0) {
      return warnings[0]; // Show first warning
    }
    if (analysis.score >= 80) return 'Excellent nutritional profile with great balance.';
    if (analysis.score >= 50) return 'Moderate nutrition quality.';
    return 'Consider healthier alternatives.';
  };

  // Generate explanations for pillars
  const getPillarExplanations = () => {
    const data = (analysis as any).nutritionData || {};

    return {
      nutrient_density: {
        factors: [
          { label: `Protein: ${data.protein || 0}g`, status: ((data.protein || 0) > 5 ? 'good' : 'bad') as 'good' | 'bad' },
          { label: `Fiber: ${data.dietaryFiber || 0}g`, status: ((data.dietaryFiber || 0) > 3 ? 'good' : 'bad') as 'good' | 'bad' },
          { label: 'Vitamins & Minerals present', status: 'neutral' as 'neutral' },
        ]
      },
      sugar_additives: {
        factors: [
          { label: `Sugars: ${data.sugars || 0}g`, status: ((data.sugars || 0) < 5 ? 'good' : 'bad') as 'good' | 'bad' },
          { label: `Sodium: ${data.sodium || 0}mg`, status: ((data.sodium || 0) < 300 ? 'good' : 'bad') as 'good' | 'bad' },
          { label: `Trans Fat: ${data.transFat || 0}g`, status: ((data.transFat || 0) === 0 ? 'good' : 'bad') as 'good' | 'bad' },
        ]
      }
    };
  };

  const pillarExplanations = getPillarExplanations();

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8">

      {/* Top Row: Score & Quick Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Health Score Card - Left Aligned */}
        <motion.div
          className="lg:col-span-1 bg-white rounded-2xl shadow-xl p-8 border border-gray-100"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <ScoreGauge score={analysis.score} context={getScoreContext()} />
        </motion.div>

        {/* Badges & Quick Insights */}
        <div className="lg:col-span-2 space-y-4">

          {/* Badges Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100"
          >
            <h3 className="text-sm font-bold text-gray-500 upper tracking-wider mb-4">Quick Overview</h3>

            <div className="flex flex-wrap gap-2 mb-4">
              {/* Green/Blue Badges */}
              {analysis.badges?.map(badge => (
                <span
                  key={badge}
                  className="inline-flex items-center px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-semibold"
                >
                  <span className="mr-1.5">🟢</span>
                  {badge}
                </span>
              ))}

              {/* Red/Yellow Alerts */}
              {analysis.warnings?.map(warning => (
                <span
                  key={warning}
                  className="inline-flex items-center px-3 py-1.5 bg-red-100 text-red-700 rounded-full text-sm font-semibold"
                >
                  <span className="mr-1.5">🔴</span>
                  {warning}
                </span>
              ))}

              {(!analysis.badges?.length && !analysis.warnings?.length) && (
                <span className="text-sm text-gray-400 italic">No specific highlights</span>
              )}
            </div>

            {/* Top Insights */}
            {analysis.insights && analysis.insights.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <ul className="space-y-2 text-sm text-gray-700">
                  {analysis.insights.slice(0, 3).map((insight, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-green-500 mr-2 mt-0.5">•</span>
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Pillars Section - Grouped in Card */}
      {analysis.pillarScores && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-gradient-to-br from-gray-50 to-white rounded-2xl shadow-lg p-6 border border-gray-100"
        >
          <h3 className="text-lg font-bold text-gray-800 mb-5">Score Breakdown</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <PillarCard
              title="Nutrient Density"
              score={analysis.pillarScores.nutrient_density}
              icon={Leaf}
              delay={0.5}
              explanation={pillarExplanations.nutrient_density}
            />
            <PillarCard
              title="Macro Balance"
              score={analysis.pillarScores.macro_balance}
              icon={Scale}
              delay={0.6}
            />
            <PillarCard
              title="Sugar & Additives"
              score={analysis.pillarScores.sugar_additives}
              icon={AlertTriangle}
              delay={0.7}
              explanation={pillarExplanations.sugar_additives}
            />
            <PillarCard
              title="Satiety"
              score={analysis.pillarScores.satiety_glycemic}
              icon={Heart}
              delay={0.8}
            />
            <PillarCard
              title="Processing"
              score={analysis.pillarScores.processing_level}
              icon={Activity}
              delay={0.9}
            />
          </div>
        </motion.div>
      )}

      {/* Serving Info - Compact */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex flex-wrap justify-between items-center gap-4 text-sm text-blue-800"
      >
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4" />
          <span className="font-semibold">Serving:</span>
          {(analysis as any).nutritionData?.servingSize || 'N/A'}
        </div>
        <div className="flex items-center gap-2">
          <span className="font-semibold">Servings/Pack:</span>
          {(analysis as any).nutritionData?.servingsPerContainer || 'N/A'}
        </div>
        <div className="flex items-center gap-2">
          <span className="font-semibold">Package:</span>
          {(analysis as any).nutritionData?.packageSizeGrams ? `${(analysis as any).nutritionData.packageSizeGrams}g` : 'N/A'}
        </div>
      </motion.div>

      {/* Collapsible Nutrition Facts */}
      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
        <button
          onClick={() => setShowNutritionDetails(!showNutritionDetails)}
          className="w-full flex items-center justify-between p-5 hover:bg-gray-50 transition-colors"
        >
          <span className="font-semibold text-gray-800 flex items-center text-left">
            <Flame className="w-5 h-5 mr-3 text-orange-500" />
            See Full Nutrition Breakdown
          </span>
          {showNutritionDetails ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
        </button>

        {showNutritionDetails && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-6 border-t border-gray-100 bg-gray-50"
          >
            {analysis.totalPackage ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6">
                <NutrientItem icon={Flame} label="Calories" value={`${analysis.totalPackage.calories}`} unit="kcal" highlight />
                <NutrientItem icon={Beef} label="Protein" value={`${analysis.totalPackage.protein}`} unit="g" />
                <NutrientItem icon={Wheat} label="Carbs" value={`${analysis.totalPackage.totalCarbohydrates}`} unit="g" />
                <NutrientItem icon={Droplet} label="Fat" value={`${analysis.totalPackage.totalFat}`} unit="g" />
                <NutrientItem icon={Candy} label="Sugar" value={`${analysis.totalPackage.sugars || 0}`} unit="g" />
                <NutrientItem icon={Droplet} label="Sodium" value={`${analysis.totalPackage.sodium || 0}`} unit="mg" />
                <NutrientItem icon={Leaf} label="Fiber" value={`${analysis.totalPackage.dietaryFiber || 0}`} unit="g" />
                <NutrientItem icon={Droplet} label="Sat. Fat" value={`${analysis.totalPackage.saturatedFat || 0}`} unit="g" />
              </div>
            ) : (
              <p className="text-gray-500 italic text-center">Total package data not available.</p>
            )}
          </motion.div>
        )}
      </div>

      {/* Interactive Nutrition Image - NEW SECTION */}
      {uploadedImageUrl && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
        >
          <InteractiveNutritionImage imageUrl={uploadedImageUrl} analysis={analysis} />
        </motion.div>
      )}
    </div>
  );
};

// Helper Component for Nutrition Items with Icons
const NutrientItem = ({
  icon: Icon,
  label,
  value,
  unit,
  highlight = false
}: {
  icon: any;
  label: string;
  value: string;
  unit: string;
  highlight?: boolean;
}) => (
  <div className={`flex flex-col ${highlight ? 'text-orange-600' : 'text-gray-700'}`}>
    <div className="flex items-center gap-2 mb-1">
      <Icon className={`w-4 h-4 ${highlight ? 'text-orange-500' : 'text-gray-400'}`} />
      <span className="text-xs text-gray-500 font-medium uppercase">{label}</span>
    </div>
    <span className={`text-xl font-bold ${highlight ? 'text-2xl' : ''}`}>
      {value}<span className="text-sm font-normal text-gray-500 ml-1">{unit}</span>
    </span>
  </div>
);