import unittest
from src.agents.nutrition_parser import NutritionParserAgent

class TestNutritionParser(unittest.TestCase):
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

    def test_parse_items_present(self):
        res = self.parser.parse_nutrition_text(self.sample_text)
        self.assertEqual(res['status'], 'success')
        data = res['data']
        self.assertIn('items', data)
        items = data['items']
        # Expect at least calories, protein, fat, carbs to be present
        names = [it['name'] for it in items if it.get('name')]
        self.assertTrue(any('calories' in n for n in names))
        self.assertTrue(any('protein' in n for n in names))
        self.assertTrue(any('fat' in n for n in names) or any('total fat' in n for n in names))
        self.assertTrue(any('carbohydrate' in n for n in names) or any('carbs' in n for n in names))

if __name__ == '__main__':
    unittest.main()
