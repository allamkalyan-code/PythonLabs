export interface FoodData {
    name?: string;
    serving_size_g?: number;
    energy_kcal?: number;
    protein_g?: number;
    carbs_g?: number;
    sugars_total_g?: number;
    sugars_added_g?: number;
    fat_total_g?: number;
    fat_sat_g?: number;
    fat_trans_g?: number;
    fiber_g?: number;
    sodium_mg?: number;
    vitamins_mg?: Record<string, number>;
    minerals_mg?: Record<string, number>;
    gi?: number;
    nova_level?: number; // 1-4
    additives?: string[];
    tags?: string[];
}

export interface PillarScores {
    nutrient_density: number;
    macro_balance: number;
    sugar_additives: number;
    satiety_glycemic: number;
    processing_level: number;
}

export interface HealthScoreResult {
    final_score: number;
    pillar_scores: PillarScores;
    badges: string[];
    warnings: string[];
}

const RDI: Record<string, number> = {
    protein: 50,
    fiber: 25,
    'vitamin c': 80,
    'vitamin b12': 2.4,
    calcium: 1000,
    iron: 18,
    potassium: 3500,
    magnesium: 400,
    // Map common variations
    'vit c': 80,
    'vit b12': 2.4,
};

export class AdvancedScoringService {

    public calculateHealthScore(food: FoodData): HealthScoreResult {
        const nd = this.calculateNutrientDensity(food);
        const mb = this.calculateMacroBalance(food);
        const sa = this.calculateSugarAndAdditives(food);
        const sg = this.calculateSatietyAndGlycemic(food);
        const pl = this.calculateProcessingLevel(food);

        // Final Score Calculation
        // Weights: ND 30%, MB 25%, SA 20%, SG 15%, PL 10%
        let finalScore = (0.30 * nd) + (0.25 * mb) + (0.20 * sa) + (0.15 * sg.score) + (0.10 * pl);
        finalScore = Math.round(Math.max(0, Math.min(100, finalScore)));

        const { badges, warnings } = this.generateBadgesAndWarnings(food, sa, sg);

        return {
            final_score: finalScore,
            pillar_scores: {
                nutrient_density: Math.round(nd),
                macro_balance: Math.round(mb),
                sugar_additives: Math.round(sa),
                satiety_glycemic: Math.round(sg.score),
                processing_level: Math.round(pl),
            },
            badges,
            warnings,
        };
    }

    private calculateNutrientDensity(food: FoodData): number {
        // 1. Compute %DV for each nutrient
        // We need to look at protein, fiber, vitamins, minerals

        const getDV = (amount: number | undefined, rdi: number) => {
            if (!amount) return 0;
            const pct = (amount / rdi) * 100;
            return Math.min(150, pct); // Cap at 150
        };

        const proteinDV = getDV(food.protein_g, RDI.protein);
        const fiberDV = getDV(food.fiber_g, RDI.fiber);

        // Average Vitamin %DV
        let vitaminSum = 0;
        let vitaminCount = 0;
        if (food.vitamins_mg) {
            Object.entries(food.vitamins_mg).forEach(([key, val]) => {
                const normKey = key.toLowerCase().replace(/[^a-z0-9 ]/g, '');
                // Try to find RDI
                const rdi = RDI[normKey];
                if (rdi) {
                    vitaminSum += getDV(val, rdi);
                    vitaminCount++;
                }
            });
        }
        const avgVitaminDV = vitaminCount > 0 ? vitaminSum / vitaminCount : 0;

        // Average Mineral %DV
        let mineralSum = 0;
        let mineralCount = 0;
        if (food.minerals_mg) {
            Object.entries(food.minerals_mg).forEach(([key, val]) => {
                const normKey = key.toLowerCase().replace(/[^a-z0-9 ]/g, '');
                const rdi = RDI[normKey];
                if (rdi) {
                    mineralSum += getDV(val, rdi);
                    mineralCount++;
                }
            });
        }
        const avgMineralDV = mineralCount > 0 ? mineralSum / mineralCount : 0;

        // Compute equal-weight average -> ND_raw
        // If no vitamins/minerals found, should we divide by 4? 
        // The prompt implies 4 grouped numbers. If missing, they are 0.
        const ndRaw = (proteinDV + fiberDV + avgVitaminDV + avgMineralDV) / 4;

        // Convert to score: ND_score = min(100, (ND_raw / 150) * 100)
        // Wait, if ND_raw is 150, score is 100.
        // If ND_raw is 75, score is 50.
        return Math.min(100, (ndRaw / 150) * 100); // Wait, logic check. 
        // If I have 150% DV of everything, average is 150. 150/150*100 = 100. Correct.
    }

    private calculateMacroBalance(food: FoodData): number {
        const p = (food.protein_g || 0) * 4;
        const c = (food.carbs_g || 0) * 4;
        const f = (food.fat_total_g || 0) * 9;
        const total = p + c + f;

        if (total === 0) return 100; // Water or empty?

        const pPct = (p / total) * 100;
        const cPct = (c / total) * 100;
        const fPct = (f / total) * 100;

        const getDev = (val: number, min: number, max: number) => {
            if (val >= min && val <= max) return 0;
            if (val < min) return min - val;
            return val - max;
        };

        const pDev = getDev(pPct, 20, 30);
        const cDev = getDev(cPct, 45, 55);
        const fDev = getDev(fPct, 25, 35);

        const totalDev = pDev + cDev + fDev;

        return Math.max(0, 100 - (2 * totalDev));
    }

