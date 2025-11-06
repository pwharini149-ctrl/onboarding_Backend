import json
import xml.etree.ElementTree as ET
import io
from flask import jsonify, request


# ---------- CONFIG ----------
MAPPING_FILE = "AFM\Templates\gl_ri_mapping.json"
DETAILS_FILE = "AFM\Templates\gl_ri_beans.json"
BASE_FILE = "AFM/Templates/gl_ri_base.xml"
OUTER_BEANS_TEMPLATE = "AFM/Templates/ri_outerbeans.xml"
# ----------------------------

def load_json(path):
    """Load JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
    
def ri_outer_beans_file(template_path, modifications=None):
    """
    Generates XML content as a string based on a template.

    :param template_path: Path to afm_outerbeans.xml template
    :param modifications: Optional dict of {tag_name: new_value} to modify elements
    :return: XML content as a string
    """
    try:
        # Parse the XML template
        tree = ET.parse(template_path)
        root = tree.getroot()

        # Apply modifications if provided
        if modifications:
            for tag_name, new_value in modifications.items():
                for elem in root.iter(tag_name):
                    elem.text = new_value

        # Convert the XML tree to a string
        xml_io = io.BytesIO()
        tree.write(xml_io, encoding='utf-8', xml_declaration=True)
        xml_content = xml_io.getvalue().decode('utf-8')

        return xml_content

    except Exception as e:
        print(f"Error generating XML: {e}")
        return None


def ri_gl_beans_file(data):
    try:
        data = request.get_json(force=True)
        if not data or "match_keys" not in data:
            return jsonify({"error": "Missing 'match_keys'"}), 400

        match_keys = [k.strip() for k in data["match_keys"] if k.strip()]
        if not match_keys:
            return jsonify({"error": "No valid search keys provided"}), 400

        # Load mapping & details
        mapping_data = load_json(MAPPING_FILE)
        details_data = load_json(DETAILS_FILE)

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

        # Build <util:list>
        util_block = '<util:list id="queryConfigs" list-class="java.util.ArrayList">'
        for cfg in selected_configs:
            util_block += f'<ref bean="{cfg}" />'
        util_block += '</util:list>' + '\n'

        # Build generator beans
        generator_block = ""
        for cfg in selected_configs:
            snippet = config_to_snippet.get(cfg, "").strip()
            if snippet:
                generator_block +=snippet.strip()

        # Load base.xml
        with open(BASE_FILE, encoding="utf-8") as f:
            base_template = f.read()
        final_xml = base_template.replace("<!-- UTIL_LIST_BLOCK -->", util_block.strip())
        final_xml = final_xml.replace("<!-- GENERATOR_BLOCK -->", generator_block.strip())

        return final_xml

    except Exception as e:
        return jsonify({"error": str(e)}), 500