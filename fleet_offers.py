"""This script handles the logic for fleet offers."""

import constants
from external_functions import sort_fleet_offers
from fleet_classes import (
    Component,
    GroupedInstance,
    GroupedParam,
    Offer,
    ComponentOffer,
)
from group_generator import create_groups, partition2
from single_instance_calculator import SpotInstanceCalculator
from LocalSearchAlgorithm.comb_optimizer import CombOptim


# from single_instance_calculator import EbsCalculator
# from LocalSearchAlgorithm.partitions_generator import simplest_comb
# from LocalSearchAlgorithm.partitions_generator import one_pair
# from LocalSearchAlgorithm.partitions_generator import find_all_poss_pairs
# from LocalSearchAlgorithm.partitions_generator import best_current_price


class FleetCalculator:
    """FleetCalculator class."""

    def __init__(self, ec2_calculator: SpotInstanceCalculator):
        """Initialize class."""
        self.ec2_calculator = ec2_calculator
        self.calculated_combinations: dict = {}
        self.bestPrice: dict = {}
        self.rep = 0
        self.count = 0

    def calculate_limits_cpu(self, region):
        """Calculate cpu limits function."""
        max_cpu = max(float(d["cpu"]) for d in self.ec2_calculator.ec2.get(region))
        # min_cpu = min(d['cpu'] for d in self.ec2_calculator.ec2.get(region))
        return float(max_cpu)

    def calculate_limits_memory(self, region):
        """Calculate memory limits function."""
        max_memory = max(
            float(d["memory"]) for d in self.ec2_calculator.ec2.get(region)
        )
        # min_memory = min(d['memory'] for d in self.ec2_calculator.ec2.get(region))
        return float(max_memory)

    def create_component_offer(self, component: Component, region):
        """Create component offer function."""
        # ebs = self.ebs_calculator.get_ebs_lowest_price
        # (region,component.storage_type,component.iops, component.throughput)[region]
        # if ebs is None:
        #     return None
        # storage_price = component.storage_size*ebs['price']
        return ComponentOffer(component.app_name, component.component_name)

    # def match_group_allregions(self,grouped_param:GroupedParam):
    #     instances = self.ec2_calculator.get_spot_estimations_allregions
    #                                           (grouped_param.total_vcpus, grouped_param.total_memory,
    #                                           'all', 'all', grouped_param.behavior,
    #                                           grouped_param.interruption_frequency,
    #                                           grouped_param.network, grouped_param.burstable)
    #     components = list(grouped_param.params)
    #     if len(instances) == 0:
    #         return None
    #     return [[GroupedInstance(instances[i],components, payment)] for i in range(min(len(instances),2))]

    def match_group(
        self,
        grouped_param: GroupedParam,
        region,
        payment,
        architecture,
        type_major,
        provider,
    ):  ## finds best configuration for each combination
        """Match instance to group of components."""
        sub_combination = []
        for single_component in grouped_param.params:
            sub_combination.append(single_component.get_component_name())
        sub_combination.append(region)
        sub_combination_str = str(sub_combination)
        if (
            sub_combination_str in self.calculated_combinations
        ):  ## prevent repetitive calculations
            instances = self.calculated_combinations[sub_combination_str]
            # self.rep = self.rep + 1 ## check number of repetitive calculation
            # print('repetition: ', self.rep)
            # print(sub_combination_str)
        else:
            limits_cpu = self.calculate_limits_cpu(region)
            limits_memory = self.calculate_limits_memory(region)
            if (
                grouped_param.total_vcpus <= limits_cpu
                and grouped_param.total_memory <= limits_memory
            ):
                instances = self.ec2_calculator.get_spot_estimations(
                    grouped_param.total_vcpus,
                    grouped_param.total_memory,
                    architecture,
                    type_major,
                    provider,
                    region,
                    "all",
                    grouped_param.behavior,
                    grouped_param.interruption_frequency,
                    grouped_param.network,
                    grouped_param.burstable,
                )
                combination = []
                for single_component in grouped_param.params:
                    combination.append(single_component.get_component_name())
                combination.append(region)
                combination_str = str(combination)
                self.calculated_combinations[combination_str] = instances
                # print(self.calculated_combinations.get(combination_str)[0].get('spot_price'))
                # self.bestPrice[combination_str] = instances
                # self.count = self.count + 1 ##check number of calculations
                # print ('number of first time calculations', self.count)
                # print(combination_str)
            else:
                return None
        components = list(grouped_param.params)
        if len(instances) == 0:
            return None
        # print(grouped_param.params)
        # if (len(grouped_param.params[0].component_name) < 2):
        #     return [[GroupedInstance(instances[i],components)] for i in range(min(len(instances),2))]
        return [
            [GroupedInstance(instances[i], components, payment)]
            for i in range(min(len(instances), 1))
        ]

    ## match_group function of the first version (with repetitions). Should stay, in order to check times improvement
    # def match_group(self,grouped_param:GroupedParam,region):
    #     instances = self.ec2_calculator.get_spot_estimations(grouped_param.total_vcpus, grouped_param.total_memory,
    #     region, 'all', grouped_param.behavior,
    #     grouped_param.interruption_frequency, grouped_param.network,grouped_param.burstable)
    #     components = list(map(lambda g: g.storage_offer, grouped_param.params))
    #     if len(instances) == 0:
    #         return None
    #     return [[GroupedInstance(instances[i],components)] for i in range(min(len(instances),3))]

    # def get_offers_allregions(self, group: Offer):
    #    """Get offers allregions function."""
    #    instances = []
    #    for i in group.remaining_partitions:
    #        instances.append(self.match_group_allregions(i))
    #    result = []
    #    instances = list(filter(None, instances))
    #    for partition in partition2(instances):
    #        new_group = group.copy_group()
    #        new_group.total_price = sum(map(lambda i: i.total_price, partition))
    #        new_group.instance_groups = partition
    #        new_group.region = partition.region
    #        result.append(new_group)
    #    return result  ## result is a list of Offer objects

    def get_offers(
        self, group: Offer, region, payment, architecture, type_major, provider
    ):
        """Get offers function."""
        instances = []
        for i in group.remaining_partitions:
            instances.append(
                self.match_group(i, region, payment, architecture, type_major, provider)
            )  ## finds best configuration for each combination
        instances = list(filter(None, instances))
        if len(instances) < len(group.remaining_partitions):
            return []
        result = []
        for partition in partition2(instances, region):
            new_group = group.copy_group()
            new_group.total_price = sum(map(lambda i: i.total_price, partition))
            new_group.instance_groups = partition
            new_group.region = region
            result.append(new_group)
        return result  ## result is a list of Offer objects

    def get_best_price(
        self, group: Offer, region, pricing, architecture, type_major, provider
    ):
        """Get offers function."""
        instances = []
        for i in group.remaining_partitions:
            instances.append(
                self.match_group(i, region, pricing, architecture, type_major, provider)
            )  ## finds best configuration for each combination
        instances = list(filter(None, instances))
        if len(instances) < len(group.remaining_partitions):
            return None

        best_group = None
        for partition in partition2(instances, region):
            new_group = group.copy_group()
            new_group.total_price = sum(map(lambda i: i.total_price, partition))
            new_group.instance_groups = partition
            new_group.region = region
            if best_group is None or new_group.total_price < best_group.total_price:
                best_group = new_group.copy_group()
        return best_group


