// Nutrition term definitions
export const nutritionDefinitions: Record<string, { term: string; definition: string }> = {
    servingSize: {
        term: "Serving Size",
        definition: "The amount of food typically consumed in one sitting. All nutrition values are based on this quantity."
    },
    servingsPerContainer: {
        term: "Servings Per Container",
        definition: "The total number of servings in the entire package. Multiply nutrition values by this to get total package nutrition."
    },
    calories: {
        term: "Calories",
        definition: "Energy provided by food. Average adult needs 2000-2500 calories per day. Too many calories can lead to weight gain."
    },
    totalFat: {
        term: "Total Fat",
        definition: "Sum of all fats. While fat is essential, limit saturated and avoid trans fats. Recommended: <30% of daily calories."
    },
    saturatedFat: {
        term: "Saturated Fat",
        definition: "Fat linked to raised cholesterol. Found in animal products and some oils. Limit to <10% of daily calories."
    },
    transFat: {
        term: "Trans Fat",
        definition: "Artificial fat that raises bad cholesterol. Avoid entirely. Even small amounts are harmful to heart health."
    },
    cholesterol: {
        term: "Cholesterol",
        definition: "Waxy substance in animal products. High intake can clog arteries. Limit to <300mg per day."
    },
    sodium: {
        term: "Sodium",
        definition: "Salt content. High sodium increases blood pressure and heart disease risk. Limit to <2300mg per day."
    },
    totalCarbohydrates: {
        term: "Total Carbohydrates",
        definition: "Body's main energy source including sugars, starches, and fiber. Choose whole grains over refined carbs."
    },
    dietaryFiber: {
        term: "Dietary Fiber",
        definition: "Indigestible plant material that aids digestion and keeps you full. Aim for 25-30g per day. Higher is better!"
    },
    sugars: {
        term: "Sugars",
        definition: "Natural and added sugars combined. High sugar intake linked to obesity and diabetes. Limit added sugars to <50g/day."
    },
    addedSugars: {
        term: "Added Sugars",
        definition: "Sugars added during processing. Unlike natural sugars, these provide no nutritional value. Limit to <25g/day."
    },
    protein: {
        term: "Protein",
        definition: "Essential for building muscle, enzymes, and hormones. Adults need ~50g per day. Higher protein promotes satiety."
    },
    vitamins: {
        term: "Vitamins & Minerals",
        definition: "Micronutrients essential for health. Look for foods naturally rich in these rather than fortified products."
    },
    percentDailyValue: {
        term: "% Daily Value",
        definition: "Percentage of recommended daily intake. 5% or less is low, 20% or more is high. Based on 2000 calorie diet."
    },
    ingredients: {
        term: "Ingredients",
        definition: "Listed by weight, heaviest first. Watch for hidden sugars, unhealthy fats, and long lists of additives."
    }
};

// Define hotspot positions for a standard nutrition label (percentage-based for responsiveness)
export interface Hotspot {
    id: string;
    term: keyof typeof nutritionDefinitions;
    x: number; // percentage from left
    y: number; // percentage from top
    width: number; // percentage width
    height: number; // percentage height
}

// Standard FDA nutrition label layout hotspots
export const standardHotspots: Hotspot[] = [
    { id: 'serving-size', term: 'servingSize', x: 10, y: 8, width: 40, height: 4 },
    { id: 'servings-container', term: 'servingsPerContainer', x: 10, y: 12, width: 45, height: 4 },
    { id: 'calories', term: 'calories', x: 10, y: 20, width: 35, height: 6 },
    { id: 'total-fat', term: 'totalFat', x: 10, y: 30, width: 40, height: 4 },
    { id: 'saturated-fat', term: 'saturatedFat', x: 15, y: 34, width: 40, height: 4 },
    { id: 'trans-fat', term: 'transFat', x: 15, y: 38, width: 35, height: 4 },
    { id: 'cholesterol', term: 'cholesterol', x: 10, y: 44, width: 35, height: 4 },
    { id: 'sodium', term: 'sodium', x: 10, y: 48, width: 30, height: 4 },
    { id: 'total-carbs', term: 'totalCarbohydrates', x: 10, y: 54, width: 50, height: 4 },
    { id: 'fiber', term: 'dietaryFiber', x: 15, y: 58, width: 35, height: 4 },
    { id: 'sugars', term: 'sugars', x: 15, y: 62, width: 30, height: 4 },
    { id: 'added-sugars', term: 'addedSugars', x: 20, y: 66, width: 35, height: 4 },
    { id: 'protein', term: 'protein', x: 10, y: 72, width: 30, height: 4 },
    { id: 'vitamins', term: 'vitamins', x: 10, y: 80, width: 60, height: 8 },
    { id: 'percent-dv', term: 'percentDailyValue', x: 70, y: 28, width: 25, height: 45 },
];

export class NutritionDefinitionsService {
    /**
     * Get definition for a nutrition term
     */
    getDefinition(term: keyof typeof nutritionDefinitions): { term: string; definition: string } | null {
        return nutritionDefinitions[term] || null;
    }

    /**
     * Get all hotspots for a standard nutrition label
     */
    getStandardHotspots(): Hotspot[] {
        return standardHotspots;
    }

    /**
     * Get all available definitions
     */
    getAllDefinitions(): Record<string, { term: string; definition: string }> {
        return nutritionDefinitions;
    }
}

// Export singleton instance
export default new NutritionDefinitionsService();
