"""This script is for the non-web-based optimizer."""

import json
from fleet_classes import Offer, ComponentOffer
from fleet_offers import Component
from get_spot import SpotCalculator
import boto3
from LocalSearchAlgorithm.comb_optimizer import (
    DevelopMode,
    GetNextMode,
    GetStartNodeMode,
)

calc = SpotCalculator()


def use_boto3(instance_type, region, os):
    """Boto3 function."""
    client = boto3.client("ec2", region)
    filters = [{"Name": "instance-type", "Values": [instance_type]}]
    details = client.describe_spot_price_history(Filters=filters)
    if details["SpotPriceHistory"]:
        # print(min(details['SpotPriceHistory'], key=lambda x: x['SpotPrice']))
        details["SpotPriceHistory"] = [
            d for d in details["SpotPriceHistory"] if os in d["ProductDescription"]
        ]
        if details["SpotPriceHistory"]:
            min_instance = min(
                details["SpotPriceHistory"], key=lambda x: x["SpotPrice"]
            )
            if "Timestamp" in min_instance:
                del min_instance["Timestamp"]
                min_instance["SpotPrice"] = float(min_instance["SpotPrice"])
            return min_instance
    return {"region": region, "InstanceType": instance_type, "SpotPrice": "N/A"}
    # for i in range(len(details['SpotPriceHistory'])):
    # print(details['SpotPriceHistory'][i])


def serialize_group(group: Offer, payment, availability_zone, os):
    """Serialize group in fleet option."""
    res = dict()
    res["price"] = round(group.total_price, 5)
    res["EC2 Type"] = payment
    res["region"] = group.region
    res["instances"] = list(
        map(lambda i: serialize_instance(i, os), group.instance_groups)
    )
    return res


def serialize_instance(instance, os):
    """Lower level of serialize group in fleet option."""
    result = instance.instance.copy()
    if os == "linux":
        os = "Linux"
    if os == "windows":
        os = "Windows"
    file = open("config_file.json")
    config_file = json.load(file)
    if config_file["boto3 (enable / disable)"] == "enable":
        boto3_data = use_boto3(
            instance.instance["typeName"], instance.instance["region"], os
        )
        if isinstance(boto3_data["SpotPrice"], float):
            result["boto3_AZ"] = boto3_data["AvailabilityZone"]
            result["boto3_ProductDescription"] = boto3_data["ProductDescription"]
        result["boto3_spot_price"] = boto3_data["SpotPrice"]
    result["spot_price"] = instance.instance["spot_price"]
    result["components"] = list(
        map(lambda param: serialize_component(param), instance.components)
    )
    return result


def serialize_component(component: ComponentOffer):
    """Lower level of serialize group in fleet option."""
    result = dict()
    result["appName"] = component.app_name
    result["componentName"] = component.component_name
    return result


def run_optimizer(
    bruteforce,
    input_file_name="input_fleet.json",
    output_file_name="fleet_results.json",
    **kw
):
    """Run Optimizer- Fleet calculator."""
    file = open(input_file_name)
    shared_apps = []
    partitions = []
    app_size = dict()
    filter = json.load(file)
    file1 = open("config_file.json")
    config_file = json.load(file1)
    provider = config_file["Provider (AWS / Azure / Hybrid)"]
    for i, a in enumerate(filter["apps"]):
        app_size[i] = len(a["components"])
        if "share" in a and a["share"] is True:
            for c in a["components"]:
                shared_apps.append(Component(i, a["app"], c))
        else:
            app = []
            for c in a["components"]:
                app.append(Component(i, a["app"], c))
            if len(app) > 0:
                partitions.append(app)
    if len(shared_apps) > 0:
        partitions.append(shared_apps)
    os = filter["selectedOs"]
    if provider != "Hybrid":
        region = filter["region"] if "region" in filter else "all"
    else:
        region = "hybrid"
    payment = filter["spot/onDemand"] if "spot/onDemand" in filter else "spot"
    filter_instances = (
        filter["filterInstances"] if "filterInstances" in filter else "NA"
    )
    availability_zone = (
        filter["availability_zone"] if "availability_zone" in filter else "NA"
    )
    architecture = filter["architecture"] if "architecture" in filter else "all"
    type_major = filter["type_major"] if "type_major" in filter else "all"
    # affinity_list = filter["spot/onDemand"] if "spot/onDemand" in filter else "spot"
    offers_list = calc.get_fleet_offers(
        os,
        region,
        app_size,
        partitions,
        payment,
        architecture,
        type_major,
        filter_instances,
        provider,
        bruteforce,
        **kw
    )
    # print('Connecting to boto3')
    res = list(
        map(lambda g: serialize_group(g, payment, availability_zone, os), offers_list)
    )
    if not res:
        print("Couldnt find any match")
    else:
        pass
        # print("Optimizer has found you the optimal configuration. check it out")
    with open(output_file_name, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    file1 = open("config_file.json")
    config_file = json.load(file1)
    candidate_list_size = config_file["Candidate list size"]
    time_per_region = config_file["Time per region"]
    proportion_amount_node_sons_to_develop = config_file["Proportion amount node/sons"]
    verbose = True if config_file["Verbose"] == "True" else False
    INPUT_FILE = "input_fleet.json"
    OUTPUT_FILE = "fleet_results.json"
    brute_force = True if config_file["Brute Force"] == "True" else False
    ALG_PARAMETERS = {
        "candidate_list_size": candidate_list_size,
        "time_per_region": time_per_region,
        "exploitation_score_price_bias": 0.5,
        "exploration_score_depth_bias": 1.0,
        "exploitation_bias": 0.2,
        "sql_path": "Run_Statistic.sqlite3",
        "verbose": verbose,
        "develop_mode": DevelopMode.PROPORTIONAL,
        "proportion_amount_node_sons_to_develop": proportion_amount_node_sons_to_develop,
        "get_next_mode": GetNextMode.STOCHASTIC_ANNEALING,
        "get_starting_node_mode": GetStartNodeMode.RANDOM,
    }

    run_optimizer(brute_force, INPUT_FILE, OUTPUT_FILE, **ALG_PARAMETERS)
