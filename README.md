# Cloud Cost Optimizer
This project offers the user an api for getting AWS spot (or on-demand) best offers based on a given configuration.

## Getting Started - prerequisite
The Cloud Cost Optimizer requires Python3

installation:
```
$ python -m pip install requests
$ pip3 install urllib3
$ pip install grequests
```


parameters:
maxCpu - max number of cpus
maxMemory - max memory size (GB)
maxStorage - max storage size (GB)
maxNetwork - network traffic size (GBs)
typeCategory - category of the instance type (General Purpose,Compute Optimized, Memory Optimized,Accelerated Computing,Storage Optimized)
OS - instance operating system (Linux,Windows)
result
A list of estimated prices for instance types.

Each offer has the type name, OS, on demand hourly price, historic spot hourly price, total estimated hourly price including other aws services (EBS,S3,CloudWatch). The list is sorted by total estimated price.


The list is divided into the following interruption behaviors:
termination
stop
hibernation

Cloud Cost optimizer
https://docs.google.com/document/d/1YED-mUN6uNbClHCi6DbKl0HOe4LwLfZrBdbs8u3WhoM/edit?usp=sharing
