import json
import os
from flask import jsonify, request
import requests
from urllib.parse import urlparse, urlencode, urljoin
import xml.etree.ElementTree as ET

# ---------- AFM CONFIG ----------
OUTER_CUSTOM_DATAPOINTS= "AFM/Templates/afm_custom_properties.json"
OUTER_CUSTOM_TEMPLATE = "AFM/Templates/afm_custom.properties"
# ----------------------------


def prettify_xml(elem):
    """Return pretty formatted XML string."""
    from xml.dom import minidom
    rough_string = ET.tostring(elem, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def read_properties_file(file_path):
    """
    Reads a .properties file and returns its content as a string.

    :param file_path: Path to the .properties file
    :return: File content as string
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error reading properties file: {e}")
        return None

# Main function to accept JSON input
def afm_gl_custom_file(data):
    """
    data: dict containing 'website_url', 'Comp_name', 'Search_xpath'
    Returns: dict with updated properties content and search link
    """
    search_link = data.get("website_url")
    comp_name = data.get("Comp_name")
    search_xpath = data.get("Search_xpath")

    if not search_link:
        return {"error": "Missing website_url"}
    if not comp_name:
        return {"error": "Missing Comp_name"}
    if not search_xpath:
        return {"error": "Missing Search_xpath"}

    # search_link = get_search_url(website_url)
    # if not search_link:
    #     return {"error": "No working search link found"}

    # Read base properties template file
    with open(r"AFM/Templates/gl_afm_custom.properties", "r", encoding="utf-8") as f:
        properties_content = f.read()

    # Update template
    updated_content = update_properties_content(properties_content, search_link, comp_name, search_xpath)
    return updated_content

# Function to get search link (tries multiple patterns with "black")
def get_search_url(competitor_url, keyword="black"):
    parsed = urlparse(competitor_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    patterns = [
        f"/search?{urlencode({'q': keyword})}",
        f"/search?q={keyword}",
        f"/s?{urlencode({'k': keyword})}",
        f"/search?{urlencode({'query': keyword})}",
        f"/catalogsearch/result/?{urlencode({'q': keyword})}",
        f"/search/{keyword}",
        f"/search?search={keyword}",
        f"/search-results?q={keyword}",
        f"/q-{keyword}"
    ]

    for path in patterns:
        search_url = urljoin(base_url, path)
        try:
            r = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if r.status_code == 200 and keyword.lower() in r.text.lower():
                return search_url
            else:
                search_url = ""  # Reset if not valid
                return search_url
        except Exception:
            continue
    return None


# Function to update properties content dynamically
def update_properties_content(properties_content, search_link, comp_name, search_xpath, keyword="black"):
    invalid_queries_url = search_link.replace(keyword, "")
    default_query_template = search_link.replace(keyword, "${keywords}")

    updated_lines = []
    for line in properties_content.splitlines():
        if line.startswith("DEFAULT_QUERY_TEMPLATE="):
            updated_lines.append(f"DEFAULT_QUERY_TEMPLATE={default_query_template}")
        elif line.startswith("INVALID_QUERIES="):
            updated_lines.append(f"INVALID_QUERIES={invalid_queries_url}")
        elif line.startswith("SEARCH_VALIDATION_URL="):
            updated_lines.append(f"SEARCH_VALIDATION_URL={search_link}")
        elif line.startswith("WEBSITE_NAME_IN_DB="):
            updated_lines.append(f"WEBSITE_NAME_IN_DB={comp_name}")
        elif line.startswith("SEARCH_RECORD_XPATH="):
            updated_lines.append(f"SEARCH_RECORD_XPATH={search_xpath}")
        else:
            updated_lines.append(line)
    return "\n".join(updated_lines)



def afm_outer_custom(data):
    """Generate .properties style text dynamically based on selected search_keys."""
    try:
        # Ensure JSON input
        if isinstance(data, dict):
            request_data = data
        else:
            request_data = request.get_json(force=True)

        if not request_data or "search_keys" not in request_data:
            return {"error": "Missing 'search_keys'"}

        search_keys = [k.strip() for k in request_data["search_keys"] if k.strip()]

        # --- Load your mapping JSON ---
        with open(OUTER_CUSTOM_DATAPOINTS, "r", encoding="utf-8") as f:
            mappings = json.load(f)

        mapping_dict = {item["search_key"].lower(): item["config_name"] for item in mappings}

        # --- Read the static .properties file header ---
        with open(OUTER_CUSTOM_TEMPLATE, "r", encoding="utf-8") as f:
            base_properties = f.read().strip()

        # --- Dynamically append lines for selected search keys ---
        dynamic_lines = []
        for selection in search_keys:
            key = selection.lower()
            if key in mapping_dict:
                config_name = mapping_dict[key]
                dynamic_lines.append(f"dataPoint.{config_name}.xpath=")
            else:
                print(f"⚠️ No mapping found for '{selection}'")

        # --- Combine the base and dynamic sections ---
        full_properties = base_properties + "\n\n" + "\n".join(dynamic_lines)

        return full_properties

    except Exception as e:
        return {"error": str(e)}
