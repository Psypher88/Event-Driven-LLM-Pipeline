import sys
import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# add project root so we can import from agents/ and contracts/
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contracts import agent_schema
import agents.agent_buyer as agent_buyer
import agents.agent_seller as agent_seller

DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def discover_sources():
    # Purpose: find all JSON files in data/ folder and load their contents
    # Input: none
    # Output: (list of dicts) each dict is one loaded source JSON file

    results = []

    if not os.path.exists(DATA_DIR):
        print("orchestrator: data/ folder does not exist, run a source first")
        return results

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(DATA_DIR, filename)
            f = open(filepath, "r", encoding="utf-8")
            content = json.load(f)
            f.close()
            results.append(content)
            print("orchestrator: loaded source file:", filename)

    return results


def discover_agents():
    # Purpose: return the list of all active agent modules
    # Input: none
    # Output: (list of modules) each module has a run() function
    # To add a new agent: import it at the top of this file, then add it to this list

    modules = [agent_buyer, agent_seller]
    return modules


def run_all():
    # Purpose: run every agent on every news item from every source
    # Input: none
    # Output: (list of dicts) each entry has item_text, agent_name, score, reason, weight

    sources = discover_sources()
    agents = discover_agents()
    results = []

    if len(sources) == 0:
        print("orchestrator: no source data found, nothing to process")
        return results

    if len(agents) == 0:
        print("orchestrator: no agents found, nothing to process")
        return results

    for source in sources:
        source_name = source.get("source_name", "unknown")
        items = source.get("items", [])

        for item in items:
            item_text = item["text"]

            for agent in agents:
                agent_result = agent.run(item_text)

                is_valid = agent_schema.validate(agent_result)
                if not is_valid:
                    print("orchestrator: agent result failed validation, skipping")
                    continue

                entry = {
                    "source_name": source_name,
                    "item_text": item_text,
                    "agent_name": agent_result["agent_name"],
                    "score": agent_result["score"],
                    "reason": agent_result["reason"],
                    "weight": agent_result["weight"]
                }
                results.append(entry)

    return results


def run_and_return_sources():
    # Purpose: run the full pipeline and return both agent results and raw source data
    # Input: none
    # Output: (tuple) (agent_results, source_data_list)
    #         agent_results: list of dicts following agent contract
    #         source_data_list: list of dicts following source contract

    sources = discover_sources()
    agents = discover_agents()
    agent_results = []

    if len(sources) == 0:
        print("orchestrator: no source data found, nothing to process")
        return agent_results, sources

    if len(agents) == 0:
        print("orchestrator: no agents found, nothing to process")
        return agent_results, sources

    for source in sources:
        source_name = source.get("source_name", "unknown")
        items = source.get("items", [])

        for item in items:
            item_text = item["text"]

            for agent in agents:
                agent_result = agent.run(item_text)

                is_valid = agent_schema.validate(agent_result)
                if not is_valid:
                    print("orchestrator: agent result failed validation, skipping")
                    continue

                entry = {
                    "source_name": source_name,
                    "item_text": item_text,
                    "agent_name": agent_result["agent_name"],
                    "score": agent_result["score"],
                    "reason": agent_result["reason"],
                    "weight": agent_result["weight"]
                }
                agent_results.append(entry)

    return agent_results, sources


if __name__ == "__main__":
    all_results = run_all()
    print()
    print("=== orchestrator results ===")
    for entry in all_results:
        print(entry)
