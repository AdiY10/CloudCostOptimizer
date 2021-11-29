from flask import Flask, jsonify, request
import json
from flask_cors import CORS, cross_origin

from fleet_classes import Offer, ComponentOffer
from fleet_offers import Component
from get_spot import SpotCalculator
from FindPrice import GetPriceFromAWS


calc = SpotCalculator()
AWSPrice = GetPriceFromAWS()
app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/getPrices', methods=['POST'])
@cross_origin()
def get_spot_prices():
    if(request.method == 'POST'):
        filter = request.get_json()
        os = filter['selectedOs']
        vCPUs = float(filter['vCPUs'])
        memory = float(filter['memory'])
        storage_size = float(filter['size'])
        region = filter['selectedRegion'] if 'selectedRegion' in filter else 'all'
        type = filter['type'] if 'type' in filter else 'all'
        behavior = filter['behavior'] if 'behavior' in filter else 'terminate'
        storage_type = filter['storageType'] if 'storageType' in filter and filter['storageType'] is not None else 'all'
        iops = float(filter['iops']) if 'iops' in filter and filter['iops'] is not None else 0
        throughput = float(filter['throughput']) if 'throughput' in filter and filter['throughput'] is not None else 0
        frequency = float(filter['frequency']) if 'frequency' in filter else 4
        network = float(filter['network']) if 'network' in filter else 0
        burstable  = True
        if network > 0:
            burstable = filter['burstable'] == True if 'burstable' in filter else False
        AWSPrices = AWSPrice.calculatePrice()
        res = calc.get_spot_estimations(os, vCPUs, memory,storage_size,AWSPrices , region, type, behavior, storage_type, iops, throughput, frequency, network,burstable)
        return jsonify(res)
    else:
        return jsonify()



"""
POST endpoint to get spot fleet hourly price estimations
body: configuration for fleet, i.e apps,components and other optional configurations
    dto = {
        selectedOs: <str>               REQUIRED, requested instances os. options: linux,windows
        region: <str>                   OPTIONAL, region for instances. options: us-east-2 etc. (see readme for full options)
        apps: [                         REQUIRED, list of app specifications
            {
            name: <str>                 REQUIRED, name of app
            share: <str>                REQUIRED, set to true if app can share instances with other apps
            components:[                REQUIRED, list of component specifications
                {
                    name: <str>         REQUIRED, name of component
                    cpu: <int>          REQUIRED, required cpu for component
                    memory: <int>       REQUIRED, required memory for component (GB)
                    network: <int>      OPTIONAL, component network consumption (GBs)
                    behavior: <str>     OPTIONAL, component required interruption behavior: options: terminate,stop,hibernation
                    interruptionFrequency: <int>    OPTIONAL, limit interruption frequency of the instances. options: 0-4 (see readme)
                    storageSize: <int>  REQUIRED, component storage size (GB)
                    IOPS: <int>         OPTIONAL, component required IOPS (MiB I/O)
                    throughput: <int>   OPTIONAL, component required throughput (MB/s)
                     
                }
                ]
            }
        ]
               
                                                                                                                                                                                                         
"""
@app.route('/getFleet', methods=['POST'])
@cross_origin()
def get_fleet_prices():
    if(request.method == 'POST'):
        filter = request.get_json()
        shared_apps = []
        partitions = []
        app_size = dict()
        for i,a in enumerate(filter['apps']):
            app_size[i]=len(a['components'])
            if 'share' in a and a['share'] == True:
                for c in a['components']:
                    shared_apps.append(Component(i,a['app'],c))
            else:
                app = []
                for c in a['components']:
                    app.append(Component(i,a['app'],c))
                partitions.append(app)
        if len(shared_apps)>0:
            partitions.append(shared_apps)
        os = filter['selectedOs']
        region = filter['region'] if 'region' in filter else 'all'
        res = calc.get_fleet_offers(os,region,app_size,partitions)
        return jsonify(list(map(lambda g: serialize_group(g),res)))
    else:
        return jsonify()

def serialize_group(group:Offer):
    res = dict()
    res['price'] = round(group.total_price,4)
    res['instances'] = list(map(lambda i:serializeInstance(i),group.instance_groups))
    res['region'] = group.region
    return res

def serializeInstance(instance):
    result = instance.instance.copy()
    result['total_price'] = round(instance.total_price,4)
    result['components'] = list(map(lambda param: serializeComponent(param),instance.components))
    return  result

def serializeComponent(component: ComponentOffer):
    result = component.ebs_instance.copy()
    result['appName'] = component.app_name
    result['componentName'] = component.component_name
    result['storagePrice'] = component.storage_price
    return result

if __name__ == '__main__':
    app.run()
