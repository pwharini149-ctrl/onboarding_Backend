import time
from flask import Flask, request, render_template, jsonify
import json
from xml.dom import minidom
from flask_cors import CORS

from ri_beans import ri_gl_beans_file, ri_outer_beans_file
from ri_matching import ri_gl_matching_file
from afm_beans import afm_gl_beans_file, afm_outer_beans_file
from afm_custom import afm_outer_custom, read_properties_file,afm_gl_custom_file
from afm_matching import afm_gl_matching_file

# ---------- AFM CONFIG ----------
OUTER_BEANS_TEMPLATE = "AFM/Templates/afm_outerbeans.xml"
OUTER_CUSTOM = "AFM/Templates/afm_custom.properties"
OUTER_CUSTOM_DATAPOINTS= "AFM/Templates/afm_custom_properties.json"
# ----------------------------

# ---------- RI CONFIG ----------
OUTER_BEANS_TEMPLATE1 = "AFM/Templates/ri_outerbeans.xml"
OUTER_CUSTOM1 = "AFM/Templates/ri_custom.properties"
INNER_CUSTOM1 = "AFM/Templates/gl_ri_custom.properties"

# ----------------------------

app = Flask(__name__)
CORS(app)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def pretty_format(xml_string):
    """Return formatted XML with indentation but without extra blank lines."""
    try:
        parsed = minidom.parseString(xml_string)
        pretty = parsed.toprettyxml(indent="    ")
        
        pretty_no_blanks = "\n".join([line for line in pretty.splitlines() if line.strip()])
        return pretty_no_blanks
    except Exception:
        return xml_string
    
@app.route("/")
def index():
    return render_template("result.html")

@app.route("/AFM", methods=["POST"])
def afm_generate_files():
    start_time = time.time()   # ⏱ start timer
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Please provide input json"}), 400

        xml_content = afm_gl_beans_file(data)
        txt_content = afm_gl_matching_file(data)
        print("TXT CONTENT", txt_content)

        beans_xml = afm_outer_beans_file(OUTER_BEANS_TEMPLATE, modifications=None)  
        outer_content= afm_outer_custom(data)
        inner_custom_updated = afm_gl_custom_file(data) 
        
        elapsed = round(time.time() - start_time, 3)
        print(f"⏱ gl_matching_file executed in {elapsed} ms")

        return jsonify({
            "AFM_inner_beans": pretty_format(xml_content),
            "AFM_inner_matching": txt_content,
            "AFM_outer_beans": pretty_format(beans_xml) if beans_xml else "",
            "AFM_outer_custom" : outer_content if outer_content else "",
            "AFM_inner_custom": inner_custom_updated if inner_custom_updated else "",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/RI", methods=["POST"])
def ri_generate_files():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Please provide input json"}), 400

        xml_content = ri_gl_beans_file(data)
        # Generate beans XML from template
        beans_xml = ri_outer_beans_file(OUTER_BEANS_TEMPLATE1, modifications=None)  # or pass modifications if needed
        outer_content = read_properties_file(OUTER_CUSTOM1)
        inner_content = read_properties_file(INNER_CUSTOM1)
        matching_content = ri_gl_matching_file(data)
        # Return JSON (will be rendered by JS)
        return jsonify({
            "RI_inner_matching": matching_content if matching_content else "",
            "RI_inner_beans": pretty_format(xml_content) if xml_content else "",
            "RI_outer_beans": pretty_format(beans_xml) if beans_xml else "",
            "RI_outer_custom": outer_content if outer_content else "",
            "RI_inner_custom": inner_content if inner_content else ""
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
