import json
import re

def fix_multiline_strings(s):
        lines = s.split('\n')
        new_lines = []
        buffer = ""
        in_string = False

        for line in lines:
            line = line.rstrip()
            quote_count = line.count('"')
            if not in_string:
                buffer = line
                if quote_count % 2 == 1:  # Odd number of quotes -> string not closed
                    in_string = True
                else:
                    new_lines.append(buffer)
            else:
                buffer += ' ' + line
                if quote_count % 2 == 1:
                    new_lines.append(buffer)
                    in_string = False

        if in_string:
            new_lines.append(buffer)  # Last incomplete line
        return "\n".join(new_lines)

def extract_dict_from_text(text):
    # Extract the code block
    match = re.search(r"```(?:python)?\s*({.*?})\s*```", text, re.DOTALL)
    if not match:
        match = re.search(r"({.*})", text, re.DOTALL)
    if not match:
        return None

    dict_str = match.group(1)

    # Step 1: Replace unescaped line breaks inside strings
    
    dict_str = fix_multiline_strings(dict_str)

    # Step 2: Try parsing as JSON
    try:
        return json.loads(dict_str)
    except json.JSONDecodeError as je:
        print("JSON decode error:", je)
        return None
