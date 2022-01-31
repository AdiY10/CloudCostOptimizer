# Cloud Cost Optimizer
The goal of the project to provide the user an api for getting [AWS spot](https://aws.amazon.com/ec2/spot/) (or on-demand) best (cheapest) offers based on a given configuration.
The Optimizer first gets from the user application(s) requirements such as OS, region, cpu, memory, storage, network, etc.. 
After calculating All the options, the Optimizer suggests the user the cheapest configuration of spot instances to run their app.

## Getting Started 
#### Prerequisite
The Cloud Cost Optimizer requires Python3

#### Installation:
```
$ python -m pip install requests
$ pip3 install urllib3
$ pip install grequests
```

## Parameters:
The json file **input_fleet.json**- is an example of an appropriate input (see input_fleet_instructions.json for more explanations).
The user's workload should be in the **input_fleet.json** file- don't forget to change it.

#### Required parameters:
* vCPUs - min number of vCPUs in the instance 
* Memory (GB) - min memory (RAM) size in the instance 
* OS - operating system for the instance 
#### Optional parameters:
* Region - used if a specific region is required, otherwise, searches in all regions 
* Category - specifies the instance category- General Purpose, Compute Optimized, Memory Optimized, Media Accelerator Instance, Storage Optimized, GPU instance.
* Interruption Behavior- display only instances meeting a specific interruption behavior criteria (stop / hiberbate / terminate) - in case of using Spot instances.
* Interruption frequency- Represents the rate at which Spot will be reclaimed capacit (0- *< 5%*,1- *5-10%*,2- *10-15%*,3- *15-20%*, 4- *>20%*)
* Network - required network capacity
* IOPS (MiB I/O) - max IOPS per volume.
* Throughput (MiB/s)- max throughput per volume. 

## Results
The optimizer provides an API (.json file) which present the best configurations (limited to 10) for the current workload.
