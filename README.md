# Cloud Cost Optimizer
[SYSTOR23_Adi Yehoshua Extended Version PDF](https://github.com/AdiY10/CloudCostOptimizer/blob/master/SYSTOR23_Adi%20Yehoshua_extended_version.pdf)

The goal of this project is to design and implement a scalable multi-cloud cost optimizer capable of calculating the best scheme for deploying a given arbitrary complex workload over a public (hybrid) cloud, thus reducing the involved monetary costs.
As an input, the optimizer receives the specification of the desired workload. It includes the resource requirements for each of the components comprising the workload, the connections between the components, and additional constraints. CCO analyzes this specification and calculates the mapping of the workload components to cloud resources (VM instances) that minimizes the expected monetary cost of deploying the application over a public cloud. This operation could be performed over a given single cloud provider (e.g., AWS) or over a set of cloud providers by splitting the workload over multiple clouds in accordance with the hybrid cloud paradigm.
The optimization problem to be solved by CCO is increasingly complex due to a combination of: (1) its inherently convoluted structure - each workload component must be allocated to some cloud resource and the number of ways they can share a resource is exponential; and (2) the multitude of parameters - for instance, AWS provides over 9000 combinations of a VM instance type, region, and operating system. To overcome the combinatorial hardness of the problem, our optimizer utilizes a combination of metaheuristics including Tabu search and simulated annealing.
The currently available version of the optimizer supports AWS and Azure. An intuitive and well-documented plugin interface makes it possible to easily support additional public clouds. CCO fully supports both on-demand / pay-as-you-go and spot instances, with the latter option allowing customers to save up to 90% in the instance cost. The tool can be used via a web-based UI and an API.
While the fully functional version of CCO is already available for use, there is no shortage of possible extensions and further improvements. To list a few examples, we are planning to replace a metaheuristic-based optimization algorithm with a reinforcement learning approach; to support planning ahead-of-time by predicting future prices of instances based on the market situation; to predict future interruption rates of spot instances and factor them in the calculations performed by CCO.

For further information:
* [AWS EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html)
* [AWS Spot Instances](https://aws.amazon.com/ec2/spot/)
* [Azure VMs](https://azure.microsoft.com/en-us/)
* [Azure Spot Virtual Macines](https://azure.microsoft.com/en-us/services/virtual-machines/spot/#features)
* [Hybrid Cloud](https://cloud.google.com/learn/what-is-hybrid-cloud)



## Getting Started
To start using The Cloud Cost Optimizer, please *clone* this git repository:
```
git clone https://github.com/AdiY10/CloudCostOptimizer.git
```
### Prerequisites
* The Cloud Cost Optimizer requires Python3- Python 3.4 or newer installed. You can check the version by typing ```python3 --version``` in your command line.
* You can download the latest Python version from [here](https://www.python.org/downloads/).

### Installation
```
$ python3 -m pip install requests
$ pip3 install urllib3
$ pip3 install grequests
$ pip3 install numpy
$ pip3 install boto3
```

### Usage
```
$ python3 CCO.py
```
Where the following command activate the Optimizer

## Parameters
The file **input_fleet.json** is an example of an input (see input_fleet_instructions.json for further information).
The user's workload should be in the **input_fleet.json** file- **don't forget to change it according to your needs.**
#### Example of an input json file:
```
{
    "selectedOs": "linux",
    "spot/onDemand": "spot",
    "region": ["eu-south-1", "eu-west-3", "us-east-2","us-east-1"],
    "filterInstances": ["a1","t3a","c5a.xlarge"],
    "Architecture": "all",
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
                    "affinity": "Comp2",
                    "name": "Comp1",
                },
                {
                    "memory": 8,
                    "vCPUs": 3,
                    "network": 0,
                    "behavior": "hibernate",
                    "frequency": "3",
                    "storageType": null,
                    "burstable": true,
                    "anti-affinity": "Comp3",
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

Where we can see an input of two Applications (App1, App2), which uses linux as their Operation System.
App1 includes three components (Comp1, Comp2, Comp5), and App2 includes only one component (Comp3). each component
has different resource requirements, which described by their memory, vCPUs etc...
### General parameters:
#### Required parameters:
* selectedOs - operating system (OS) for the workloads
* spot/onDemand - choose instances pricing option- **spot / on-Demand**
#### Optional parameters:
* Region - used if a specific region is required, otherwise, searches in all regions.
  * region defined as "all"- to look for the best configuration, in all regions
  * region defined as specific region, for example "us-east-2"- to look for the best configuration only in us-east-2
  * region defined as list of multiple regions- ["eu-west-1","eu-east-2","sa-east-1"]- to look for the best configuration in these regions
* filterInstances - used if specific instance types (major, minor or instance type) should not be displayed by Optimizer- for example, if major type a1, and instance type c5.large are not relevant, insert- filterInstances: ["a1","c5.large"]
* Architecture - processor architecture, can be selected as- 'all' / 'x86_64' (64-bit x86) / 'arm64' (64-bit arm) / 'i386' (32-bit) / 'x86_64_mac' (64-bit mac)
* AvailabilityZone - used if specific AZ is required
### App parameters:
##### Required parameters:
* app - name of app
* share - boolean parameter, indicates if the app can share instances with different apps
### Component parameters:
##### Required parameters:
* name - The name of the component
* memory - Min Memory (GB) size required in the instance
* vCPUs - Min number of vCPUs (virtual CPUs) required in the instance
##### Optional parameters:
* affinity - An affinity rule places a group of virtual machines on a specific Instance
* anti-affinity - An anti-affinity rule places a group of virtual machines on a different Instance
* type - required instance type ["General Purpose","Compute Optimized","Memory Optimized","Media Accelerator Instances","Storage Optimized","GPU Instances"]
* behavior- Displays only instances meeting a specific Interruption Behavior criteria (stop / hibernate / terminate) - *in case of using Spot instances.*
* frequency- Represents the rate at which Spot will be reclaimed capacity (0- *< 5%*,1- *5-10%*,2- *10-15%*,3- *15-20%*, 4- *>20%*) - *in case of using Spot instances.*
* typeMajor - Used when specific instance types are required. For example, when only C5, R5, A1 are supported- insert "typeMajor": ["c5", "r5", "a1"]
* Category - Specifies the instance category- General Purpose, Compute Optimized, Memory Optimized, Media Accelerator Instance, Storage Optimized, GPU instance.
* network - required network capacity (Gbs)
* size - Min storage size (GB)
* iops - Max IOPS (MiB I/O) per volume.
* throughput - Max throughput (MiB/s) per volume.

### Configuration file:
A configuration file with advanced settings is provided to the user, which allows him to edit default settings according to his preferences.
#### Example of a Configuration file:
```
{
    "Data Extraction (always / onceAday)": "onceAday",
    "boto3 (enable / disable)": "disable",
    "Provider (AWS / Azure / Hybrid)": "AWS",
    "Brute Force": "False",
    "Time per region": 1,
    "Candidate list size": 100,
    "Proportion amount node/sons": 0.0005,
    "Verbose": "True"
}
```
* When using Brute Force (marked as "True"), other parameters are irrelevant (Time per region,Candidate list size, * When using Brute Force (marked as "True"), other parameters are irrelevant (Time per region, Candidate list size, Proportion amount node/sons).
####Configuration Parameters
* Data Extraction- The frequency with which the data will be extracted
* boto3- Do the information retrieval using [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html). Note that in the case of enable, the data extraction process will be slower
* Provider- which cloud provider should be supported
* Brute Force- boolean parameter, indicates if the CCO should use BF In order to find the optimal solution, or not. Note that this algorithm suitable for less than 7 components. Otherwise, use Local Search Algorithm (explained below)
* [Other Parameters are hyperparameters](#hyperParameter) for the [Local Search algorithm](#local-search-algorithm-description)


## Results
The output of the Optimizer is a json file containing  a list of configurations. Each configuration represents an assignment of all application components to AWS instances.

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

## Local Search Algorithm Description

### General Description
The algorithm Is split into epochs.
each epoch is a combination of 2 phases:
  - **searching** - search for combiniation with minimal price. the search is based on Simulated Annealing and Stochastic Hill Climbing.
  - **selecting the next node to start searching from** -
    -  selects randomly.


#### Search Algorithm
the search is based on Simulated Annealing and Stochastic Hill Climbing.
```mermaid
flowchart TD
    O[initial node]
    A[decide proportion of sons to develop]
    B[develop proportion node sons]
    C[Split the group of sons:\n one that improve start node price  \n one that deteriorated start node price]
    D{decide to improve?}
    E[select one of the bad nodes stochastically,\n weighted by diff]
    F[select one of the good nodes stochastically,\n weighted by diff]
    G{selected?}
    H[finish search]
    I[continue search from selected node]

    O --> A -->B --> C -->D
    D -- no --> E --> G
    D -- yes --> F --> G

    G -- no --> H
    G -- yes --> I -->A
```

### HyperParameter
- **Candidate list size** - The maximum capacity of the Candidate list size from the Reset Selector.

- **Time per region** - The maximum time [seconds] the algorithm is allowed to run on each of the regions.

- **Proportion amount node sons to develop** - Initial proportion to develop at each epoch.

- **Exploitation score price bias** - Proportion between price score and subtree score.

- **Exploration score depth bias** - Proportion between depth score and uniqueness score.

- **Exploitation bias** -  Proportion between exploitation score and exploration score.
