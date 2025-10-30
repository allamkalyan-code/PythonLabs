from typing import Dict, Any, List
import re
import os
from typing import Optional

try:
    # import optional OpenAI client; keep optional to avoid hard dependency at runtime
    from openai import OpenAI
except Exception:
    OpenAI = None


class NutritionParserAgent:
    """Parse OCR'd nutrition label text into structured, dynamic nutrient items.

    Returns a dict with:
      - status: 'success'|'error'
      - data: {
          'items': [ {name, amount, unit, pct_dv, raw} ... ],
          'by_name': { name: item, ... },
          'serving': optional serving string or None
        }
      - error: error message or None

    The parser is intentionally permissive: it extracts any lines with numeric
    values (and units) and treats other lines as informational entries. This
    allows handling labels with more or fewer nutrients dynamically.
    """

    def __init__(self):
        self.name = "Nutrition Parser Agent"
        self.description = "Agent responsible for parsing and structuring nutritional information"

    def parse_nutrition_text(self, text: str, use_llm: bool = False, llm_model: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not text:
                return {"status": "success", "data": {"items": [], "by_name": {}, "serving": None}, "error": None}

            # If requested and available, use an LLM to parse the text into structured JSON
            if use_llm:
                # require OpenAI client and API key
                api_key = os.environ.get('OPENAI_API_KEY')
                if not api_key:
                    return {"status": "error", "data": None, "error": "OPENAI_API_KEY not set in environment for LLM parsing"}
                if OpenAI is None:
                    return {"status": "error", "data": None, "error": "openai client library not available"}

                model = llm_model or "gpt-3.5-turbo"
                llm_result = self._parse_with_llm(text, api_key, model)
                return llm_result

            # Normalize line endings and split into meaningful fragments
            # Some OCR outputs place multiple nutrients on a single line separated by ';' or ','
            raw_lines = []
            for line in text.splitlines():
                if not line:
                    continue
                # split by semicolon when multiple items are on one line
                parts = re.split(r'\s*;\s*', line)
                for p in parts:
                    # further split by ' - ' or ' — ' if present
                    subparts = re.split(r'\s[\-–—]\s', p)
                    for sp in subparts:
                        cleaned = sp.strip()
                        if cleaned:
                            raw_lines.append(cleaned)

            items: List[Dict[str, Any]] = []
            by_name: Dict[str, Any] = {}
            serving = None

            # regex to find a numeric value and optional unit or %
            num_unit_re = re.compile(r"(?P<number>\d+[\d,\.]*)(?:\s*(?P<unit>mg|g|mcg|µg|ug|kcal|cal|kj|iu|%))?", re.I)
            pct_re = re.compile(r"(?P<pct>\d+)%")

            for line in raw_lines:
                ln = line.strip()
                # detect serving info
                if re.search(r'serving', ln, re.I):
                    serving = ln
                    continue

                # find first numeric occurrence
                m = num_unit_re.search(ln)
                if m:
                    number = m.group('number')
                    # normalize number (commas to dots when needed)
                    number_norm = number.replace(',', '.')
                    try:
                        amount = float(number_norm)
                    except ValueError:
                        amount = None

                    unit = m.group('unit')
                    if unit:
                        unit = unit.lower()
                        if unit == 'cal':
                            unit = 'kcal'

                    # percent DV may appear later in line or as separate parenthetical
                    pct = None
                    pct_m = pct_re.search(ln)
                    if pct_m:
                        pct = int(pct_m.group('pct'))

                    # name is the part of the line before the matched number
                    name_part = ln[:m.start()].strip(' :-.')
                    label = self._normalize_label(name_part)
                    key = self._canonical_key(label)

                    item = {
                        'name': label,         # human readable label
                        'key': key,            # canonical machine key
                        'amount': amount,
                        'unit': unit,
                        'pct_dv': pct,
                        'raw': ln
                    }
                    items.append(item)
                    # For convenience, store by_name keyed by canonical key; if duplicates, make list
                    if key in by_name:
                        existing = by_name[key]
                        if isinstance(existing, list):
                            existing.append(item)
                        else:
                            by_name[key] = [existing, item]
                    else:
                        by_name[key] = item
                else:
                    # no numeric value found; include as informational entry
                    label = self._normalize_label(ln)
                    key = self._canonical_key(label)
                    item = {'name': label, 'key': key, 'amount': None, 'unit': None, 'pct_dv': None, 'raw': ln}
                    items.append(item)
                    if key not in by_name:
                        by_name[key] = item

            data = {'items': items, 'by_name': by_name, 'serving': serving}

            return {"status": "success", "data": data, "error": None}
        except Exception as e:
            return {"status": "error", "data": None, "error": str(e)}

    def _normalize_name(self, s: str) -> str:
        """Normalize nutrient/information names into a consistent key.
        Lowercase, strip extra words and collapse spaces.
        """
        s = s.lower().strip()
        # remove common trailing words
        s = re.sub(r"\s*per serving$", '', s)
        s = re.sub(r"[^a-z0-9 %()\-+/\.]+", ' ', s)
        s = re.sub(r"\s+", ' ', s)
        return s.strip()

    def _normalize_label(self, s: str) -> str:
        """Return a cleaned, human-readable label (lowercase, cleaned punctuation).
        This is used as the display name for items.
        """
        return self._normalize_name(s)

    # A small canonicalization mapping from common label variants to stable keys
    CANONICAL_MAP = {
        r"^calor(?:ies)?$": 'calories',
        r"^calories$": 'calories',
        r"^total fat$": 'fat',
        r"^fat$": 'fat',
        r"^saturated fat$": 'saturated_fat',
        r"^trans fat$": 'trans_fat',
        r"^cholesterol$": 'cholesterol',
        r"^sodium$": 'sodium',
        r"^total carbohydrate$": 'carbohydrates',
        r"^carbohydrate$": 'carbohydrates',
        r"^carbohydrates$": 'carbohydrates',
        r"^dietary fiber$": 'dietary_fiber',
        r"^total sugars$": 'total_sugars',
        r"added sugars$": 'added_sugars',
        r"^includes$": 'added_sugars',
        r"^protein$": 'protein',
        r"^vitamin d$": 'vitamin_d',
        r"^calcium$": 'calcium',
        r"^iron$": 'iron',
        r"^potassium$": 'potassium',
    }

    def _canonical_key(self, label: str) -> str:
        """Map a normalized label to a canonical key using CANONICAL_MAP.
        Falls back to a snake_case version of the label.
        """
        nl = label.lower().strip()
        for pat, key in self.CANONICAL_MAP.items():
            if re.search(pat, nl):
                return key
        # fallback: convert spaces to underscores and remove percent signs
        key = re.sub(r"[^a-z0-9]+", '_', nl).strip('_')
        return key

    def _parse_with_llm(self, text: str, api_key: str, model: str) -> Dict[str, Any]:
        """Use an LLM to extract structured nutrition items from OCR text.

        The LLM is asked to return a JSON object with `items` (list of {name, amount, unit, pct_dv, raw}),
        and optional `serving`.
        """
        try:
            client = OpenAI(api_key=api_key)
            prompt = (
                "You are given raw OCR text from a nutrition facts label. \n"
                "Extract every nutrition line and return JSON with two keys: `serving` (string or null) and `items` (array).\n"
                "Each item must be an object with: `name` (string), `amount` (number or null), `unit` (string or null), `pct_dv` (number or null), `raw` (original line).\n"
                "Do not include any explanation. Respond ONLY with valid JSON.\n\n"
                "Here is the text:\n" + text
            )

            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            content = resp.choices[0].message.content

            # Parse JSON from the model output robustly
            import json
            try:
                parsed = json.loads(content)
            except Exception:
                # try to find JSON substring
                import re as _re
                m = _re.search(r"(\{[\s\S]*\})", content)
                if not m:
                    return {"status": "error", "data": None, "error": "LLM did not return JSON"}
                parsed = json.loads(m.group(1))

            # Basic validation and normalization
            items = parsed.get('items', [])
            by_name = {}
            for it in items:
                key = self._normalize_name(it.get('name', ''))
                by_name[key] = it

            data = {'items': items, 'by_name': by_name, 'serving': parsed.get('serving')}
            return {"status": "success", "data": data, "error": None}
        except Exception as e:
            return {"status": "error", "data": None, "error": str(e)}