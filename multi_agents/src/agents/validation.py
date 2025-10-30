from typing import Dict, Any, Optional
from openai import OpenAI

class ValidationAgent:
    def __init__(self, openai_api_key: str):
        self.name = "Validation Agent"
        self.description = "Agent responsible for verifying the accuracy of extracted information and explanations"
        self.client = OpenAI(api_key=openai_api_key)

    def validate_nutrition_data(self, original_text: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the parsed nutritional information against the original text
        """
        try:
            validation_results = {
                'consistency': self._check_consistency(original_text, parsed_data),
                'completeness': self._check_completeness(parsed_data),
                'reasonableness': self._check_reasonableness(parsed_data)
            }
            
            is_valid = all(validation_results.values())
            
            return {
                "status": "success",
                "is_valid": is_valid,
                "validation_details": validation_results,
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "is_valid": False,
                "validation_details": None,
                "error": str(e)
            }
    
    def _check_consistency(self, original_text: str, parsed_data: Dict[str, Any]) -> bool:
        """Check if parsed data is consistent with the original text"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"""Compare the following original text and parsed nutritional data.
                Are they consistent with each other?
                Answer only with true or false.
                
                Original text:
                {original_text}
                
                Parsed data:
                {parsed_data}"""
            }]
        )
        return response.choices[0].message.content.lower().strip() == 'true'
    
    def _check_completeness(self, parsed_data: Dict[str, Any]) -> bool:
        """Check if all expected nutritional information is present"""
        required_fields = ['calories', 'protein', 'carbohydrates', 'fat']
        # Support new parser shape where parsed_data has 'by_name'
        if isinstance(parsed_data, dict) and 'by_name' in parsed_data:
            by_name = parsed_data.get('by_name', {})
            for field in required_fields:
                if field not in by_name:
                    return False
                val = by_name[field]
                # val may be item dict or list
                if isinstance(val, dict):
                    if val.get('amount') is None:
                        return False
                elif isinstance(val, list):
                    # at least one with amount
                    if not any(v.get('amount') is not None for v in val if isinstance(v, dict)):
                        return False
            return True

        # fallback to old behavior
        return all(field in parsed_data and parsed_data[field] is not None for field in required_fields)
    
    def _check_reasonableness(self, parsed_data: Dict[str, Any]) -> bool:
        """Check if the nutritional values are within reasonable ranges"""
        def check_value(name: str, low: float, high: float, unit_hint: Optional[str] = None) -> bool:
            # Try to extract value from new parser format (by_name uses canonical keys)
            if isinstance(parsed_data, dict) and 'by_name' in parsed_data:
                v = parsed_data['by_name'].get(name)
                if v is None:
                    return True  # missing value shouldn't be treated as unreasonable here
                if isinstance(v, list):
                    # check first numeric
                    v = v[0]
                try:
                    amt = v.get('amount')
                except Exception:
                    return True
                if amt is None:
                    return True
                return low <= amt <= high
            # fallback to old shape
            val = parsed_data.get(name)
            if val is None:
                return True
            return low <= val <= high

        # per-serving reasonable ranges
        if not check_value('calories', 0, 1000):
            return False
        if not check_value('protein', 0, 100):
            return False
        if not check_value('carbohydrates', 0, 200):
            return False
        if not check_value('fat', 0, 100):
            return False

        return True