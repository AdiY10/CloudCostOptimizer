import json

from fleet_classes import Offer, ComponentOffer
from fleet_offers import Component
from get_spot import SpotCalculator

'''
This script is for the non-web-based optimizer
'''
calc = SpotCalculator()

def serialize_group(group:Offer, pricing):
    res = dict()
    res['price'] = round(group.total_price,5)
    res['instances'] = list(map(lambda i:serializeInstance(i),group.instance_groups))
    res['region'] = group.region
    return res

def serializeInstance(instance):
    result = instance.instance.copy()
    result['spot_price'] = instance.instance['spot_price']
    result['components'] = list(map(lambda param: serializeComponent(param),instance.components))
    return result

def serializeComponent(component: ComponentOffer):
    result = dict()
    result['appName'] = component.app_name
    result['componentName'] = component.component_name
    return result


def runOptimizer():
    file = open('input_Fleet.json')
    filter = json.load(file)
    pricing = filter['spot/onDemand']
    shared_apps = []
    partitions = []
    app_size = dict()
    for i, a in enumerate(filter['apps']):
        app_size[i] = len(a['components'])
        if 'share' in a and a['share'] == True:
            for c in a['components']:
                shared_apps.append(Component(i, a['app'], c))
        else:
            app = []
            for c in a['components']:
                app.append(Component(i, a['app'], c))
            if len(app) > 0:
                partitions.append(app)
    if len(shared_apps) > 0:
        partitions.append(shared_apps)
    os = filter['selectedOs']
    region = filter['region'] if 'region' in filter else 'all'
    listOfOffers = calc.get_fleet_offers(os, region, app_size, partitions, pricing)
    res = list(map(lambda g: serialize_group(g,pricing), listOfOffers))
    with open('FleetResults.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    runOptimizer()
