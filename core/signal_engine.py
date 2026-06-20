import sys
import os
import json
import socket
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core import orchestrator

LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")


def calculate_weighted_score(agent_results):
    # Purpose: combine all agent scores into one final score using weights
    # Input: agent_results (list of dicts) each following agent contract
    # Output: (float) weighted average score, rounded to 2 decimal places

    if len(agent_results) == 0:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for result in agent_results:
        score = result["score"]
        weight = result["weight"]
        weighted_sum = weighted_sum + (score * weight)
        total_weight = total_weight + weight

    if total_weight == 0.0:
        return 0.0

    return round(weighted_sum / total_weight, 2)


def get_turnover_rate(source_data_list):
    # Purpose: find turnover rate from the akshare source data
    # Input: source_data_list (list of dicts) loaded source JSON files
    # Output: (float) turnover rate, or 0.0 if not found

    for source in source_data_list:
        if source.get("source_name") == "akshare":
            items = source.get("items", [])
            if len(items) > 0:
                meta = items[0].get("meta", {})
                return float(meta.get("turnover_rate", 0.0))

    return 0.0


def check_filters(final_score, turnover_rate):
    # Purpose: decide whether to buy or pass based on score and turnover
    # Input: final_score (float), turnover_rate (float)
    # Output: (string) "BUY" or "PASS"
    # NOTE: turnover_rate filter is relaxed when rate is 0.0 (Yahoo Finance fallback)
    # TODO: restore full filter (score >= 3.0 AND turnover >= 2.0) once akshare is working

    if turnover_rate == 0.0:
        if final_score >= 2.0:
            return "BUY"
        else:
            return "PASS"

    if final_score >= 3.0 and turnover_rate >= 2.0:
        return "BUY"

    return "PASS"


def write_signal_log(stock_code, final_score, turnover_rate, decision, server_response):
    # Purpose: append one decision record to logs/signal_log.txt
    # Input: stock_code (string), final_score (float), turnover_rate (float),
    #        decision (string), server_response (string) - reply from C server
    # Output: none

    os.makedirs(LOGS_DIR, exist_ok=True)
    filepath = os.path.join(LOGS_DIR, "signal_log.txt")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (
        timestamp + " | " +
        stock_code + " | " +
        "score=" + str(final_score) + " | " +
        "turnover=" + str(turnover_rate) + "% | " +
        decision + " | " +
        "server=" + server_response
    )

    f = open(filepath, "a", encoding="utf-8")
    f.write(line + "\n")
    f.close()

    print("signal_engine: wrote to", filepath)


def send_score_to_pipeline(score):
    # Purpose: send the final score to the C server for circuit breaker check
    # Input: score (float) - converted to int before sending
    # Output: (string) server's echo, "CIRCUIT_BREAKER_TRIGGERED", or "NO_RESPONSE"

    int_score = int(score)
    message = str(int_score)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)

    try:
        s.connect(("localhost", 9000))
        s.sendall(message.encode("utf-8"))
        data = s.recv(256)
    except ConnectionRefusedError:
        print("signal_engine: C server not running at localhost:9000, skipping")
        s.close()
        return "NO_RESPONSE"
    except socket.timeout:
        print("signal_engine: C server did not respond within 3 seconds")
        s.close()
        return "NO_RESPONSE"
    except socket.error as e:
        print("signal_engine: socket error:", e)
        s.close()
        return "NO_RESPONSE"

    s.close()
    print("signal_engine: sent score=" + message + " to C server")

    if len(data) == 0:
        # server closed connection without reply — circuit breaker triggered
        print("signal_engine: C server closed connection (circuit breaker triggered)")
        return "CIRCUIT_BREAKER_TRIGGERED"

    response_text = data.decode("utf-8").strip()
    print("signal_engine: C server response=" + response_text)
    return response_text


def run(stock_code):
    # Purpose: run the full pipeline from reading data to outputting a signal
    # Input: stock_code (string)
    # Output: (string) "BUY" or "PASS"

    agent_results, source_data_list = orchestrator.run_and_return_sources()

    final_score = calculate_weighted_score(agent_results)
    turnover_rate = get_turnover_rate(source_data_list)
    decision = check_filters(final_score, turnover_rate)
    server_response = send_score_to_pipeline(final_score)

    write_signal_log(stock_code, final_score, turnover_rate, decision, server_response)

    print("signal_engine: stock=" + stock_code + " score=" + str(final_score) + " turnover=" + str(turnover_rate) + "% decision=" + decision)

    return decision


if __name__ == "__main__":
    result = run("000001")
    print("Final decision:", result)
