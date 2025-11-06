# txt_generator.py
import json
from flask import jsonify, request

# ---------- CONFIG ----------
MAPPING_FILE = "AFM\Templates\gl_ri_mapping.json"
MATCHING_FILE = "AFM\Templates\gl_ri_matching.json"
TEMPLATE_FILE = "AFM/Templates/gl_ri_matching.txt"
# ----------------------------

def load_json(path):
    """Load JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
    
    
def ri_gl_matching_file(data):
    """Generate TXT file based on whether EAN is selected."""
    try:
        data = request.get_json(force=True)
        if not data or "match_keys" not in data:
            return jsonify({"error": "Missing 'match_keys'"}), 400

        match_keys = [k.strip() for k in data["match_keys"] if k.strip()]
        if not match_keys:
            return jsonify({"error": "No valid search keys provided"}), 400

        # Load mapping & details
        mapping_data = load_json(MAPPING_FILE)
        details_data = load_json(MATCHING_FILE)

        search_to_config = {m["match_key"]: m["config_name"] for m in mapping_data}
        config_to_snippet = {d["config_name"]: d["generator_snippet"] for d in details_data}

        # Normalize keys
        valid_keys = []
        for key in match_keys:
            match = next((k for k in search_to_config if k.lower() == key.lower()), None)
            if match:
                valid_keys.append(match)
        valid_keys = list(dict.fromkeys(valid_keys))

        if not valid_keys:
            return jsonify({"error": "No valid search keys found"}), 400

        selected_configs = [search_to_config[k] for k in valid_keys]

        print(selected_configs)
        # Build generator beans
        generator_block = ""
        for cfg in selected_configs:
            snippet = config_to_snippet.get(cfg, "").strip()
            if snippet:
                generator_block += "\n" + snippet + "\n"

        # Load base.xml
        with open(TEMPLATE_FILE, encoding="utf-8") as f:
            base_template = f.read()
        final_xml = base_template.replace("<!-- GENERATOR_BLOCK -->", generator_block.strip())

        return final_xml
        

    except Exception as e:
        return jsonify({"error": str(e)}), 500