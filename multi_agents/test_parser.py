from src.agents.nutrition_parser import NutritionParserAgent

sample_text = '''
Serving Size 1 cup (240g)
Servings Per Container 2
Calories 240
Total Fat 8g 10% DV
Saturated Fat 2g 10% DV
Trans Fat 0g
Cholesterol 30mg 10% DV
Sodium 400mg 17% DV
Total Carbohydrate 34g 12% DV
Dietary Fiber 4g 14% DV
Total Sugars 12g
Includes 10g Added Sugars 20% DV
Protein 12g
Vitamin D 2mcg 10% DV
Calcium 130mg 10% DV
Iron 2.7mg 15% DV
Potassium 470mg 10% DV
''' 

parser = NutritionParserAgent()
res = parser.parse_nutrition_text(sample_text)
import json
print(json.dumps(res, indent=2))
