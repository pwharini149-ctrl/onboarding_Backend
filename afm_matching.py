from flask import request


EAN_TEMPLATE = """DEFINE ATTRIBUTE SET target_attr AS
content,url

DEFINE MATCHING FUNCTION ID AS
TOKENIZER standard AND
TOKEN COMPARATORS exact

DEFINE RULE SET content_match_rule AS
simple_rule

DEFINE RULE simple_rule AS
ID MATCH ean WITH ATTRIBUTE SET target_attr USING THRESHOLD 0.1
"""

OTHER_TEMPLATE = """DEFINE MATCHING FUNCTION ID AS
TOKENIZER aggressive AND
TOKEN COMPARATORS exact

DEFINE ATTRIBUTE SET target_attr AS
content

DEFINE RULE SET content_match_rule AS 
simple_rule

DEFINE RULE simple_rule AS
ID MATCH item_name WITH ATTRIBUTE SET target_attr USING THRESHOLD 0.2
"""

def afm_gl_matching_file(data=None):
    """Generate TXT file based on whether EAN is selected."""
    try:
        # If called as Flask endpoint → use request.get_json()
        if data is None:
            data = request.get_json(force=True)

        # Extract keys
        selected_keys = data.get("search_keys", [])

        if any(key.upper() == "EAN" for key in selected_keys):
            return EAN_TEMPLATE
        else:
            return OTHER_TEMPLATE

    except Exception as e:
        print(f"Error generating TXT: {e}")
        return None

    