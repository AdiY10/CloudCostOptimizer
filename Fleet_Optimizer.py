"""This script is for the non-web-based optimizer."""

import json
from fleet_classes import Offer, ComponentOffer
from fleet_offers import Component
from get_spot import SpotCalculator
import boto3


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


def serialize_group(group: Offer, pricing, availability_zone, os):
    """Serialize group in fleet option."""
    res = dict()
    res["price"] = round(group.total_price, 5)
    res["EC2 Type"] = pricing
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
    file = open("Config_file.json")
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


def run_optimizer():
    """Run Optimizer- Fleet calculator."""
    file = open("input_Fleet.json")
    filter = json.load(file)
    file1 = open("Config_file.json")
    config_file = json.load(file1)
    provider = config_file["Provider (AWS / Azure)"]
    shared_apps = []
    partitions = []
    app_size = dict()
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
    region = filter["region"] if "region" in filter else "all"
    pricing = filter["spot/onDemand"] if "spot/onDemand" in filter else "spot"
    filter_instances = (
        filter["filterInstances"] if "filterInstances" in filter else "NA"
    )
    availability_zone = (
        filter["availability_zone"] if "availability_zone" in filter else "NA"
    )
    architecture = filter["architecture"] if "architecture" in filter else "all"
    type_major = filter["type_major"] if "type_major" in filter else "all"
    offers_list = calc.get_fleet_offers(
        os,
        region,
        app_size,
        partitions,
        pricing,
        architecture,
        type_major,
        filter_instances,
        provider
    )
    # print('Connecting to boto3')
    res = list(
        map(lambda g: serialize_group(g, pricing, availability_zone, os), offers_list)
    )
    if not res:
        print("Couldnt find any match")
    else:
        print("Optimizer has found you the optimal configuration. check it out")
    with open("FleetResults.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_optimizer()