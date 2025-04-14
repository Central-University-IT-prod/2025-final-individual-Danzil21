import json
import re


def extract_json_to_dict(text):
    json_pattern = r'\{[^{}]*\}'
    match = re.search(json_pattern, text)

    if match:
        json_str = match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            corrected_json_str = re.sub(r'\bTrue\b', 'true', json_str)
            corrected_json_str = re.sub(r'\bFalse\b', 'false', corrected_json_str)
            try:
                return json.loads(corrected_json_str)
            except json.JSONDecodeError:
                print("Ошибка при разборе JSON после исправления.")
                return None
    else:
        print("JSON не найден в тексте.")
        return None
