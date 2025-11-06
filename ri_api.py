from flask import Flask, request, render_template, jsonify
import json
from xml.dom import minidom
from flask_cors import CORS

from ri_beans import ri_outer_beans_file, ri_gl_beans_file
from ri_custom import read_properties_file
from ri_matching import  ri_gl_matching_file

# ---------- CONFIG ----------
OUTER_BEANS_TEMPLATE = "RI/Templates/ri_outerbeans.xml"
OUTER_CUSTOM = "RI/Templates/ri_custom.properties"
INNER_CUSTOM = "RI\Templates\gl_ri_custom.properties"
# ----------------------------

app = Flask(__name__)
CORS(app)

def pretty_format(xml_string):
    """Return formatted XML with indentation but without extra blank lines."""
    try:
        parsed = minidom.parseString(xml_string)
        pretty = parsed.toprettyxml(indent="    ")
        # Remove extra blank lines
        pretty_no_blanks = "\n".join([line for line in pretty.splitlines() if line.strip()])
        return pretty_no_blanks
    except Exception:
        return xml_string

@app.route("/")
def index():
    return render_template("result.html")

@app.route("/RI", methods=["POST"])
def ri_generate_files():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Please provide input json"}), 400

        xml_content = ri_gl_beans_file(data)
        # Generate beans XML from template
        beans_xml = ri_outer_beans_file(OUTER_BEANS_TEMPLATE, modifications=None)  # or pass modifications if needed
        outer_content = read_properties_file(OUTER_CUSTOM)
        inner_content = read_properties_file(INNER_CUSTOM)
        matching_content = ri_gl_matching_file(data)
        # Return JSON (will be rendered by JS)
        return jsonify({
            "matching rule": matching_content if matching_content else "",
            "xml": pretty_format(xml_content),
            "beans": pretty_format(beans_xml) if beans_xml else "",
            "outer_custom": outer_content if outer_content else "",
            "inner_custom": inner_content if inner_content else ""
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5001)
