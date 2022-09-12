import sqlite3
import numpy as np
from numpy import average, ndarray, ones_like
import time
from fleet_classes import Offer, Component
import copy
from LocalSearchAlgorithm.partitions_generator import separate_partitions
from enum import IntEnum


class DevelopMode(IntEnum):
    ALL = 1
    PROPORTIONAL = 2


class GetNextMode(IntEnum):
    STOCHASTIC_ANNEALING = 1
    GREEDY = 2


class GetStartNodeMode(IntEnum):
    RESET_SELECTOR = 1
    ROOT = 2
    RANDOM = 3


class CombOptim:
    def __init__(self,
                 number_of_results: int,
                 candidate_list_size: int,
                 price_calc,
                 initial_seperated,
                 time_per_region: float,
                 region: str,
                 exploitation_score_price_bias: float,
                 exploration_score_depth_bias: float,
                 exploitation_bias: float,
                 sql_path: str,
                 verbose: bool = True,
                 develop_mode=DevelopMode.ALL,
                 proportion_amount_node_sons_to_develop: float = 0.05,
                 get_next_mode=GetNextMode.STOCHASTIC_ANNEALING,
                 get_starting_node_mode=GetStartNodeMode.RESET_SELECTOR
                 ):
        self.verbose = verbose
        Node.verbose = verbose
        Node.node_cache.clear()

        """'price_calc' is a function: (Offer)-->float which calculate the price of a certain configuration"""
        self.root = self.calc_root(initial_seperated, price_calc)
        self.optim_set = OptimumSet(1)
        if get_starting_node_mode == GetStartNodeMode.RESET_SELECTOR:
            self.reset_sel = ResetSelector(candidate_list_size, self.get_num_components(), self.root,
                                           exploitation_score_price_bias, exploration_score_depth_bias,
                                           exploitation_bias, self.verbose)

        self.get_starting_node_mode = get_starting_node_mode
        self.search_algo = SearchAlgorithm(
            develop_mode=develop_mode,
            get_next_mode=get_next_mode,
            num_components=self.get_num_components(),
            proportion_amount_node_sons_to_develop=proportion_amount_node_sons_to_develop
        )
        self.start_time = time.time()
        self.time_per_region = time_per_region / number_of_results
        self.region = region
        self.exploitation_score_price_bias = exploitation_score_price_bias
        self.exploration_score_depth_bias = exploration_score_depth_bias
        self.exploitation_bias = exploitation_bias
        self.conn = sqlite3.connect(sql_path)
        self.get_next_mode = get_next_mode

    def finish_stats_operation(self):
        self.conn.commit()
        self.conn.close()

    def insert_stats(self, iteration):
        returned_best = self.optim_set.returnBest()
        best_node = returned_best[0]
        best_price = best_node.getPrice()
        depth_best = best_node.getDepth()
        query = "INSERT INTO STATS (INSERT_TIME, NODES_COUNT, BEST_PRICE, DEPTH_BEST, ITERATION, REGION_SOLUTION)\
                          VALUES ({insert_time}, {NODES_COUNT}, {BEST_PRICE}, {DEPTH_BEST}, {ITERATION}, '{region}')".format(
            insert_time=time.time() - self.start_time, NODES_COUNT=len(Node.node_cache), BEST_PRICE=best_price, \
            DEPTH_BEST=depth_best, ITERATION=iteration, region=self.region)
        self.conn.execute(query)

    def create_stats_table(self):
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS STATS
        (INSERT_TIME    REAL     NOT NULL,
        NODES_COUNT   INT     NOT NULL,
        BEST_PRICE  REAL    NOT NULL,
        DEPTH_BEST  INT NOT NULL,
        ITERATION  INT NOT NULL,
        REGION_SOLUTION TEXT    NOT NULL);''')

    def calc_root(self, initial_seperated, price_calc):
        partitions = list(map(lambda i: separate_partitions(i), initial_seperated))
        return Node(partitions, 0, price_calc)

    def get_num_components(self):
        num_of_comp = 0
        for group in self.root.partitions:
            combination = group[0]  # each group has 1 combination
            num_of_comp += len(combination)

        return num_of_comp

    def get_root(self):
        return self.root

    def get_start_node(self):
        start_node = None
        if self.get_starting_node_mode == GetStartNodeMode.RESET_SELECTOR:
            start_node = self.reset_sel.getStartNode()
        elif self.get_starting_node_mode == GetStartNodeMode.ROOT:
            start_node = self.root
        elif self.get_starting_node_mode == GetStartNodeMode.RANDOM:
            while True:
                start_node = Node.random_node_from(self.root)
                if not self.check_anti_affinity(start_node) and self.check_affinity(start_node):
                    break

            # if start_node.getPrice() == np.inf:
            #     start_node = self.root
        return start_node

    def check_anti_affinity(self, start_node):
        """Check if there are pairs that shouldn't be paired (anti-affinity)."""
        anti_affinity_list = []
        for stp in start_node.partitions[0]:
            for stp1 in stp:
                for aff_stp1 in stp1:
                    anti_affinity_list.append(aff_stp1.anti_affinity) if stp1 is not None else None
        anti_affinity_list = list(filter(None, anti_affinity_list))
        if self.anti_affinity(start_node, anti_affinity_list):
            return True
        return False

    def check_affinity(self, start_node):
        """Check if there are pairs that must be paired together (affinity)."""
        affinity_list = []
        for stp in start_node.partitions[0]:
            for stp1 in stp:
                for aff_stp1 in stp1:
                    affinity_list.append(aff_stp1.affinity) if stp1 is not None else None
        affinity_list = list(filter(None, affinity_list))
        if self.affinity(start_node, affinity_list):
            return True
        return False

    def affinity(self, next_node, aff):
        """Check if there are pairs that must be paired together (affinity)."""
        flag = True
        for nnp in next_node.partitions:
            for nnp1 in nnp:
                arr2 = []
                for nnp2 in nnp1:
                    arr = []
                    for nnp3 in nnp2:
                        arr.append(nnp3.component_name)
                    arr2.append(arr)
        for ind in aff:
            if not self.compare_sublists(ind, arr2):
                flag = False
        return flag

    def anti_affinity(self, next_node, aff):
        """Check if there are pairs that shouldn't be paired (anti-affinity)."""
        for nnp in next_node.partitions:
            for nnp1 in nnp:
                arr2 = []
                for nnp2 in nnp1:
                    arr = []
                    for nnp3 in nnp2:
                        arr.append(nnp3.component_name)
                    arr2.append(arr)
        for ind in aff:
            if self.compare_sublists(ind, arr2):
                return True
        return False

    def compare_sublists(self, list, listoflists):
        """Check if list 'listoflists' contains the list 'list'."""
        for sublist in listoflists:
            temp = [i for i in sublist if i in list]
            if sorted(temp) == sorted(list):
                return True
        return False

    def run(self):
        """main function of algorithm.

        Returns: list of best offers.
        """
        if self.root.getPrice() == np.inf:
            print("CombOptim.run: infinite price for root, returning empty result.")
            return []
        # print("comb optimizer starting run.")
        self.create_stats_table()  # in order to save stat info
        i = 1
        res = []
        while not self.isDone():
            start_node = self.get_start_node()  # get start node
            path = self.search_algo.run(start_node, self.start_time, self.time_per_region)  # run search from start node
            if path is None:
                break
            if len(path) != 0:
                self.optim_set.update(path)  # update the final solution

            # self.insert_stats(i)  # save stat info
            i += 1

        # if self.insert_stats is None:
        #     print("No match found in ", self.region, ". Consider giving extra time per region.")
        self.finish_stats_operation()

        return [node.getOffer() for node in self.optim_set.returnBest()]

    def isDone(self) -> bool:
        return time.time() - self.start_time > self.time_per_region


class Node:
    # declare node_cache dict with type annotation
    node_cache: dict = {}
    verbose = False

    @staticmethod
    def getGroupHash(group_set) -> int:
        group_set_hashable_parts = []
        for group in group_set:
            group_hashable_parts = []
            for module in group[0]:
                module_hashable_parts = []
                for component in module:
                    module_hashable_parts.append(hash(component.component_name))
                group_hashable_parts.append(hash(tuple(sorted(module_hashable_parts))))
            group_set_hashable_parts.append(hash(tuple(sorted(group_hashable_parts))))

        group_set_hashable = tuple(sorted(group_set_hashable_parts))
        return hash(group_set_hashable)

    def __init__(self, partitions, node_depth: int, price_calc):
        self.price_calc = price_calc
        self.node_depth = node_depth
        self.partitions = copy.deepcopy(partitions)
        self.offer = self.__calc_offer()
        if self.offer is not None:
            self.price = self.offer.total_price
        else:
            self.price = np.inf

        self.sons = None
        Node.node_cache[self.hashCode()] = self
        if Node.verbose:
            print(f"Node.__init__;\
            hash: {self.hashCode()}\
            , depth: {self.getDepth()}\
            , total_score: {self.price}")

    def __calc_offer(self):
        modules = []
        for group in self.partitions:
            combination = group[0]  # each group has 1 combination
            for module in combination:
                modules.append(module)

        return self.price_calc(Offer(modules, None))

    def getDepth(self):
        return self.node_depth

    def getPrice(self):
        return self.price

    def getOffer(self):
        return self.offer

    def hashCode(self) -> int:
        return Node.getGroupHash(self.partitions)

    @staticmethod
    def hashCodeOfPartition(partition) -> int:
        return Node.getGroupHash(partition)

    def __append_new_node(self, container, combination, combination_index, module1, module1_index, module2,
                          module2_index):
        """combine 2 modules to make new node.

        Args:
            container (_type_): container of new node.
            combination (_type_): the combination of 2 received modules.
            combination_index (_type_): index of combination
            module1 (_type_): the first module to create the node from.
            module1_index (_type_): index of first module
            module2 (_type_): the second module to create the node from.
            module2_index (_type_): index of second module
        """
        new_combination = copy.deepcopy(combination)
        new_module = copy.deepcopy(module1 + module2)
        del new_combination[max(module1_index, module2_index)]
        del new_combination[min(module1_index, module2_index)]
        new_combination.append(new_module)

        new_partition = copy.deepcopy(self.partitions)
        new_partition[combination_index][0] = new_combination

        if Node.hashCodeOfPartition(new_partition) in Node.node_cache:
            container.append(Node.node_cache[Node.hashCodeOfPartition(new_partition)])
        else:
            container.append(Node(new_partition, self.getDepth() + 1, self.price_calc))

    @staticmethod
    def random_node_from(start_node):
        new_partition = copy.deepcopy(start_node.partitions)
        depth_calc = 0
        for i, group in enumerate(start_node.partitions):
            combination = group[0]  # each group has 1 combination

            combination_number = len(combination)
            num_final_modules = np.random.choice(combination_number)
            if num_final_modules == 0:
                continue
            new_modules_group = np.random.choice(num_final_modules, size=combination_number)
            num_final_modules = np.max(new_modules_group) + 1
            new_combination = [[] for _ in range(num_final_modules)]
            for index, combination_index in enumerate(new_modules_group):
                new_combination[combination_index] += combination[index]

            new_combination = [new_combination[i] if new_combination[i] != [] else None for i in
                               range(num_final_modules)]
            new_combination = list(filter(None, new_combination))

            new_partition[i][0] = copy.deepcopy(new_combination)
            depth_calc += combination_number - len(new_combination)

        if Node.hashCodeOfPartition(new_partition) in Node.node_cache:
            new_node = Node.node_cache[Node.hashCodeOfPartition(new_partition)]
        else:
            new_depth = start_node.getDepth() + depth_calc
            new_node = Node(new_partition, new_depth, start_node.price_calc)

        return new_node

    def calcProportionSons(self, proportion_amount_to_develop):  # for example, 0.1
        sons = []
        for i, group in enumerate(self.partitions):
            combination = group[0]  # each group has 1 combination

            for j, module1 in enumerate(combination):
                for k, module2 in enumerate(combination):
                    if j < k:
                        prob = np.random.binomial(1, proportion_amount_to_develop)
                        if prob == 1:
                            self.__append_new_node(sons, combination, i, module1, j, module2, k)
        return sons

    def calcAllSons(self):
        if self.sons is None:
            self.sons = []
            for i, group in enumerate(self.partitions):
                combination = group[0]  # each group has 1 combination
                for j, module1 in enumerate(combination):
                    for k, module2 in enumerate(combination):
                        if j < k:
                            self.__append_new_node(self.sons, combination, i, module1, j, module2, k)


class OptimumSet:
    def __init__(self, k: int):
        """the table holds the best k seen so far in terms of price.
            requires that the elements inserted will have the method 'getPrice' which should
            return a float."""
        self.k = k
        self.table: list = []  # contain hashcode

    def update(self, visited_nodes: list):
        """considers the list of new nodes, such that the resulting set of nodes will be the 'k' best nodes
            seen at any update. The ordering the nodes is given by their 'getPrice()' method."""
        candidates = self.table + [node.hashCode() for node in visited_nodes if (not (node.hashCode() in self.table))]
        candidates.sort(key=lambda hashcode: Node.node_cache[hashcode].getPrice())
        self.table = candidates[:self.k]

    def returnBest(self):
        """returns the 'k' nodes with the best price seen so far.
        If not seen 'k' nodes yet, returns a list shorter than 'k'."""
        return [Node.node_cache[hashcode] for hashcode in self.table]


class ResetSelector:
    class Candidate():
        def __init__(self, node: Node):
            """The 'self.reachable_bonus' is a variable used in calculating the exploitation score for
                this candidate.
                 * Each node that can be reached from this candidate has a 'reachable_bonus' associated
                with it and the candidate.
                 * At any givem time, the candidate will save the maximum 'reachable_bonus' that it gets from
                any nodes that have been reached in runs starting from itself."""
            self.node = node
            self.total_score = None
            self.subtree_price_penalty = -self.node.getPrice()
            self.hash = None

    def __init__(self, candidate_list_size: int, num_componants: int, root: Node, exploitation_score_price_bias,
                 exploration_score_depth_bias, exploitation_bias, verbose=True):
        """ The reset-selector remembers a list of the best candidates (candidate nodes) seen so far,
            list is saved at: self.top_candidates.
            The parameter 'k' is the maximum allowed size for the candidate list."""
        self.verbose = verbose
        self.top_candidates = [ResetSelector.Candidate(root)]
        self.candidate_list_size = int(candidate_list_size)
        self.num_componants = num_componants

        # reachable_bonus_formula_base is calculated here so we only have to calculate it once.
        self.penalty_base = 10 ** (1.0 / num_componants)

        # hyperparameters:
        self.exploitation_score_price_bias = exploitation_score_price_bias
        self.exploration_score_depth_bias = exploration_score_depth_bias
        self.exploitation_bias = exploitation_bias

        self.updateTotalScores()

    def getStartNode(self) -> Node:
        """this method represents the main functionality of the reset-selector: based on all data seen so far
            - the reset-selector will return the the node it thinks the next run should start from."""
        scores_list = [candidate.total_score for candidate in self.top_candidates]
        scores_arr = np.array(scores_list)
        try:
            selected_node_idx = sampleFromWeighted(scores_arr)
        except:
            print("sample from weighted raised err, scores list: ", scores_list)
            return self.top_candidates[0].node

        selected_candidate = self.top_candidates[selected_node_idx]
        if self.verbose:
            print(f"ResetSelector.getStartNode;\
                hash: {selected_candidate.node.hashCode()}\
                , depth: {selected_candidate.node.getDepth()}\
                , total_score: {selected_candidate.total_score}")
        return selected_candidate.node

    def update(self, path: list):
        """'path' is a list of nodes seen in the last run the serach algorithm.
            this method will update in state of the reset selector - to consider the nodes seen in last search run.

            The order of nodes in 'path' is exprected to be the same order as the nodes were seen in the search.

            Calling this method will also cause the reset-selector to re-calculate the total scores for each
            of the candidates saved within it."""
        # consider all nodes seen in last path as candidates:
        candidate_dict = {candidate.node.hashCode(): candidate for candidate in self.top_candidates}
        last_candidate = None
        for node in reversed(path):
            # add the new node to set of candidates if it's not already there:
            node_hash = node.hashCode()
            if not node_hash in candidate_dict:
                candidate_dict[node_hash] = ResetSelector.Candidate(node)
            candidate = candidate_dict[node_hash]

            # update the subtree penalty of the candidate base on path:
            if last_candidate is not None and candidate is not None:
                candidate.subtree_price_penalty = \
                    max(
                        candidate.subtree_price_penalty,
                        last_candidate.subtree_price_penalty * self.penalty_base
                    )
            last_candidate = candidate

        # update the list of top candidates and re-calculate total scores for all candidates currently saved:
        self.top_candidates = [item for item in candidate_dict.values()]
        self.updateTotalScores()
        # if 0 in [c.total_score for c in self.top_candidates]:
        #     raise Exception("ResetSelector.update: error: a candidates has a total score of 0.")

        # sort the list of top candidates and throw away the candidates that are not in the top k:
        self.top_candidates = sorted(self.top_candidates, key=lambda candidate: candidate.total_score)
        self.top_candidates = self.top_candidates[:self.candidate_list_size]

    def updateTotalScores(self) -> list:
        """updates the total scores (floats) of all candidates in 'self.top_candidates'."""
        ration_scores = self.calcRationScores()
        tation_scores = self.calcTationScores()
        tation_bias = self.getCurrentTationBias()

        total_scores = tation_bias * tation_scores + (1 - tation_bias) * ration_scores
        for idx in range(len(self.top_candidates)):
            self.top_candidates[idx].total_score = total_scores[idx]
        if np.all(total_scores < 1e-6):
            total_scores = np.ones_like(total_scores, dtype=np.float)
        return []

    def getCurrentTationBias(self) -> float:
        """get the current exploitation bias, this represents the current preference of the algorithm for exploitation
            over exploration."""
        return self.exploitation_bias

    @staticmethod
    def normalizeArray(arr: ndarray) -> ndarray:
        # minmax normalization:
        diff = arr.max() - arr.min()
        if diff == 0:
            return ones_like(arr) / 2
        else:
            return (arr - arr.min()) / diff

        # return arr/np.sum(arr) #normalise according to L1
        # return arr/np.linalg.norm(arr)#normalize according to L2

    def calcRationScores(self) -> ndarray:
        """calculates the exploration scores of all candidates in 'self.top_candidates' and returns scores
            in list of floats in same order."""
        uniqueness_scores = self.calcUniquenessScores()
        depth_scores = self.calcDepthScores()
        exploration_scores = ResetSelector.normalizeArray(self.exploration_score_depth_bias * depth_scores
                                                          + (1 - self.exploration_score_depth_bias) * uniqueness_scores)

        return exploration_scores

    def calcDepthScores(self) -> ndarray:
        """Calculate the 'depth score' for each candidate in 'self.top_candidates'.
            The deeper the candidate's node - the higher the depth score."""
        depths = np.array([c.node.getDepth() for c in self.top_candidates])
        return ResetSelector.normalizeArray((depths - self.num_componants) * (depths - self.num_componants))

    def calcUniquenessScores(self) -> ndarray:
        """Calculate the 'uniqueness score' for each candidate in 'self.top_candidates'.
            This score will be highest for nodes that are very different from the other nodes in 'top_candidates'."""
        nodes_list = [c.node for c in self.top_candidates]
        distances = self.combinationDistancesFormula(nodes_list)
        return ResetSelector.normalizeArray(distances)

    def getCompResources(self, component: Component) -> ndarray:
        """given a component, return a list of resources
            that this component requires."""
        return np.array([component.vCPUs, component.memory, component.network])

    def getModuleResourceVector(self, module: list) -> ndarray:
        """give a module (a list of components) return an array of total resource
            requirements of all components in the module.
            If an empty module is given, the method returns None"""
        if len(module) == 0:
            return None
        total_resources = self.getCompResources(module[0])
        for idx in range(1, len(module)):
            total_resources += self.getCompResources(module[idx])
        return total_resources

    def getResourceDistribution(self, node: Node) -> ndarray:
        """given a node that represents a combination, return a 2d array,
            The first dimention relates to each module,
            the second dimention to each resource."""
        first_comb = node.partitions[0]  # need to subscript again here?
        return np.stack([self.getModuleResourceVector(ls[0]) for ls in first_comb])

    def calcVectorDistributionDistatnce(distr1: ndarray, distr2: ndarray) -> float:
        """given two distributions of vectors, calculate a distance between these two distributions.
            this is currently just the difference between the average resource requirments, and not KL-Div as planned."""
        avg1 = average(distr1, axis=0)
        avg2 = average(distr2, axis=0)
        return np.linalg.norm(avg1 - avg2)

    def combinationDistancesFormula(self, node_list: list) -> ndarray:
        """Implementation of formula for calculating 'distance' for all nodes to all other nodes.
            The input is a list of combinations, and the output is an array of floats where the i'th float
            represents the average 'distance' of i'th node from the rest of the nodes in the input list.

            Input is in the form of list<Node>."""
        all_distributions = [self.getResourceDistribution(node) for node in node_list]
        all_distances = np.stack([
            np.array([
                ResetSelector.calcVectorDistributionDistatnce(distr1, distr2)
                for distr2 in all_distributions
            ])
            for distr1 in all_distributions
        ])
        # the i,j cell in 'all_distances' should contain the distance between the distributions of the i'th node and the j'th node.
        # the average distance from the i'th node will be the average value of the i'th row.
        return np.average(all_distances, axis=0)

    def calcTationScores(self) -> ndarray:
        """calculates the explotation scores of all candidates in 'self.top_candidates' and returns scores
            in an array of floats with a corresponding order."""
        reachable_bonus_scores = ResetSelector.normalizeArray(
            np.array([c.subtree_price_penalty for c in self.top_candidates])
        )
        price_scores = ResetSelector.normalizeArray(np.array([-c.node.price for c in self.top_candidates]))
        exploitation_scores = ResetSelector.normalizeArray(self.exploitation_score_price_bias * price_scores
                                                           + (
                                                                       1 - self.exploitation_score_price_bias) * reachable_bonus_scores)

        return exploitation_scores


class SearchAlgorithm:
    def __init__(self,
                 develop_mode: DevelopMode,
                 get_next_mode: GetNextMode,
                 num_components: int,
                 proportion_amount_node_sons_to_develop=0.1
                 ):
        self.temperature = 0
        self.temperature_increment_pace = 1
        self.proportion_amount_node_sons_to_develop = proportion_amount_node_sons_to_develop
        self.develop_mode = develop_mode
        self.get_next_mode = get_next_mode
        self.num_components = num_components
        self.base = (0.9 / self.proportion_amount_node_sons_to_develop) ** (float(2) / self.num_components)

    def run(self, start_node: Node, start_time, time_per_region) -> list:
        """returns the list of nodes visited in the run"""
        self.update_temperature()
        path: list = []
        next_node = start_node

        while not self.isDone(start_time, time_per_region):
            if next_node.getPrice() == np.inf:
                return path
            path.append(next_node)
            next_node = self.get_next(next_node)  # implement the search algorithm
            if next_node is None:
                return path
        return path

    def isDone(self, start_time, time_per_region) -> bool:
        return time.time() - start_time > time_per_region

    def __get_next_greedy(self, node: Node, sons):
        best = None
        for son in sons:
            son_price = son.getPrice()
            if (best is None) or (son_price > node.price and son_price > node.price):
                best = son
        return best

    def __get_next_alg(self, node: Node, sons):
        flag = self.is_choosing_downgrades()  # annealing part
        improves, downgrades = SearchAlgorithm.split_sons_to_improves_and_downgrades(sons, node.getPrice())
        # if any(map(lambda x: x.getPrice()!=np.inf, downgrades)):
        #     print(f"FOUND WORST SON")
        try:
            if (downgrades.shape[0] != 0) and flag:
                return SearchAlgorithm.get_son_by_weights(downgrades)
            elif improves.shape[0] != 0:
                return SearchAlgorithm.get_son_by_weights(improves)
            else:
                return None
        except:
            return None

    def calc_sons(self, node):
        sons = []
        if self.develop_mode == DevelopMode.ALL:
            node.calcAllSons()
            sons = node.sons
        elif self.develop_mode == DevelopMode.PROPORTIONAL:
            cur_proportion = min(
                self.proportion_amount_node_sons_to_develop * (self.base ** (node.getDepth())),
                1
            )
            # print(f"{cur_proportion=}, {node.getDepth()=}")
            sons = node.calcProportionSons(cur_proportion)
        return sons

    def get_next(self, node: Node) -> Node:
        """get the chosen son to continue to in the next iteration"""
        sons = self.calc_sons(node)

        if self.get_next_mode == GetNextMode.STOCHASTIC_ANNEALING:
            return self.__get_next_alg(node, sons)
        elif self.get_next_mode == GetNextMode.GREEDY:
            return self.__get_next_greedy(node, sons)
        else:
            return self.__get_next_alg(node, sons)

    @staticmethod
    def get_son_by_weights(sons):
        """get the choosen son by the weights of the price diffs"""
        if sons.shape[0] == 0:
            return None

        index = sampleFromWeighted(np.array(sons[:, 1], dtype=np.float))
        return sons[index, 0]

    @staticmethod
    def split_sons_to_improves_and_downgrades(all_sons, cur_node_price):
        """split the sons to 2 ndarray of improves and downgrades. first column is sons, second column is the son
        corrsponding pricr diff"""
        improves = []
        downgrades = []

        for son in all_sons:
            price_diff = cur_node_price - son.getPrice()
            if price_diff > 0:
                improves.append([son, price_diff])
            else:
                downgrades.append([son, price_diff])

        return np.array(improves), np.array(downgrades)

    def is_choosing_downgrades(self):
        """return if we will choose a downgrade son"""
        prob_for_downgrade = 0.1 - 1.0 / (
                12 * np.exp(1.0 / (np.power(self.temperature, 0.9))))  # 12 is our lucky number...
        return (np.random.choice([0, 1], p=[1 - prob_for_downgrade, prob_for_downgrade])) == 1

    def update_temperature(self):
        """change the temperature according to the self.temperature_increment_pace"""
        self.temperature += self.temperature_increment_pace


def sampleFromWeighted(weight_arr: np.ndarray) -> int:
    if np.NaN in weight_arr:
        print(weight_arr)
        raise Exception("sampleFromWeighted: error: weight_arr contains NaN")

    sum_array = weight_arr.sum()
    if sum_array == 0:
        return np.random.choice(weight_arr.shape[0], p=np.ones_like(weight_arr) / weight_arr.shape[0])
    weight_arr1 = weight_arr / sum_array
    index = np.random.choice(weight_arr1.shape[0], p=weight_arr1)

    return index