def price_calc_lambda(
    calculator, region_to_check, payment, architecture, type_major, provider
):
    """Price calc with lambda usage."""
    return lambda comb: calculator.get_best_price(
        comb, region_to_check, payment, architecture, type_major, provider
    )


def check_anti_affinity(res):
    """Check if there are pairs that shouldn't be paired (anti-affinity)."""
    anti_affinity_list = []
    for stp in res.remaining_partitions:
        for stp1 in stp.params:
            anti_affinity_list.append(stp1.anti_affinity) if stp1 is not None else None
    anti_affinity_list = list(filter(None, anti_affinity_list))
    if anti_affinity(res, anti_affinity_list):
        return True
    return False


def check_affinity(res):
    """Check if there are pairs that must be paired together (affinity)."""
    affinity_list = []
    for stp in res.remaining_partitions:
        for stp1 in stp.params:
            affinity_list.append(stp1.affinity) if stp1 is not None else None
    affinity_list = list(filter(None, affinity_list))
    if affinity(res, affinity_list):
        return True
    return False


def affinity(res, affinity_list):
    """Check if there are pairs that must be paired together (affinity)."""
    flag = True
    all_comb = []
    for stp in res.remaining_partitions:
        comb = []
        for stp1 in stp.params:
            comb.append(stp1.component_name)
        all_comb.append(comb)
    for ind in affinity_list:
        if not compare_sublists(ind, all_comb):
            flag = False
    return flag


