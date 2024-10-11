import allure
import requests
import json

from prepare_test import prepare_data, prepare_for_comparison, compare_results


BOT_KNOWLEDGE_MEMORIZER_PORT = 8044  # tested with dream_kg_prompted distribution
BOT_KNOWLEDGE_MEMORIZER_URL = f"http://0.0.0.0:{BOT_KNOWLEDGE_MEMORIZER_PORT}/respond"


@allure.description("""4.1.2 Test input and output data types""")
def test_in_out():
    input_data, _ = prepare_data()

    result = requests.post(BOT_KNOWLEDGE_MEMORIZER_URL, json=next(iter(input_data)))

    assert isinstance(input_data, (dict, list)), "Invalid input type"
    assert isinstance(result.json(), (dict, list)), "Invalid output type"


@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    def _extract_function_duration(source, func):
        if source["function"] == func:
            return source["time"]
        for child in source["children"]:
            return _extract_function_duration(child, func)
        return 0

    def _get_exec_time():
        knowledge_time = _extract_function_duration(output_dict["root_frame"], "get_knowledge")
        llm_time = _extract_function_duration(output_dict["root_frame"], "convert_triplets_to_natural_language")
        terminusdb_time = _extract_function_duration(output_dict["root_frame"], "create_entities")
        props_time = _extract_function_duration(output_dict["root_frame"], "get_properties_of_entities")

        return total_time - knowledge_time - llm_time - terminusdb_time - props_time

    input_data, _ = prepare_data()
    time_result = requests.post(f"{BOT_KNOWLEDGE_MEMORIZER_URL}?profile", json=next(iter(input_data)))
    output_dict = json.loads(time_result.text)

    total_time = output_dict["duration"]

    exec_time = _get_exec_time()
    assert exec_time <= 0.4, "Unsufficient run time"


@allure.description("""Execution test""")
def test_execution():
    request_data, golden_results = prepare_data()
    count = 0
    for data, golden_result in zip(request_data, golden_results):
        result = requests.post(BOT_KNOWLEDGE_MEMORIZER_URL, json=data).json()

        prepared_result = prepare_for_comparison(result)
        if compare_results(prepared_result, golden_result):
            count += 1
    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    test_in_out()
    test_exec_time()
    test_execution()
