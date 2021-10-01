import client
from flask import Flask, request, jsonify
import logging

import fill_db

import json

import time

time.sleep(40)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

fill_db.fill_db()
greeter = client.HelloWorldExample("neo4j://neo4j:7687", "neo4j", "vbifhbr!@")

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

    c_3po_id = greeter.get_nodes_with_keyword('C-3PO')[0]['p.id']
    answers = []
    confidences = []
    name_nodes = []
    for word in sentence.split():
        if word in stopWords:
            continue
        nodes_ids = greeter.get_nodes_with_keyword(word)
        if len(nodes_ids):
            for id in nodes_ids:
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
                    confidences.append(0.9)
                    name_nodes.append(name_node)
                except:
                    answers.append("sorry, I don't know.")
                    confidences.append(0.2)
                    name_nodes.append(name_node)
        sub_nodes_ids = greeter.get_nodes_with_subkeyword(word)
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
                    answers.append("sorry, I don't know.")
                    confidences.append(0.2)
                    name_nodes.append(name_node)
    max_conf_index = confidences.index(max(confidences))

    return json.dumps({"answer": answers[max_conf_index], "confidence": confidences[max_conf_index], "topic": name_nodes[max_conf_index]})

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
    sentence = request.json["sentence"][:-1]

    for word in sentence.split():
        if word in stopWords:
            continue
        nodes_ids = greeter.get_prop_with_subkeyword(word)
        if len(nodes_ids):
            for id in nodes_ids:
                try:
                    get_inform = False
                    answer = id['p']['name'] + ', '
                    node_prop = id['p']
                    for key in node_prop.keys():
                        if key != 'name' and key != 'id':
                            get_inform = True
                            inf = node_prop[key]
                            answer += key + ' ' + inf + ', '
                    if not get_inform:
                        answer = 'Sorry, I dont know'
                        confidence = 0.1
                        return json.dumps({"answer": answer, "confidence": confidence})
                    answer = answer[:-2] + '.'
                    return json.dumps({"answer": answer, "confidence": 0.9})
                except:
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
    #search_answer("What are you think about Hoth?")
    app.run(debug=False, host="0.0.0.0", port=3055)

