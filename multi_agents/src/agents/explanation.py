from typing import Dict, Any
from openai import OpenAI

class ExplanationAgent:
    def __init__(self, openai_api_key: str):
        self.name = "Explanation Agent"
        self.description = "Agent responsible for converting technical nutritional information into easy-to-understand explanations"
        self.client = OpenAI(api_key=openai_api_key)

    def explain_nutrition(self, nutrition_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert technical nutritional information into easy-to-understand explanations.

        Supports both the previous flat dict format (calories/protein/...) and
        the new parser output which has an `items` list.
        """
        try:
            explanation = {}

            # Support both old-style flat dicts (calories/protein/...) and new parser output
            items = None
            if isinstance(nutrition_data, dict) and 'items' in nutrition_data:
                items = nutrition_data['items']
            else:
                # attempt to convert old-style dict into items list
                items = []
                for key in ['calories', 'protein', 'carbohydrates', 'fat']:
                    if nutrition_data.get(key) is not None:
                        items.append({'name': key, 'amount': nutrition_data.get(key), 'unit': None, 'pct_dv': None, 'raw': key})

            # For each detected item, ask the LLM to produce a short explanation
            for it in items:
                # support both new and old item formats
                key = it.get('key') or it.get('name')
                label = it.get('name') or key
                amount = it.get('amount')
                unit = it.get('unit')
                prompt_amount = f"{amount}{unit or ''}" if amount is not None else label
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "user",
                        "content": f"Explain {prompt_amount} of {label} in simple terms for a general audience. Keep it short and use an everyday comparison when possible."
                    }]
                )
                explanation[key] = response.choices[0].message.content

            # Generate an overall summary from the items
            summary_prompt = "Create a brief, easy-to-understand summary of the following nutrition items:\n"
            for it in items:
                summary_prompt += f"- {it.get('raw')}\n"

            summary_resp = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": summary_prompt}]
            )
            summary = summary_resp.choices[0].message.content

            return {
                "status": "success",
                "explanation": explanation,
                "summary": summary,
                "error": None
            }
        except Exception as e:
            return {
                "status": "error",
                "explanation": None,
                "summary": None,
                "error": str(e)
            }
    
    def _explain_calories(self, calories: float) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Explain {calories} calories in simple terms that anyone can understand. Keep it brief and use everyday comparisons when possible."
            }]
        )
        return response.choices[0].message.content
    
    def _explain_protein(self, protein: float) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Explain {protein}g of protein in simple terms that anyone can understand. Keep it brief and use everyday comparisons when possible."
            }]
        )
        return response.choices[0].message.content
    
    def _explain_carbs(self, carbs: float) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Explain {carbs}g of carbohydrates in simple terms that anyone can understand. Keep it brief and use everyday comparisons when possible."
            }]
        )
        return response.choices[0].message.content
    
    def _explain_fat(self, fat: float) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Explain {fat}g of fat in simple terms that anyone can understand. Keep it brief and use everyday comparisons when possible."
            }]
        )
        return response.choices[0].message.content
    
    def _generate_summary(self, nutrition_data: Dict[str, Any]) -> str:
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Create a brief, easy-to-understand summary of this nutritional information:\n{nutrition_data}\nFocus on the most important aspects and explain it in a way that anyone can understand."
            }]
        )
        return response.choices[0].message.content