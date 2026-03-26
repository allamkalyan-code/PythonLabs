import OpenAI from 'openai';
import sharp from 'sharp';
import { NutritionFacts } from '@/types/nutrition';

/**
 * Vision LLM service for processing nutrition label images
 * Uses OpenAI's GPT-4 Vision API to extract structured nutrition data
 */
export class VisionService {
  private maxImageSize = 20 * 1024 * 1024; // 20MB limit for OpenAI
  private targetWidth = 2000; // Max width to resize to
  private targetQuality = 80; // JPEG quality for compression
  public openai: OpenAI; // Make openai client accessible for reuse

  constructor() {
    // Initialize OpenAI client with API key from environment
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
  }

  /**
   * Process and optimize an image for the Vision API
   * @param buffer Original image buffer
   * @returns Base64 encoded optimized image
   */
  private async preprocessImage(buffer: Buffer): Promise<string> {
    try {
      const image = sharp(buffer);
      const metadata = await image.metadata();

      if (metadata.width && metadata.width > this.targetWidth) {
        image.resize({
          width: this.targetWidth,
          withoutEnlargement: true,
        });
      }

      const optimized = await image
        .jpeg({ quality: this.targetQuality })
        .toBuffer();

      if (optimized.length > this.maxImageSize) {
        throw new Error('Image too large even after optimization');
      }

      return optimized.toString('base64');
    } catch (error) {
      console.error('Image preprocessing failed:', error);
      throw new Error('Failed to process image');
    }
  }