def anti_affinity(res, anti_affinity_list):
    """Check if there are pairs that shouldn't be paired (anti-affinity)."""
    all_comb = []
    for stp in res.remaining_partitions:
        comb = []
        for stp1 in stp.params:
            comb.append(stp1.component_name)
        all_comb.append(comb)
    for ind in anti_affinity_list:
        if compare_sublists(ind, all_comb):
            return True
    return False


def compare_sublists(list, listoflists):
    """Check if list listoflists contains list."""
    for sublist in listoflists:
        temp = [i for i in sublist if i in list]
        if sorted(temp) == sorted(list):
            return True
    return False


def get_fleet_offers(
    params,
    region,
    os,
    app_size,
    ec2,
    payment,
    architecture,
    type_major,
    config_file,
    provider,
    bruteforce,
    **kw
):
    """Get fleet offers function."""
    res = []
    regions = region
    if not isinstance(region, list):
        regions = [region]
    calculator = FleetCalculator(ec2)
    if region == "all":
        if provider == "AWS":
            regions = constants.AWS_REGIONS.copy()
        elif provider == "Azure":
            regions = constants.AZURE_REGIONS.copy()
        else:
            print("Wrong Provider in Config file")

    for region_to_check in regions:
        print("Searching in region", region_to_check)
        updated_params = params.copy()
        for pl in updated_params:
            for p in pl:
                storage_offer = calculator.create_component_offer(p, region_to_check)
                if storage_offer is None:
                    p.iops = 0
                    p.throughput = 0
                    p.storage_type = "all"
                    storage_offer = calculator.create_component_offer(
                        p, region_to_check
                    )
                p.storage_offer = storage_offer

        if bruteforce:  # Brute-Force Algorithm-optimal results / more complex
            groups = create_groups(
                updated_params, app_size, region_to_check
            )  ## creates all the possible combinations
            for combination in groups:  ## for each combination (group) find best offer
                res += calculator.get_offers(
                    combination,
                    region_to_check,
                    payment,
                    architecture,
                    type_major,
                    provider,
                )
                if not check_affinity(res[-1]):  ## Validating affinity condition
                    res = res[:-1]
                elif check_anti_affinity(
                    res[-1]
                ):  ## Validating anti-affinity condition
                    res = res[:-1]
                # if runtime > kw["time_per_region"]: ## in case of time limit per region- then stops the brute force
                #     break

        else:  ## Local Search Algorithm
            if "verbose" in kw and kw["verbose"]:
                print("running optimizer of region: ", region_to_check)
            price_calc = price_calc_lambda(
                calculator, region_to_check, payment, architecture, type_major, provider
            )
            results_per_region = 1
            for i in range(1, results_per_region + 1):
                res += CombOptim(
                    number_of_results=i,
                    price_calc=price_calc,
                    initial_seperated=updated_params,
                    region=region_to_check,
                    **kw
                ).run()

        # First Step- match an instance for every component
        # firstBranch = simplest_comb(updated_params, app_size)
        # for combination in firstBranch:
        #     res += calculator.get_offers(combination, region_to_check, pricing, architecture, type_major)
        # ## one_pair Algorithm
        # pairs = one_pair(updated_params, app_size)
        # for combination in pairs:
        #     res += calculator.get_offers(combination, region_to_check, payment, architecture, type_major)

        # ## AllPairs Algorithm
        # pairs = find_all_poss_pairs(updated_params, app_size)
        # for combination in pairs:
        #     res += calculator.get_offers(combination, region_to_check, payment, architecture, type_major)

        # ## B&B Algorithm- first step- cross region
        # print(updated_params)
        # if region == 'all':
        #     firstBranch = simplest_comb(updated_params, app_size)
        #     for combination in firstBranch:
        #         res += calculator.get_offers_allregions(combination)
        #     break
        # else:
        #     firstBranch = simplest_comb(updated_params, app_size)
        #     for combination in firstBranch:
        #         res += calculator.get_offers(combination, region_to_check, payment, architecture, type_major)
        # secondBranch = branchStep(firstBranch)
        # for combination in secondBranch:

        #     res += calculator.get_offers(combination, region_to_check, payment, architecture, type_major)

        ## Full B&B Algorithm
        # Coming Soon
    res = list(filter(lambda g: g is not None, res))
    return sort_fleet_offers(res)
