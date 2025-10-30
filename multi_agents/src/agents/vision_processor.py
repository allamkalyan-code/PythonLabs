from typing import Dict, Any
import base64
from pathlib import Path
from openai import OpenAI
import os

class VisionProcessorAgent:
    def __init__(self):
        self.name = "Vision Processor Agent"
        self.description = "Agent responsible for processing images using GPT-4 Vision API"
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def _encode_image(self, image_path: Path) -> str:
        """Convert image to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def process_image(self, image_path: Path) -> Dict[str, Any]:
        """Process the image using GPT-4 Vision API to extract structured nutrition data"""
        try:
            # Encode image
            base64_image = self._encode_image(image_path)
            
            # Create the prompt for structured extraction
            prompt = """
            You are a precise nutrition label reader. Analyze this nutrition label image and extract:
            1. All nutrient values with their units and % Daily Value
            2. Serving size information
            3. Any additional nutrition information
            
            Return the data in this exact JSON format:
            {
                "serving": {"size": "amount and unit", "per_container": "number"},
                "items": [
                    {
                        "name": "nutrient name",
                        "amount": number,
                        "unit": "g/mg/mcg",
                        "pct_dv": number or null,
                        "raw": "original text as seen"
                    },
                    ...
                ]
            }
            
            Be precise with numbers and units. Include all visible nutrients.
            """
            
            # Call Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.2  # Lower temperature for more precise extraction
            )
            
            # Extract JSON response
            content = response.choices[0].message.content
            # Find JSON portion (between first { and last })
            json_str = content[content.find('{'):content.rfind('}')+1]
            
            # Use the existing NutritionParserAgent's structure
            import json
            parsed_data = json.loads(json_str)
            
            return {
                "status": "success",
                "text": content,  # Keep full text for compatibility
                "data": parsed_data,  # Structured data
                "error": None
            }
            
        except Exception as e:
            import traceback
            error_detail = f"Error: {str(e)}\nTrace:\n{traceback.format_exc()}"
            print(f"Vision API Error Details:\n{error_detail}")  # Debug print
            return {
                "status": "error",
                "text": None,
                "data": None,
                "error": error_detail
            }