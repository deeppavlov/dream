from flask import Flask, request, jsonify
from client import HelloWorldExample
import logging

# import fill_db

import json

import time

time.sleep(40)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

# fill_db.fill_db()
greeter = HelloWorldExample("neo4j://neo4j:7687", "neo4j", "vbifhbr!@")
# greeter.get_graph()
stopWords = ['the', 'about', 'and', 'can', 'a', 'what', 'where', 'you', 'me', 'with', "I", "You", "He", "She", "It",
             "We", "They", "Me", "Him", "Her", "Us", "Them", "My", "Your", "Its", "Our", "Their", "Mine", "Yours",
             "His", "Hers", "Ours", "Yours", "Theirs", "Myself", "Yourself", "Himself", "Herself", "Itself",
             "Ourselves", "Yourselves", "Themselves", 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
             'us', 'them', 'my', 'your', 'its', 'our', 'their', 'mine', 'yours', 'his', 'hers', 'ours', 'yours',
             'theirs', 'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'yourselves', 'themselves',
             "Is", "Are", "is", "are", "Do", "do", "Does", "does", "who", "Who", "am", "Am", "Should", "should"]


@app.route("/trigger", methods=["POST"])
def search_answer():
    sentence = request.json["sentence"][:-1]
    logger.error(f"sentence: {sentence}")
    logger.error(f"request.json: {request.json}")
    c_3po_id = greeter.get_nodes_with_keyword('C-3PO')[0]['p.id']
    answers = []
    confidences = []
    name_nodes = []
    logger.error(f"sentence.split: {sentence.split()}")
    for word in sentence.split():
        if word in stopWords:
            continue
        nodes_ids = greeter.get_nodes_with_keyword(word)
        logger.error(f'nodes_ids: {nodes_ids}')
        if len(nodes_ids):
            for id in nodes_ids:
                name_node = greeter.get_name(id['p.id'])[0]['p.name']
                print(name_node)
                logger.error(f"name_node: {name_node}")
                try:
                    path = greeter.get_path(c_3po_id, id['p.id'])
                    path = path[0]['allShortestPaths((start)-[*]->(finish))'][0]
                    i = 0
                    answer = ''
                    while i < len(path):
                        item = path[i]
                        try:
                            answer += item['name'] + ', '
                        except:
                            answer += path[i] + ' '
                        i += 1

                    answer = answer.replace('_', ' ')[:-2] + '.'
                    answers.append(answer)
                    confidences.append(0.9)
                    name_nodes.append(name_node)
                except:
                    logger.error("except1")
                    answers.append("sorry, I don't know.")
                    confidences.append(0.2)
                    name_nodes.append(name_node)
        sub_nodes_ids = greeter.get_nodes_with_subkeyword(word)
        logger.error(f"sub_nodes_ids: {sub_nodes_ids}")
        if len(sub_nodes_ids) == 0:
            answers.append("sorry, I don't know.")
            confidences.append(0.2)
            name_nodes.append('')
        else:
            for id in sub_nodes_ids:
                name_node = greeter.get_name(id['p.id'])[0]['p.name']
                print(name_node)
                try:
                    path = greeter.get_path(c_3po_id, id['p.id'])
                    path = path[0]['allShortestPaths((start)-[*]->(finish))'][0]
                    i = 0
                    answer = ''
                    while i < len(path):
                        item = path[i]
                        try:
                            answer += item['name'] + ', '
                        except:
                            answer += path[i] + ' '
                        i += 1

                    answer = answer.replace('_', ' ')[:-2] + '.'
                    answers.append(answer)
                    confidences.append(0.6)
                    name_nodes.append(name_node)
                except:
                    logger.error("except2")
                    answers.append("sorry, I don't know.")
                    confidences.append(0.2)
                    name_nodes.append(name_node)
    logger.error(f"confidences: {confidences}")
    max_conf_index = confidences.index(max(confidences))
    logger.error(f"max_conf_index: {max_conf_index}")

    return json.dumps({"answer": answers[max_conf_index], "confidence": confidences[max_conf_index],
                       "topic": name_nodes[max_conf_index]})


@app.route("/can_trigger", methods=["POST"])
def bool_search_answer():
    sentence = request.json["sentence"]
    sentence = sentence[:-1]

    for word in sentence.split():
        if word in stopWords:
            continue

        nodes_ids = greeter.get_nodes_with_keyword(word)
        if len(nodes_ids):
            return json.dumps(True)

        sub_nodes_ids = greeter.get_nodes_with_subkeyword(word)
        if len(sub_nodes_ids):
            return json.dumps(True)

    return json.dumps(False)


@app.route("/detailed_trigger", methods=["POST"])
def second_answer():
    logger.error("detailed trigger")
    sentence = request.json["sentence"][:-1]
    logger.error(f"sentence[:-1]: {sentence}")
    logger.error(f"request.json: {request.json}")

    for word in sentence.split():
        if word in stopWords:
            continue
        nodes_ids = greeter.get_prop_with_subkeyword(word)
        logger.error(f"nodes_ids: {nodes_ids}")
        if len(nodes_ids):
            for id in nodes_ids:
                try:
                    get_inform = False
                    answer = id['p']['name'] + ', '
                    logger.error(f"answer: {answer}")
                    node_prop = id['p']
                    logger.error(f"node_prop: {node_prop}")
                    logger.error(f"node_prop.keys: {node_prop.keys}")
                    for key in node_prop.keys():
                        if key != 'name' and key != 'id':
                            get_inform = True
                            inf = node_prop[key]
                            answer += key + ' ' + inf + ', '
                    if not get_inform:
                        logger.error("not get_inform")
                        answer = 'Sorry, I dont know'
                        confidence = 0.1
                        return json.dumps({"answer": answer, "confidence": confidence})
                    answer = answer[:-2] + '.'
                    logger.error(f"answer: {answer}")
                    return json.dumps({"answer": answer, "confidence": 0.9})
                except:
                    logger.error("except")
                    answer = 'Sorry, I dont know'
                    confidence = 0.1
                    return json.dumps({"answer": answer, "confidence": confidence})


@app.route("/respond", methods=["POST"])
def respond():
    dialogs = request.json["dialogs"]

    responses = []
    confidences = []

    for dialog in dialogs:
        sentence = None
        # sentence = dialog['human_utterances'][-1]['annotations'].get(
        #    "spelling_preprocessing")

        if sentence is None:
            logger.warning('Not found spelling preprocessing annotation')
            sentence = dialog['human_utterances'][-1]['text']


if __name__ == '__main__':
    # search_answer("What are you think about Hoth?")
    app.run(debug=False, host="0.0.0.0", port=3055)
