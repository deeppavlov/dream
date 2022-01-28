from neo4j import GraphDatabase


class HelloWorldExample:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver((uri) , auth=(user, password), encrypted=False)
        self.node_id = 0
        self.relation_id = 0

    def close(self):
        self.driver.close()

    def delete_all(self):
        with self.driver.session() as session:
            session.write_transaction(self._delete_all)
            self.node_id = 0
            self.relation_id = 0

    @staticmethod
    def _delete_all(tx):
        result = tx.run("MATCH (n) "
                        "DETACH DELETE n")

    def create_node(self, label="", properties="{}"):
        if properties == "{}":
            properties = "{" + "id: {}".format(self.node_id) + "}"
        else:
            properties = "{" + "id: {}, ".format(self.node_id) + properties[1:]
        with self.driver.session() as session:
            result = session.write_transaction(self._create_node, label, properties)
            self.node_id += 1
            return result

    @staticmethod
    def _create_node(tx, label, properties):
        result = tx.run("CREATE (node:{} {})"
                        "RETURN node.id".format(label, properties))
        return result.single()[0]

    def get_graph(self):
        with self.driver.session() as session:
            result = session.run("MATCH (n)"
                                 "RETURN n")
            return result.data()

    def create_relation(self, id_start, id_finish, label="", properties="{}"):
        if properties == "{}":
            properties = "{" + "id: {}".format(self.relation_id) + "}"
        else:
            properties = "{" + "id: {}, ".format(self.relation_id) + properties[1:]
        with self.driver.session() as session:
            result = session.write_transaction(self._create_relation, id_start, id_finish, label, properties)
            self.relation_id += 1
            return result

    @staticmethod
    def _create_relation(tx, id_start, id_finish, label, properties):
        result = tx.run("MATCH "
                        "   (a), (b)"
                        "WHERE a.id = {} AND b.id = {}"
                        "CREATE (a)-[r:{} {}] -> (b)"
                        "RETURN r.id".format(id_start, id_finish, label, properties))
        return result.single()[0]

    def get_path(self, id_start, id_finish):
        with self.driver.session() as session:
            result = session.run("MATCH "
                                 "  (start), (finish)"
                                 "WHERE start.id = {} AND finish.id = {} "
                                 "RETURN allShortestPaths((start)-[*]->(finish))".format(id_start, id_finish))
            return result.data()

    def delete_node(self, id_node):
        with self.driver.session() as session:
            session.write_transaction(self._delete_node, id_node)

    @staticmethod
    def _delete_node(tx, id_node):
        tx.run("MATCH "
               "   (n)"
               "WHERE n.id = {} "
               "DETACH DELETE n".format(id_node))

    def delete_relation(self, id_relation):
        with self.driver.session() as session:
            session.write_transaction(self._delete_ralation, id_relation)

    @staticmethod
    def _delete_ralation(tx, id_relation):
        tx.run("MATCH "
               "  (a)-[r]->(b)"
               "WHERE r.id = {} "
               "DETACH DELETE r".format(id_relation))

    def get_name(self, node_id):
        with self.driver.session() as session:
            result = session.run("MATCH "
                                 "  (p)"
                                 "WHERE p.id = {}"
                                 "RETURN p.name".format(node_id))
            return result.data()

    def update_node(self, node_id, new_properties):
        if new_properties == "{}":
            new_properties = "{" + "id: {}".format(node_id) + "}"
        else:
            new_properties = "{" + "id: {}, ".format(node_id) + new_properties[1:]
        with self.driver.session() as session:
            session.write_transaction(self._update_node, node_id, new_properties)

    @staticmethod
    def _update_node(tx, node_id, new_properties):
        tx.run("MATCH "
               "  (n)"
               "WHERE n.id = {} "
               "SET n = {}".format(node_id, new_properties))

    def get_nodes_with_subkeyword(self, substr):
        with self.driver.session() as session:
            result = session.run("MATCH "
                                 "  (p)"
                                 "WHERE p.name =~ '.*{}.*'"
                                 "RETURN p.id".format(substr))
            return result.data()

    def get_nodes_with_keyword(self, str_):
        with self.driver.session() as session:
            result = session.run("MATCH "
                                 "  (p)"
                                 "WHERE p.name =~ '{}'"
                                 "RETURN p.id".format(str_))
            return result.data()

    def get_prop_with_subkeyword(self, substr):
        with self.driver.session() as session:
            result = session.run("MATCH "
                                 "  (p)"
                                 "WHERE p.name =~ '.*{}.*'"
                                 "RETURN p".format(substr))
            return result.data()

if __name__ == "__main__":
    # in localhost
    greeter = HelloWorldExample("neo4j://localhost:8687", "neo4j", "vbifhbr!@")
    # in docker exec
    # greeter = HelloWorldExample("neo4j://hoe4j:7687", "neo4j", "vbifhbr!@")
    greeter.delete_all()
    greeter.create_node(label="xxx:yyy", properties="{city:'Moscow'}")
    greeter.create_node(label="xxx")
    greeter.create_relation(0, 1, "a", "{length: 100}")
    greeter.create_relation(0, 1, "b", "{length: 100}")
    print(greeter.get_path(0, 1))
    greeter.delete_relation(1)
    print(greeter.get_path(0, 1))
    print(greeter.get_graph())
    greeter.delete_node(1)
    print(greeter.get_graph())
    greeter.update_node(0, "{city: 'Dolgopa'}")
    print(greeter.get_graph())
    greeter.delete_all()
    greeter.close()
