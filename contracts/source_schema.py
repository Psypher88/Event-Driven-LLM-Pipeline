def validate(data):
    # Purpose: check that a source output dict has all required fields
    # Input: data (dict) - the source output to validate
    # Output: (bool) True if valid, False if any required field is missing or malformed

    if "source_name" not in data:
        print("source_schema: missing field 'source_name'")
        return False

    if "fetched_at" not in data:
        print("source_schema: missing field 'fetched_at'")
        return False

    if "items" not in data:
        print("source_schema: missing field 'items'")
        return False

    if not isinstance(data["items"], list):
        print("source_schema: 'items' must be a list")
        return False

    for i in range(len(data["items"])):
        item = data["items"][i]
        if "text" not in item:
            print("source_schema: item at index", i, "is missing 'text' field")
            return False

    return True
