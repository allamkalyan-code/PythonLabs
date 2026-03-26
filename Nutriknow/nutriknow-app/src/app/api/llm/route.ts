import { NextResponse } from 'next/server';
import { analyzeNutritionFacts } from '@/services/scoring';
import { VisionService } from '@/services/visionService';

const vision = new VisionService();

export async function POST(request: Request) {
  try {
    const contentType = request.headers.get('content-type') || '';

    let nutritionData: any = null;
    let rawText = '';
    let userAllergens: string[] = [];

    if (contentType.includes('multipart/form-data')) {
      // Handle image upload
      const formData = await request.formData();
      const imageFile = formData.get('image') as File | null;
      const allergens = formData.get('userAllergens') as string | null;
      if (allergens) {
        try { userAllergens = JSON.parse(allergens); } catch { userAllergens = []; }
      }

      if (!imageFile) {
        return NextResponse.json({ error: 'No image provided' }, { status: 400 });
      }

      const buffer = Buffer.from(await imageFile.arrayBuffer());
      const result = await vision.processNutritionLabel(buffer);
      nutritionData = result.nutritionData;
      rawText = result.rawText;
    } else {
      // Expect JSON body with nutrition data
      const body = await request.json();
      nutritionData = body;
      userAllergens = body.userAllergens || [];
    }

    const analysis = analyzeNutritionFacts(nutritionData, userAllergens);

    // Build a prompt that includes the full parsed table and extras so the LLM can reference them
    const promptParts = [];
    promptParts.push(`You are a helpful nutritionist explaining nutrition facts to a general audience. Keep explanations clear but informative, focusing on the most important health aspects.`);
    promptParts.push(`NutritionData: ${JSON.stringify(nutritionData)}`);
    if ((nutritionData as any).rawTable) {
      promptParts.push(`RawTable: ${JSON.stringify((nutritionData as any).rawTable)}`);
    }
    if ((nutritionData as any).extras) {
      promptParts.push(`Extras: ${JSON.stringify((nutritionData as any).extras)}`);
    }
    promptParts.push(`Analysis Score: ${analysis.score}/100`);
    promptParts.push(`Key Insights: ${analysis.insights.join('; ')}`);
    promptParts.push(`Normalized (per 100g): Calories ${analysis.servingNormalized.calories}, Protein ${analysis.servingNormalized.protein}, Added Sugar ${analysis.servingNormalized.addedSugars || 0}, Saturated Fat ${analysis.servingNormalized.saturatedFat}`);
    promptParts.push(`When present, mention %RDA per serving values and highlight anything >=30% of daily value. Also mention any ingredient warnings or footnotes present in Extras.`);

    // Ask the LLM for a helpful explanation using the parsed table as reference
    const explanationResponse = await vision.openai.chat.completions.create({
      model: 'gpt-4',
      messages: [
        { role: 'system', content: 'You are a helpful nutritionist and communicator.' },
        { role: 'user', content: promptParts.join('\n\n') },
      ],
      max_tokens: 400,
      temperature: 0.7,
    });

    const explanation = explanationResponse.choices[0]?.message?.content ||
      `This item has about ${analysis.servingNormalized.calories} kcal per 100g; score ${analysis.score}/100. ${analysis.insights.join(' ')}`;

    return NextResponse.json({
      success: true,
      explanation,
      rawText,
      nutritionData, // Include full nutrition data for debugging
      parsedRawTable: (nutritionData as any).rawTable,
      extras: (nutritionData as any).extras,
      debugOutput: process.env.NODE_ENV !== 'production' ? {
        visionRawText: rawText,
        explanationRawText: explanationResponse.choices[0]?.message?.content,
      } : undefined,
      ...analysis,
    });
  } catch (error: any) {
    console.error('API Error Details:', error);
    return NextResponse.json(
      {
        error: 'Processing failed',
        details: error.message,
        stack: error.stack
      },
      { status: 500 }
    );
  }
}
