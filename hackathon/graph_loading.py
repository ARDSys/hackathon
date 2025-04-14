from ard.knowledge_graph.knowledge_graph import KnowledgeGraph
import pandas as pd
import os
from loguru import logger

def construct_prime_kg(file, uri, user, password, database):
    df = pd.read_csv(file)
    np_arr = df.to_numpy()
    graph = KnowledgeGraph(backend="neo4j", uri=uri, user=user, password=password, database=database)
    
    for record in np_arr:
        source_x = record[6]
        source_y = record[11]
        relation = record[1]
        node_x = record[5] + ": " + record[4]
        node_y = record[10] + ": " + record[9]
        
        if source_x == source_y:
            source = source_x
        else:
            source = source_x + "," + source_y
        
        if not graph.has_node(node_x):
            graph.add_node(node_x)
        
        if not graph.has_node(node_y):
            graph.add_node(node_y)
        
        graph.add_edge(node_x, node_y, relation=relation, sources=source)
    
def add_node_by_attribute(row, attribute, graph, added_nodes):
    node_value = row[attribute]
    if node_value in added_nodes:
        return

    node_attrs = {k: v for k, v in row.items() if not k.startswith('~') and k != attribute and v != float('NaN') and v != None}
    graph.add_node(node_value, **node_attrs)
    added_nodes.add(node_value)

def construct_ctkg(graph_file, attributes_file, uri, user, password, database):
    df = pd.read_csv(graph_file, sep='\t')

    attributes_map = {}
    for dir_file in os.listdir(attributes_file):
        key = dir_file.split("_")[0]
        attr_df = pd.read_csv(os.path.join(attributes_file, dir_file))
        attr_df = attr_df.set_index('~id', drop=False)
        attributes_map[key] = attr_df

    graph = KnowledgeGraph(backend="neo4j", uri=uri, user=user, password=password, database=database)
    added_nodes = set()

    logger.info(f"There are {len(df)} relations in the graph")

    id_keys = ['name:String', 'term:String', 'title:String', 'brief_title:String', 'group_description:String', '~id']

    for idx, row in enumerate(df.itertuples(index=False)):
        try:
            src_parts = row[0].split("::")
            trg_parts = row[2].split("::")
            id1 = src_parts[0] + "ID:" + src_parts[1]
            id2 = trg_parts[0] + "ID:" + trg_parts[1]

            names = row[1].split("::")
            if len(names) < 2:
                logger.warning(f"Row {idx} has an unexpected name format: {row[1]}")
                continue
            name1, name2 = names[0], names[1]

            if name1 not in attributes_map or name2 not in attributes_map:
                continue

            access_point1 = attributes_map[name1]
            access_point2 = attributes_map[name2]

            try:
                row1 = access_point1.loc[id1]
                row2 = access_point2.loc[id2]
            except KeyError:
                continue

            node_names = []
            for node_row in [row1, row2]:
                found = False
                for key in id_keys:
                    if key in node_row:
                        add_node_by_attribute(dict(node_row), key, graph, added_nodes)
                        node_names.append(node_row[key])
                        found = True
                        break
                if not found:
                    logger.error(f"Missing expected key in row attributes: {node_row}")
                    return

            graph.add_edge(node_names[0], node_names[1])

            if idx % 100000 == 0 and idx > 0:
                logger.info(f"Processed {idx} relations")
        except Exception as ex:
            logger.error(f"Error processing row {idx}: {ex}")
            continue

    logger.info(f"Completed graph construction")

from neo4j import GraphDatabase

def do_migrate_data(source_driver, target_driver):
    with source_driver.session() as source_session, target_driver.session() as target_session:
        # 1. Migrate nodes:
        # Retrieve all nodes with their internal ID, labels, and properties.
        node_query = "MATCH (n) RETURN id(n) as id, labels(n) as labels, properties(n) as props"
        nodes_result = source_session.run(node_query)
        
        for record in nodes_result:
            node_id = record["id"]
            labels = record["labels"]  # list of labels for the node
            props = record["props"]
            # Save the source id to match relationships later.
            props["source_id"] = node_id
            # Create the label string for the CREATE statement.
            label_str = ":" + ":".join(labels) if labels else ""
            create_node_query = f"CREATE (n{label_str} $props)"
            target_session.run(create_node_query, props=props)
        
        # 2. Migrate relationships:
        # Retrieve relationships with their type, properties, and start/end node IDs from the source.
        rel_query = """
        MATCH (a)-[r]->(b)
        RETURN type(r) as rel_type, properties(r) as props, id(a) as start, id(b) as end
        """
        rel_result = source_session.run(rel_query)
        
        for record in rel_result:
            rel_type = record["rel_type"]
            props = record["props"]
            start_source_id = record["start"]
            end_source_id = record["end"]
            # Reconnect nodes in the target using the source_id property.
            create_rel_query = f"""
            MATCH (a) WHERE a.source_id = $start_id
            MATCH (b) WHERE b.source_id = $end_id
            CREATE (a)-[r:{rel_type} $props]->(b)
            """
            target_session.run(create_rel_query, start_id=start_source_id, end_id=end_source_id, props=props)

def migrate_data(source_uri, source_username, source_password, target_uri, target_username, target_password):
    source_driver = GraphDatabase.driver(source_uri, auth=(source_username, source_password))
    target_driver = GraphDatabase.driver(target_uri, auth=(target_username, target_password))
    
    try:
        print("Starting data migration on target server...")
        do_migrate_data(source_driver, target_driver)
        print("Data migration completed successfully.")
    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        source_driver.close()
        target_driver.close()

#graph = KnowledgeGraph(backend="neo4j", uri="neo4j://robokopkg.renci.org:7687", user="", password="", database=None)
#graph = KnowledgeGraph(backend="neo4j", uri="bolt://neo4j.het.io:7687", user="", password="", database=None)
#construct_prime_kg("../kg.csv", uri="bolt://neo4j.het.io:7687", user="", password="", database=None)
#construct_ctkg("../CTKG/ctkg.tsv", "../CTKG/attributes", uri="bolt://neo4j.het.io:7687", user="", password="", database=None)

#print(graph.get_node_neighbors_relations(graph.get_random_node()))
