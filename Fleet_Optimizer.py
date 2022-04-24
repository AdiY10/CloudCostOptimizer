"""This script is for the non-web-based optimizer."""

import json
from fleet_classes import Offer, ComponentOffer
from fleet_offers import Component
from get_spot import SpotCalculator


calc = SpotCalculator()


def serialize_group(group: Offer, pricing, availability_zone):
    """Serialize group in fleet option."""
    res = dict()
    res["price"] = round(group.total_price, 5)
    res["EC2 Type"] = pricing
    res["region"] = group.region
    if availability_zone != "NA":
        res["availability_zone"] = availability_zone
    res["instances"] = list(map(lambda i: serialize_instance(i), group.instance_groups))
    return res


def serialize_instance(instance):
    """Lower level of serialize group in fleet option."""
    result = instance.instance.copy()
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
    pricing = filter["spot/onDemand"]
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
    availability_zone = (
        filter["availability_zone"] if "availability_zone" in filter else "NA"
    )
    architecture = filter["architecture"] if "architecture" in filter else "all"
    type_major = filter["type_major"] if "type_major" in filter else "all"
    offers_list = calc.get_fleet_offers(
        os, region, app_size, partitions, pricing, architecture, type_major
    )  ## add architecture
    res = list(
        map(lambda g: serialize_group(g, pricing, availability_zone), offers_list)
    )
    with open("FleetResults.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    run_optimizer()