    private calculateSugarAndAdditives(food: FoodData): number {
        let risk = 0;
        const kcal = food.energy_kcal || 0;

        // Sugar Density
        // Use added sugar if available, else total
        const sugarVal = food.sugars_added_g !== undefined ? food.sugars_added_g : (food.sugars_total_g || 0);
        const sugarDensity = kcal > 0 ? (sugarVal / kcal) * 100 : 0;

        if (sugarDensity > 8) risk += 30;
        else if (sugarDensity > 5) risk += 20;
        else if (sugarDensity > 2) risk += 10;

        // Sodium Density
        const sodiumDensity = kcal > 0 ? ((food.sodium_mg || 0) / kcal) * 100 : 0;
        if (sodiumDensity > 450) risk += 30;
        else if (sodiumDensity > 300) risk += 20;
        else if (sodiumDensity > 150) risk += 10;

        // Trans Fat
        if ((food.fat_trans_g || 0) > 0) risk += 25;

        // Additives
        const additiveCount = food.additives ? food.additives.length : 0;
        if (additiveCount >= 5) risk += 20;
        else if (additiveCount >= 3) risk += 10;
        else if (additiveCount >= 1) risk += 5;

        const riskTotal = Math.min(80, risk);
        return Math.max(0, 100 - riskTotal);
    }

    private calculateSatietyAndGlycemic(food: FoodData): { score: number, fiberScore: number, proteinScore: number } {
        const kcal = food.energy_kcal || 0;
        if (kcal === 0) return { score: 0, fiberScore: 0, proteinScore: 0 };

        const fiberDensity = ((food.fiber_g || 0) / kcal) * 100;
        const proteinDensity = ((food.protein_g || 0) / kcal) * 100;

        const getScore = (val: number, tiers: number[], scores: number[]) => {
            for (let i = 0; i < tiers.length; i++) {
                if (val >= tiers[i]) return scores[i];
            }
            return scores[scores.length - 1];
        };

        // Fiber: >=3 -> 100, 2-3 -> 85, 1-2 -> 70, 0.5-1 -> 50, <0.5 -> 30
        const fiberScore = getScore(fiberDensity, [3, 2, 1, 0.5], [100, 85, 70, 50, 30]);

        // Protein: >=7 -> 100, 5-7 -> 85, 3-5 -> 70, 1-3 -> 50, <1 -> 30
        const proteinScore = getScore(proteinDensity, [7, 5, 3, 1], [100, 85, 70, 50, 30]);

        let sgScore = 0;
        if (food.gi !== undefined) {
            // GI Score: <=40 -> 100, 40-55 -> 85, 55-70 -> 60, >70 -> 40
            let giScore = 40;
            if (food.gi <= 40) giScore = 100;
            else if (food.gi <= 55) giScore = 85;
            else if (food.gi <= 70) giScore = 60;

            sgScore = (0.4 * fiberScore) + (0.4 * proteinScore) + (0.2 * giScore);
        } else {
            sgScore = (0.5 * fiberScore) + (0.5 * proteinScore);
        }

        return { score: sgScore, fiberScore, proteinScore };
    }

    private calculateProcessingLevel(food: FoodData): number {
        if (food.nova_level === undefined) return 60; // Missing -> 60
        switch (food.nova_level) {
            case 1: return 100;
            case 2: return 85;
            case 3: return 60;
            case 4: return 30;
            default: return 60;
        }
    }

    private generateBadgesAndWarnings(food: FoodData, saScore: number, sg: { score: number, fiberScore: number, proteinScore: number }): { badges: string[], warnings: string[] } {
        const badges: string[] = [];
        const warnings: string[] = [];
        const kcal = food.energy_kcal || 0;

        // Badges
        // "High Protein" -> if protein_density_score >= 85
        // Wait, prompt says "protein_density_score", which corresponds to my proteinScore from SG pillar
        if (sg.proteinScore >= 85) badges.push('High Protein');

        // "High Fiber" -> if fiber_density_score >= 85
        if (sg.fiberScore >= 85) badges.push('High Fiber');

        // "Low Sugar" -> if sugar_density <= 2
        const sugarVal = food.sugars_added_g !== undefined ? food.sugars_added_g : (food.sugars_total_g || 0);
        const sugarDensity = kcal > 0 ? (sugarVal / kcal) * 100 : 0;
        if (sugarDensity <= 2) badges.push('Low Sugar');

        // "Heart Friendly" -> if sodium_density <= 150 AND SA_score >= 80
        const sodiumDensity = kcal > 0 ? ((food.sodium_mg || 0) / kcal) * 100 : 0;
        if (sodiumDensity <= 150 && saScore >= 80) badges.push('Heart Friendly');

        // "Whole Food" -> if NOVA = 1
        if (food.nova_level === 1) badges.push('Whole Food');

        // Warnings
        // sugars_added_g > 5
        if ((food.sugars_added_g || 0) > 5) warnings.push('High Added Sugar');

        // sodium_density > 300
        if (sodiumDensity > 300) warnings.push('High Sodium Density');

        // fat_trans_g > 0
        if ((food.fat_trans_g || 0) > 0) warnings.push('Contains Trans Fat');

        // nova_level = 4
        if (food.nova_level === 4) warnings.push('Highly Processed (NOVA 4)');

        return { badges, warnings };
    }
}
