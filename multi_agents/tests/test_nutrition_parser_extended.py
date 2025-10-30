import unittest
from src.agents.nutrition_parser import NutritionParserAgent

class TestNutritionParserExtended(unittest.TestCase):
    def setUp(self):
        self.parser = NutritionParserAgent()
        self.sample_text = '''
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

    def test_canonical_keys_present(self):
        res = self.parser.parse_nutrition_text(self.sample_text)
        self.assertEqual(res['status'], 'success')
        by_name = res['data']['by_name']
        # Check canonical keys
        expected_keys = ['calories','fat','saturated_fat','trans_fat','cholesterol','sodium','carbohydrates','dietary_fiber','total_sugars','added_sugars','protein','vitamin_d','calcium','iron','potassium']
        for k in expected_keys:
            self.assertIn(k, by_name, msg=f"Expected canonical key {k} in by_name")

if __name__ == '__main__':
    unittest.main()
