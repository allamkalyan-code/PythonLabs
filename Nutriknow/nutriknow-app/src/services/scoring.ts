import { NutritionFacts, NutritionAnalysis } from '@/types/nutrition';
import { AdvancedScoringService, FoodData } from './advancedScoringService';

const advancedScoring = new AdvancedScoringService();

/**
 * Calculate total package nutrition values
 */
export function calculateTotalPackage(n: NutritionFacts): NutritionFacts | null {
  const clone: any = { ...n };

  // Try to use the extracted values and serving size
  const extractedVals = (n as any).extractedValues;
  let extractedServingSize = (n as any).extractedServingSize; // e.g., 50 or 100
  let packageSize = (n as any).packageSizeGrams;

  // If package size is missing, try to calculate it from servings * serving size
  if (!packageSize && n.servingsPerContainer && n.servingSize) {
    // Try to parse serving size string (e.g. "20g")
    const match = n.servingSize.match(/(\d+(\.\d+)?)\s*(g|gram|ml)/i);
    if (match) {
      const servingGrams = parseFloat(match[1]);
      packageSize = n.servingsPerContainer * servingGrams;
      if (!extractedServingSize) {
        extractedServingSize = servingGrams;
      }
    }
  }

  if (!extractedVals || !packageSize || packageSize <= 0) {
    return null; // Can't calculate without this info
  }

  // If we don't know the extracted serving size, assume it's per 100g
  const servingGrams = extractedServingSize || 100;

  // Calculate the multiplier
  const multiplier = packageSize / servingGrams;

  // Apply multiplier to ALL numeric fields in extractedValues
  Object.keys(extractedVals).forEach((key) => {
    const value = extractedVals[key];
    if (typeof value === 'number') {
      clone[key] = Math.round(value * multiplier * 10) / 10;
    } else if (value !== null && value !== undefined) {
      clone[key] = value;
    }
  });

  clone.servingSize = `${packageSize} g (total package)`;
  clone.servingsPerContainer = 1;

  return clone as NutritionFacts;
}

/**
 * Build a NutritionAnalysis object using the Advanced Scoring Service
 */
export function analyzeNutritionFacts(n: NutritionFacts, userAllergens: string[] = []): NutritionAnalysis {
  const totalPackage = calculateTotalPackage(n);
  const extractedVals = (n as any).extractedValues || {};

  // Map to FoodData for advanced scoring
  // We prefer extractedValues (numbers) over the potentially string-based top-level fields
  const foodData: FoodData = {
    name: (n as any).extras?.manufacturer || 'Unknown Food',
    serving_size_g: (n as any).extractedServingSize || 100,
    energy_kcal: extractedVals.calories ?? n.calories,
    protein_g: extractedVals.protein ?? n.protein,
    carbs_g: extractedVals.totalCarbohydrates ?? n.totalCarbohydrates,
    sugars_total_g: extractedVals.sugars ?? n.sugars,
    sugars_added_g: extractedVals.addedSugars ?? n.addedSugars,
    fat_total_g: extractedVals.totalFat ?? n.totalFat,
    fat_sat_g: extractedVals.saturatedFat ?? n.saturatedFat,
    fat_trans_g: extractedVals.transFat ?? n.transFat,
    fiber_g: extractedVals.dietaryFiber ?? n.dietaryFiber,
    sodium_mg: extractedVals.sodium ?? n.sodium,
    vitamins_mg: n.vitamins,
    minerals_mg: n.minerals,
    // Note: NOVA and additives are not currently extracted by VisionService reliably
    // We would need to enhance VisionService to extract 'additives' list and 'nova_level'
  };

  const healthResult = advancedScoring.calculateHealthScore(foodData);

  // Allergen detection
  const ingredientList: string[] = (n as any).extras?.ingredients || [];
  const allergenAlerts = userAllergens.filter(a => {
    return ingredientList.some(i => i.toLowerCase().includes(a.toLowerCase()));
  });

  // Generate insights
  const insights: string[] = [];

  // Add Badges and Warnings to insights
  healthResult.badges.forEach(b => insights.push(`✅ ${b}`));
  healthResult.warnings.forEach(w => insights.push(`⚠️ ${w}`));

  // Add generic insights if few specific ones
  if (insights.length < 3) {
    if (healthResult.final_score > 80) insights.push('Excellent nutritional profile.');
    else if (healthResult.final_score > 50) insights.push('Moderate nutritional profile.');
    else insights.push('Low nutritional value, consume in moderation.');
  }

  // Add specific pillar insights
  if (healthResult.pillar_scores.nutrient_density > 70) insights.push('High nutrient density.');
  if (healthResult.pillar_scores.sugar_additives < 50) insights.push('High in sugar or additives.');

  return {
    score: healthResult.final_score,
    insights,
    allergenAlerts,
    healthIndex: healthResult.final_score,
    servingNormalized: n,
    totalPackage: totalPackage || undefined,
    pillarScores: healthResult.pillar_scores,
    badges: healthResult.badges,
    warnings: healthResult.warnings,
  };
}
