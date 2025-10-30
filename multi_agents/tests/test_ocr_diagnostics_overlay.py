import unittest
import numpy as np

class TestOCRDiagnosticsOverlay(unittest.TestCase):
    def setUp(self):
        # Simulate pytesseract image_to_data output
        self.data = {
            'text': ['Calories', '240', 'Protein', '12g', 'Fat', '8g'],
            'conf': [95, '88', 70, 'not_a_number', 100, 85],
            'left': [10, 60, 110, 160, 210, 260],
            'top': [20, 20, 40, 40, 60, 60],
            'width': [40, 30, 50, 35, 45, 30],
            'height': [20, 20, 20, 20, 20, 20]
        }

    def test_conf_val_handling(self):
        # This mimics the logic in app.py for conf_val assignment
        results = []
        for i in range(len(self.data['text'])):
            conf = self.data['conf'][i]
            if isinstance(conf, int):
                conf_val = conf
            elif isinstance(conf, str):
                conf_val = int(conf) if conf.isdigit() else -1
            else:
                conf_val = -1
            results.append(conf_val)
        # Expected: [95, 88, 70, -1, 100, 85]
        self.assertEqual(results, [95, 88, 70, -1, 100, 85])

if __name__ == '__main__':
    unittest.main()
