from pathlib import Path

from loguru import logger
from random import choice
from queue import Queue
from threading import Thread
from time import time

from ard.data import Dataset
from ard.knowledge_graph import KnowledgeGraph
from ard.hypothesis import Hypothesis
from ard.subgraph import Subgraph

from src.stuff.Pipeline import Pipeline
from src.stuff.PipelineStructure import PipelineStructure, Node, Edge
from src.stuff.agents import (
    CriticAgent,
    EvidenceAgent,
    ExplainableAgent,
    FeasibilityAgent,
    HypothesisAgent,
    MasterAgent,
    ThinkerAgent
)
from src.stuff.ApiController import ModelConfig, ModelEnum


class Master:
    def __init__(self, FILENAME):
        """
        Graph management class for the agents.
        This class is responsible for creating the knowledge graph and managing the random walk.
        """
        # Setting up knowledge graph
                # data_dir = Path(__file__).parent / "my_graph"
                # dataset = Dataset.from_local(data_dir)

                # triplets_dict = dataset.get_triplets(build_graph=False)
                # triplets_list = list(triplets_dict.values())

                # self.kg = KnowledgeGraph.from_triplets(triplets_list)

        file_dir = Path(__file__).parent.parent / FILENAME
        logger.info("Loading knowledge graph from {}".format(file_dir))
        self.kg = Subgraph.load_from_file(file_dir)

        logger.info("Knowledge graph created with {} nodes and {} edges.".format(self.kg.number_of_nodes(), self.kg.number_of_edges()))
        
        if self.kg.has_graph() != True:
            raise Exception("Graph not created. Please check the triplets.")
        
        # Parms
        self.max_walk = 100

        self.thread_stop_flag = False

        self.best_hypothesis = Hypothesis(
            title="",
            statement="",
            source=None,
            method=None,
            references=[],
            metadata={
                "score": 0,
            }
        )

        self.data_queue = Queue()

        self.node_visits = [[node, 0] for node in self.kg.get_nodes()]

    def random_walk(self, start_node, max_steps):
        if not self.kg.has_node(start_node):
            raise ValueError(f"Start node '{start_node}' not found in the graph")

        current_node = start_node
        visited = [current_node]

        for _ in range(max_steps):
            neighbors = self.kg.get_successors(current_node)
            if not neighbors:
                break
            next_node = choice(neighbors)
            visited.append(next_node)
            current_node = next_node

        return visited
            

    def check_order(self, node1, node2):
        # Returns node1 and node2 in correct order according to edge
        # node1 -> node2 or node1 <-> node2
        try:
            tmp = self.kg.get_edge_attrs(node1, node2)
            return node1, node2
        except:
            try:
                tmp = self.kg.get_edge_attrs(node2, node1)
                return node2, node1
            except:
                raise Exception("No edge between {} and {}".format(node1, node2))

    def graph_paths_gen(self):
        while True:
            self.node_visits = sorted(self.node_visits, key=lambda x: x[1])
            node = self.node_visits[0][0]
            self.node_visits[0][1] += 1

            r_walk = self.random_walk(node, self.max_walk)
            # logger.info("Random walk: {}".format(r_walk))

            res = []
            for i in range(len(r_walk) - 1):
                node1 = r_walk[i]
                node2 = r_walk[i + 1]

                attr = self.kg.get_edge_attrs(node1, node2)

                res.append((node1, attr["relation"], node2))

            if len(res) > 3:
                for node in r_walk:
                    for i in range(len(self.node_visits)):
                        if self.node_visits[i][0] == node:
                            self.node_visits[i][1] += 1
                            # print("Node {} visited {} times".format(node, self.node_visits[i][1]))
                            break
                yield res

    def worker(self, worker_id):
        structure = PipelineStructure(
            start=0,
            nodes={
                0: Node([HypothesisAgent(ModelConfig(ModelEnum.REASONING))]),
                1: Node([ThinkerAgent(ModelConfig(ModelEnum.REASONING))]),
                2: Node([EvidenceAgent(ModelConfig(ModelEnum.LARGE)), FeasibilityAgent(ModelConfig(ModelEnum.LARGE))]),
                3: Node([ExplainableAgent(ModelConfig(ModelEnum.LARGE))]),
                4: Node([CriticAgent(ModelConfig(ModelEnum.LARGE))]),
                5: Node([MasterAgent(ModelConfig(ModelEnum.LARGE))]),
            },
            edges={
                0: Edge(1),
                1: Edge(2),
                2: Edge(3),
                3: Edge(4),
                4: Edge(5),
                5: Edge(1),
            }
        )
        pipeline = Pipeline(structure, max_iters=60)

        while not self.thread_stop_flag:
            try:
                data = self.data_queue.get(timeout=3) 
            except Exception:
                break

            res_hip = pipeline.run(data)
            if res_hip.metadata["score"] > self.best_hypothesis.metadata["score"]:
                self.best_hypothesis = res_hip
                logger.info("Best hypothesis: {}".format(self.best_hypothesis))

    def run(self):
        start_time = time()
        end_time = time() + 10

        while time() < end_time:
            self.thread_stop_flag = False
            threads = []
            cnt = 0

            for i in range(1):
                t = Thread(target=self.worker, args=(i,))
                t.start()
                threads.append(t)

            for path in self.graph_paths_gen():
                data = path
                self.data_queue.put(data)
                
                cnt += 1
                if cnt > 20:
                    self.thread_stop_flag = True
                    break

            for t in threads:
                t.join()

            # TODO: save the best hypothesis
