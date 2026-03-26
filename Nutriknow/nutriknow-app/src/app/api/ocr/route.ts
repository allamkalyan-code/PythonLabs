import { NextResponse } from 'next/server';
import { VisionService } from '@/services/visionService';

// Initialize vision service
const visionService = new VisionService();

export async function POST(request: Request) {
  try {
    // Verify request is multipart/form-data
    const contentType = request.headers.get('content-type');
    if (!contentType?.includes('multipart/form-data')) {
      return NextResponse.json(
        { error: 'Request must be multipart/form-data' },
        { status: 400 }
      );
    }

    // Get the form data
    const formData = await request.formData();
    const imageFile = formData.get('image') as File | null;

    if (!imageFile) {
      return NextResponse.json(
        { error: 'No image file provided' },
        { status: 400 }
      );
    }

    // Convert File to Buffer for processing
    const buffer = Buffer.from(await imageFile.arrayBuffer());

    // Process with Vision LLM
    const result = await visionService.processNutritionLabel(buffer);

    return NextResponse.json({
      success: true,
      ...result
    });
  } catch (err) {
    console.error('OCR route error:', err);
    const message = err instanceof Error ? err.message : 'OCR processing failed';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
