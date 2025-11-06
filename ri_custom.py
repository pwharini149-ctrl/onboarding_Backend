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