  /**
   * Extract nutrition facts from an image using GPT-4V
   * @param imageFile Image file to process
   * @returns Structured nutrition data
   */
  async processNutritionLabel(imageBuffer: Buffer): Promise<{
    nutritionData: NutritionFacts;
    rawText: string;
  }> {
    try {
      const base64Image = await this.preprocessImage(imageBuffer);

      const response = await this.openai.chat.completions.create({
        model: 'gpt-4o',
        messages: [
          {
            role: 'system',
            content:
              'You are a precise nutrition label parser. Your job is to extract every useful piece of structured information from the provided nutrition label image. \\n\\nCRITICAL: You must identify the "Serving Size" and "Servings Per Container" (or "Servings per pack"). \\n- Handle variations like "4 bars per pack" (Servings Per Container = 4) and "1 bar = 10g" (Serving Size = "10g").\\n- If the label says "2.5 servings per pack" and "Serving size 20g", extract these numbers.\\n- If the total package weight is not explicitly stated as "Net Weight", you should INFER it by calculating (Servings Per Container * Serving Size) and put that value in extras.netWeight (e.g., "50g").\\n\\nReturn a strict JSON object with the fields: nutritionData (core nutrition values including servingSize and servingsPerContainer), percentRDA (map nutrient -> percent per serving if present), rawTable (array of rows mapping column name -> value), and extras (ingredients, manufacturer, barcode, footnotes, netWeight). Avoid extra explanatory text in the response — return only the JSON object. If a value is not present, use null or omit the key.'
          },
          {
            role: 'user',
            content: [
              {
                type: 'text',
                text:
                  'Please extract the nutrition information in JSON matching this shape:\\n{\\n  nutritionData: { servingSize: string, servingsPerContainer: number, calories: number, totalFat?: number, saturatedFat?: number, transFat?: number, cholesterol?: number, sodium?: number, totalCarbohydrates?: number, dietaryFiber?: number, sugars?: number, addedSugars?: number, protein?: number, vitamins?: { [key: string]: number }, minerals?: { [key: string]: number } },\\n  percentRDA?: { [key: string]: number },\\n  rawTable?: Array<{ [column: string]: string | number | null }>,\\n  extras?: { ingredients?: string[], manufacturer?: string, barcode?: string, footnotes?: string[], netWeight?: string }\\n}\\n\\n- Parse numeric values as numbers (integers or decimals).\\n- CRITICAL: Look for "Servings per container" or "Servings per pack" anywhere on the image. If found, include it in nutritionData.servingsPerContainer.\\n- CRITICAL: Look for "Serving size" (e.g. "20g", "1 cup (240ml)"). Include it in nutritionData.servingSize.\\n- If you calculate the net weight from servings * serving size, format it as a string like "50g" in extras.netWeight.\\n- Parse numeric values as numbers (integers or decimals).\\n- For percent columns, return numbers without the percent sign (e.g., 20).\\n- Preserve column headers from the label in rawTable (e.g., "Nutrients", "Per 100g", "%RDA per serve").\\n- If multiple columns exist, include them all in rawTable rows.\\n- Return only valid JSON (no surrounding markdown).'
              },
              {
                type: 'image_url',
                image_url: {
                  url: `data:image/jpeg;base64,${base64Image}`,
                },
              },
            ],
          },
        ],
        max_tokens: 1500,
        temperature: 0,
      });

      const content = response.choices[0]?.message?.content;
      if (!content) {
        throw new Error('No response from Vision API');
      }

      // Try to find JSON using regex
      let jsonMatch = content.match(/```json\n?(.*?)\n?```/s) || content.match(/\{[\s\S]*\}/s);

      let parsed: any;
      if (jsonMatch) {
        try {
          parsed = JSON.parse(jsonMatch[1] || jsonMatch[0]);
        } catch (e) {
          // Regex match failed to parse, try parsing whole content
          console.warn('Regex match found but failed to parse:', e);
        }
      }

      if (!parsed) {
        try {
          // Fallback: try parsing the entire content
          parsed = JSON.parse(content);
        } catch (e) {
          // If all parsing fails, throw error with the raw content for debugging
          // Limit content length in error message to avoid huge logs
          const preview = content.length > 500 ? content.substring(0, 500) + '...' : content;
          throw new Error(`Could not parse JSON object from vision response. Raw response: ${preview}`);
        }
      }

      const nutritionData = parsed.nutritionData || parsed;
      const percentRDA = parsed.percentRDA || parsed.percent_rda || undefined;
      const rawTable = parsed.rawTable || parsed.raw_table || undefined;
      const extras = parsed.extras || undefined;

      // Extract nutrition values from rawTable - detect the serving size column dynamically
      const extractedValues: any = {};
      let servingSizeGrams: number | null = null;
      let servingSizeLabel: string = '';

      if (rawTable && Array.isArray(rawTable)) {
        // First, detect which column contains the nutrition values
        const firstRow = rawTable[0] || {};
        const columnKeys = Object.keys(firstRow);

        // Find the nutrition value column (skip nutrient name columns)
        let valueColumnKey: string | null = null;

        for (const key of columnKeys) {
          const lowerKey = key.toLowerCase();
          // Skip the nutrient name column
          if (lowerKey.includes('nutrient') || lowerKey === 'nutrients') continue;

          // Look for serving-related columns
          if (lowerKey.includes('per ') || lowerKey.includes('serving') || lowerKey.match(/\d+\s*(g|gram|ml)/i)) {
            valueColumnKey = key;
            servingSizeLabel = key;

            // Try to extract grams from the column name
            const gramsMatch = key.match(/(\d+)\s*(g|gram)/i);
            if (gramsMatch) {
              servingSizeGrams = parseFloat(gramsMatch[1]);
            }
            break;
          }
        }

        // If we found a value column, extract the data
        if (valueColumnKey) {
          rawTable.forEach((row: any) => {
            const nutrientKey = row.Nutrients || row.nutrients || row.Nutrient;
            const value = row[valueColumnKey];

            if (nutrientKey && value !== undefined && value !== null) {
              const numericValue = typeof value === 'string'
                ? parseFloat(value.replace(/[^0-9.]/g, ''))
                : value;

              if (!isNaN(numericValue)) {
                const cleanKey = nutrientKey.toLowerCase().trim();
                if (cleanKey.includes('energy') || cleanKey.includes('calories')) {
                  extractedValues.calories = numericValue;
                } else if (cleanKey.includes('protein')) {
                  extractedValues.protein = numericValue;
                } else if (cleanKey === 'carbohydrate' || cleanKey.includes('carb')) {
                  extractedValues.totalCarbohydrates = numericValue;
                } else if (cleanKey.includes('total fat') || cleanKey === 'total fat') {
                  extractedValues.totalFat = numericValue;
                } else if (cleanKey.includes('saturated')) {
                  extractedValues.saturatedFat = numericValue;
                } else if (cleanKey.includes('trans')) {
                  extractedValues.transFat = numericValue;
                } else if (cleanKey.includes('fiber') || cleanKey.includes('fibre')) {
                  extractedValues.dietaryFiber = numericValue;
                } else if (cleanKey.includes('added sugar')) {
                  extractedValues.addedSugars = numericValue;
                } else if (cleanKey.includes('sugar')) {
                  extractedValues.sugars = numericValue;
                } else if (cleanKey.includes('sodium')) {
                  extractedValues.sodium = numericValue;
                } else if (cleanKey.includes('cholesterol')) {
                  extractedValues.cholesterol = numericValue;
                }
              }
            }
          });
        }
      }

      // Extract package size from extras.netWeight
      let packageSizeGrams: number | null = null;
      if (extras?.netWeight) {
        const match = extras.netWeight.match(/([0-9.]+)\s*(g|gram)/i);
        if (match) {
          packageSizeGrams = parseFloat(match[1]);
        }
      }

      return {
        nutritionData: {
          ...(nutritionData as any),
          percentRDA,
          rawTable,
          extras,
          extractedValues: Object.keys(extractedValues).length > 0 ? extractedValues : undefined,
          extractedServingSize: servingSizeGrams,
          extractedServingLabel: servingSizeLabel,
          packageSizeGrams
        } as any,
        rawText: content,
      };
    } catch (error: any) {
      console.error('Vision processing failed:', error);
      const msg = error?.message || String(error);
      if (error?.code === 'mismatched_organization' || msg.includes('OpenAI-Organization')) {
        throw new Error(
          'OpenAI organization mismatch: please remove or correct OPENAI_ORG_ID in .env.local so it matches your API key, then restart the server.'
        );
      }
      throw new Error(msg);
    }
  }
}