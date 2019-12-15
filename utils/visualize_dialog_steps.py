# Lets visualize all messages transitions
import pydot
import json
import networkx as nx
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', help='input json with dialogs (can be fetched through /dialogs)', default='dialogs')
parser.add_argument('--output', help='gexf file', default='dialogs.gexf')
parser.add_argument('--png', action='store_true', default=False, help='make png')

# import urllib.request
# import pprint


def visualize(dialogs_json_file, outfile, png=False):
    """
    It can read a local file with JSON formatted dialogs, or download it from Amazon's endpoint

    Then it produces gexf (png, svg) file which can be analyzed with Gephi tool

    Returns:
        graph as gexf file

    """
    # #####################################################################
    # # download json with dialogs from Amazon:
    # with urllib.request.urlopen(
    #         "http://docker-externalloa-lofsuritnple-525614984.us-east-1.elb.amazonaws.com:4242/dialogs") as url:
    #     json_data = json.loads(url.read().decode())
    #     print(json_data)

    # #####################################################################
    # # write dialogs to local file:
    # with open('dialogs_data.json', 'w') as f:
    #     json.dump(json_data, f)

    # #####################################################################
    # read dialogs from local file
    with open(dialogs_json_file) as dialogs_f:
        json_data = json.load(dialogs_f)

    graph = pydot.Dot(graph_type='digraph')
    print(len(json_data))
    # import ipdb; ipdb.set_trace()

    # pprint.pprint(json_data)
    edges_dict = {}
    for each_dialog in json_data[-100:]:
        prev_node = None
        for utt_idx, each_utterance in enumerate(each_dialog['utterances']):
            name = each_utterance['text']
            # node = pydot.Node(name, shape="rectangle")
            if utt_idx % 2 == 0:
                # if Human Utterance -> green
                color = "green"
            else:
                # if bot says:
                color = "blue"
            node = pydot.Node(name, style="filled", fillcolor=color, color=color)
            if 'frequency' in node.obj_dict:
                node.obj_dict['frequency'] += 1
            else:
                # init frequency counter:
                node.obj_dict['frequency'] = 1

            if utt_idx > 0:

                # frequency stat in edges instad of duplicated edges
                if prev_node in edges_dict:
                    if node in edges_dict[prev_node]:
                        # increase counter
                        if 'frequency' in edges_dict[prev_node][node].obj_dict:
                            edges_dict[prev_node][node].obj_dict['frequency'] += 1
                        else:
                            raise Exception("Can not be here!")
                    else:
                        edge = pydot.Edge(prev_node, node)
                        edges_dict[prev_node][node] = edge
                        edges_dict[prev_node][node].obj_dict['frequency'] = 1
                        graph.add_edge(edge)
                else:
                    edges_dict[prev_node] = {}
                    edge = pydot.Edge(prev_node, node)
                    edges_dict[prev_node][node] = edge
                    edges_dict[prev_node][node].obj_dict['frequency'] = 1
                    graph.add_edge(edge)

                # edge = pydot.Edge(prev_node, node)
                # graph.add_edge(edge)
            prev_node = node
    print("graph generated")
    # import ipdb; ipdb.set_trace()

    nx_graph = nx.drawing.nx_pydot.from_pydot(graph)

    nx.write_gexf(nx_graph, outfile)

    if png:
        graph.write_png(outfile + '.png')
        graph.write_svg(outfile + '.svg')

    print("Fin.")


if __name__ == "__main__":
    args = parser.parse_args()
    visualize(dialogs_json_file=args.input, outfile=args.output, png=args.png)
