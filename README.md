# Cloud Cost Optimizer
***
The goal of the project to provide the user an api for getting [AWS spot](https://aws.amazon.com/ec2/spot/) (on-demand in the future, stay tuned) best (cheapest) offers based on a given configuration.
The Optimizer first gets from the user application(s) requirements such as OS, region, cpu, memory, storage, network, etc.. 
After calculating All the options, the Optimizer suggests the user the cheapest configuration of spot instances to run their app.

## Getting Started 
****
To start using The Cloud Cost Optimizer, please clone this git repository:
```
git clone https://github.com/AdiY10/SpotCalculator.git
```
### Prerequisite
* The Cloud Cost Optimizer requires Python3
* Python 3.4 or newer installed. You can check the version by typing ```python3 --version``` in your command line. 
* You can download the latest Python version from [here](https://www.python.org/downloads/).

### Installation:
```
$ python -m pip install requests
$ pip3 install urllib3
$ pip install grequests
```

### Usage
```
$ python Fleet_Optimizer.py
```
Where the following command activate the Optimizer

## Parameters:
The json file **input_fleet.json**- is an example of an appropriate input (see input_fleet_instructions.json for more explanations).
The user's workload should be in the **input_fleet.json** file- don't forget to change it.
#### Example of an appropriate input json file:
```
{
    "selectedOs": "linux",
    "region": "all",
    "apps": [
        {
            "app": "App1",
            "share": true,
            "components": [
                {
                    "memory": 8,
                    "vCPUs": 4,
                    "network": 5,
                    "behavior": "terminate",
                    "frequency": "2",
                    "storageType": null,
                    "name": "Comp1"
                },
                {
                    "memory": 8,
                    "vCPUs": 3,
                    "network": 0,
                    "behavior": "hibernate",
                    "frequency": "3",
                    "storageType": null,
                    "burstable": true,
                    "name": "comp2"
                },
                                {
                    "memory": 8,
                    "vCPUs": 3,
                    "network": 0,
                    "behavior": "hibernate",
                    "frequency": "3",
                    "storageType": null,
                    "burstable": true,
                    "name": "comp5"
                }
            ]
        },
        {
            "app": "App2",
            "share": false,
            "components": [
                {
                    "memory": 10,
                    "vCPUs": 5,
                    "network": 0,
                    "behavior": "stop",
                    "frequency": "4",
                    "storageType": null,
                    "burstable": true,
                    "name": "Comp3"
                }
            ]
        }
    ]
}
```

Where we can see an input of two Applications (App1, App2), which uses linux Operation System.
App1 includes three components (Comp1, Comp2, Comp5), and App2 includes one component (Comp3). each component
has different resource requirements, which describes by the memory, vCPUs etc...

#### Required parameters:
* vCPUs - min number of vCPUs in the instance 
* Memory (GB) - min memory (RAM) size in the instance 
* OS - operating system for the instance 
#### Optional parameters:
* Region - used if a specific region is required, otherwise, searches in all regions 
* Category - specifies the instance category- General Purpose, Compute Optimized, Memory Optimized, Media Accelerator Instance, Storage Optimized, GPU instance.
* Interruption Behavior- display only instances meeting a specific interruption behavior criteria (stop / hibernate / terminate) - in case of using Spot instances.
* Interruption frequency- Represents the rate at which Spot will be reclaimed capacity (0- *< 5%*,1- *5-10%*,2- *10-15%*,3- *15-20%*, 4- *>20%*)
* Network - required network capacity
* IOPS (MiB I/O) - max IOPS per volume.
* Throughput (MiB/s)- max throughput per volume. 

## Results
The optimizer provides an API (.json file- *FleetResults.json*) which present the best configurations (limited to 10) for the current workload.
****The API consists of a list of items, where each item represents a result of the Optimizer, with the first item being the best result, and so on.**** 
### Example of the API- Best Result Only:
```
[
    {
        "price": 0.275,
        "instances": [
            {
                "onDemandPrice": 0.204,
                "region": "us-east-2",
                "cpu": "8",
                "ebsOnly": true,
                "family": "General purpose",
                "memory": "16",
                "network": "Up to 10 Gigabit",
                "os": "Linux",
                "typeMajor": "a1",
                "typeMinor": "2xlarge",
                "storage": "EBS only",
                "typeName": "a1.2xlarge",
                "discount": 81,
                "interruption_frequency": "<20%",
                "interruption_frequency_filter": 4.0,
                "spot_price": 0.0394,
                "Price_per_CPU": 0.004925,
                "Price_per_memory": 0.0024625,
                "components": [
                    {
                        "appName": "App2",
                        "componentName": "Comp3"
                    }
                ]
            },
            {
                "onDemandPrice": 0.344,
                "region": "us-east-2",
                "cpu": "8",
                "ebsOnly": false,
                "family": "Compute optimized",
                "memory": "16",
                "network": "Up to 10 Gigabit",
                "os": "Linux",
                "typeMajor": "c5ad",
                "typeMinor": "2xlarge",
                "storage": "1 x 300 NVMe SSD",
                "typeName": "c5ad.2xlarge",
                "discount": 78,
                "interruption_frequency": "<5%",
                "interruption_frequency_filter": 0.0,
                "spot_price": 0.076,
                "Price_per_CPU": 0.0095,
                "Price_per_memory": 0.00475,
                "components": [
                    {
                        "appName": "App3",
                        "componentName": "Comp4"
                    }
                ]
            },
            {
                "onDemandPrice": 0.6912,
                "region": "us-east-2",
                "cpu": "16",
                "ebsOnly": true,
                "family": "Compute optimized",
                "memory": "32",
                "network": "25 Gigabit",
                "os": "Linux",
                "typeMajor": "c6gn",
                "typeMinor": "4xlarge",
                "storage": "EBS only",
                "typeName": "c6gn.4xlarge",
                "discount": 77,
                "interruption_frequency": "5%-10%",
                "interruption_frequency_filter": 1.0,
                "spot_price": 0.1596,
                "Price_per_CPU": 0.009975,
                "Price_per_memory": 0.0049875,
                "components": [
                    {
                        "appName": "App1",
                        "componentName": "Comp1"
                    },
                    {
                        "appName": "App1",
                        "componentName": "comp2"
                    },
                    {
                        "appName": "App1",
                        "componentName": "comp5"
                    }
                ]
            }
        ],
        "region": "us-east-2"
    },
    {
        "price": 0.3,
        ...
    }
]
```