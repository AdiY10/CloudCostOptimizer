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

# from single_instance_calculator import EbsCalculator
# from BBAlgorithm import simplest_comb
# from BBAlgorithm import one_pair
# from BBAlgorithm import find_all_poss_pairs
# from BBAlgorithm import best_current_price


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
        max_cpu = max(d["cpu"] for d in self.ec2_calculator.ec2.get(region))
        # min_cpu = min(d['cpu'] for d in self.ec2_calculator.ec2.get(region))
        return float(max_cpu)

    def calculate_limits_memory(self, region):
        """Calculate memory limits function."""
        max_memory = max(d["memory"] for d in self.ec2_calculator.ec2.get(region))
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
    #     return [[GroupedInstance(instances[i],components, pricing)] for i in range(min(len(instances),2))]

    def match_group(
        self, grouped_param: GroupedParam, region, pricing, architecture, type_major
    ):  ## finds best configuration for each combination
        """Match instance to group of components function."""
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
            [GroupedInstance(instances[i], components, pricing)]
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

    def get_offers(self, group: Offer, region, pricing, architecture, type_major):
        """Get offers function."""
        instances = []
        for i in group.remaining_partitions:
            instances.append(
                self.match_group(i, region, pricing, architecture, type_major)
            )  ## finds best configuration for each combination
            # for i in instances:
            #     print('i',i)
            #     for j in i:
            #         print('j',j)
            #         for k in j:
            #             for z in k.get_info():
            #                 print('i-',i,'j-', j, 'k-', k, 'k.instance-', k.instance, k.spot_price,
        #                 'k info-', k.get_info(),'z-',z.get_component_name())
        ### only for the First step algorithm! otherwise, don't execute the if
        if instances == [None]:  #### check!!!!
            print("there is no match in ", region, " region")
            instances.clear()
        instances = list(filter(None, instances))
        result = []
        for partition in partition2(instances):
            new_group = group.copy_group()
            new_group.total_price = sum(map(lambda i: i.total_price, partition))
            new_group.instance_groups = partition
            new_group.region = region
            result.append(new_group)
        return result  ## result is a list of Offer objects


def get_fleet_offers(
    params, region, os, app_size, ec2, pricing, architecture, type_major
):
    """Get fleet offers function."""
    res = []
    regions = region
    if not isinstance(region, list):
        regions = [region]
    calculator = FleetCalculator(ec2)
    if region == "all":
        regions = constants.regions.copy()
    for region_to_check in regions:
        # res_region = []
        # print('region: ', region)
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

        ## Brute-Force Algorithm- optimal results / more complex
        groups = create_groups(
            updated_params, app_size
        )  ## creates all the possible combinations
        for (
            group
        ) in (
            groups
        ):  ## for each combination (group) find N (=3) best offers ##Algorithm for optimal results
            res += calculator.get_offers(
                group, region_to_check, pricing, architecture, type_major
            )

        # ## First Step- match an instance for every component
        # firstBranch = simplest_comb(updated_params, app_size)
        # for combination in firstBranch:
        #     res += calculator.get_offers(combination, region_to_check, pricing, architecture, type_major)

        # ## one_pair Algorithm
        # pairs = one_pair(updated_params, app_size)
        # for combination in pairs:
        #     res += calculator.get_offers(combination, region_to_check, pricing, architecture, type_major)

        # ## AllPairs Algorithm
        # pairs = find_all_poss_pairs(updated_params, app_size)
        # for combination in pairs:
        #     res += calculator.get_offers(combination, region_to_check, pricing, architecture, type_major)

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
        #         res += calculator.get_offers(combination, region_to_check, pricing, architecture, type_major)
        # secondBranch = branchStep(firstBranch)
        # for combination in secondBranch:
        #     res += calculator.get_offers(combination, region_to_check, pricing, architecture, type_major)

        ## Full B&B Algorithm
        # Coming Soon

    res = list(filter(lambda g: g is not None, res))
    return sort_fleet_offers(res)
