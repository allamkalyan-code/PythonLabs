// Types for nutrition data and analysis
export interface NutritionFacts {
  servingSize: string;
  servingsPerContainer: number;
  calories: number;
  totalFat: number;
  saturatedFat: number;
  transFat: number;
  cholesterol: number;
  sodium: number;
  totalCarbohydrates: number;
  dietaryFiber: number;
  sugars: number;
  addedSugars: number;
  protein: number;
  vitamins: {
    [key: string]: number;
  };
  minerals: {
    [key: string]: number;
  };
  // Raw table extraction: an array of rows where each row is a map of column name -> value
  rawTable?: Array<{ [column: string]: string | number | null }>;

  // Any additional metadata the parser finds: ingredients list, manufacturer, barcode, footnotes
  extras?: {
    ingredients?: string[];
    manufacturer?: string;
    barcode?: string;
    footnotes?: string[];
    netWeight?: string;
  };
}

export interface NutritionAnalysis {
  score: number;
  insights: string[];
  allergenAlerts: string[];
  healthIndex: number;
  servingNormalized: NutritionFacts;
  totalPackage?: NutritionFacts;

  // Advanced Scoring Fields
  pillarScores?: {
    nutrient_density: number;
    macro_balance: number;
    sugar_additives: number;
    satiety_glycemic: number;
    processing_level: number;
  };
  badges?: string[];
  warnings?: string[];
}

export interface IngredientInfo {
  name: string;
  description: string;
  category: string;
  concerns: string[];
}

export interface UserPreferences {
  allergens: string[];
  dietaryRestrictions: string[];
  healthGoals: string[];
}