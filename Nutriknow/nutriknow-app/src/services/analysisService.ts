import { NutritionAnalysis, NutritionFacts } from '@/types/nutrition';

/**
 * Service for handling LLM-based analysis of nutrition data
 */
export class AnalysisService {
  private readonly llmEndpoint: string;

  constructor(llmEndpoint: string) {
    this.llmEndpoint = llmEndpoint;
  }

  /**
   * Generate plain language explanations of nutrition facts
   * @param nutritionData The structured nutrition data
   * @returns Promise with plain language explanation
   */
  async generateExplanation(nutritionData: NutritionFacts): Promise<string> {
    try {
      const response = await fetch(this.llmEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(nutritionData),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const result = await response.json();
      return result.explanation;
    } catch (error) {
      console.error('Error generating explanation:', error);
      throw error;
    }
  }

  /**
   * Calculate nutrition score and generate insights
   * @param nutritionData The structured nutrition data
   * @returns Promise with nutrition analysis
   */
  async analyzeNutrition(nutritionData: NutritionFacts): Promise<NutritionAnalysis> {
    try {
      const response = await fetch(this.llmEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(nutritionData),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error analyzing nutrition:', error);
      throw error;
    }
  }

  /**
   * Send an image file to the LLM endpoint which will perform vision extraction and return analysis.
   * This allows the backend to handle images directly via OpenAI Vision and return a full analysis.
   */
  async processImage(imageFile: File): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('image', imageFile);

      const response = await fetch(this.llmEndpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = response.statusText;
        try {
          const errorData = await response.json();
          if (errorData.details) {
            errorMessage = `${errorData.error}: ${errorData.details}`;
          } else if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (e) {
          // Could not parse error JSON, stick with statusText
        }
        throw new Error(`Image analysis failed: ${errorMessage}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error processing image:', error);
      throw error;
    }
  }

  /**
   * Check for allergens and dietary restrictions
   * @param ingredients List of ingredients
   * @param userAllergens User's allergen list
   * @returns List of allergen alerts
   */
  checkAllergens(ingredients: string[], userAllergens: string[]): string[] {
    return userAllergens.filter(allergen =>
      ingredients.some(ingredient =>
        ingredient.toLowerCase().includes(allergen.toLowerCase())
      )
    );
  }
}

// Export a default instance using the /api/llm endpoint
const defaultAnalysisService = new AnalysisService('/api/llm');

export default defaultAnalysisService;