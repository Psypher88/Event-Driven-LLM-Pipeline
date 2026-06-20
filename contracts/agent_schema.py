def validate(data):
    # Purpose: check that an agent output dict has all required fields and valid values
    # Input: data (dict) - the agent output to validate
    # Output: (bool) True if valid, False if any field is missing or out of range

    if "agent_name" not in data:
        print("agent_schema: missing field 'agent_name'")
        return False

    if "score" not in data:
        print("agent_schema: missing field 'score'")
        return False

    if "reason" not in data:
        print("agent_schema: missing field 'reason'")
        return False

    if "weight" not in data:
        print("agent_schema: missing field 'weight'")
        return False

    score = data["score"]
    if not isinstance(score, int):
        print("agent_schema: 'score' must be an integer, got:", type(score))
        return False

    if score < -5 or score > 5:
        print("agent_schema: 'score' must be between -5 and +5, got:", score)
        return False

    weight = data["weight"]
    if weight < 0 or weight > 1:
        print("agent_schema: 'weight' must be between 0 and 1, got:", weight)
        return False

    return True
