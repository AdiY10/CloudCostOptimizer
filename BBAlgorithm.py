from fleet_classes import Offer
import itertools
'''
This script creates all partitions for first-step/one-pair/all-pairs/BB algorithm
'''
def bestCurrentPrice(offers):
    sortedList = sorted(offers,key=lambda g: g.total_price)[:1]
    return sortedList[0].total_price

def addIndividuals(original):
    return [[el] for el in original]

def completeCombination(original,pairs):
    temp = []
    for p in pairs:
        individuals = list(set(original)-set(p))
        z = [p]
        for i in individuals:
            z.append([i])
        temp.append(z)
    temp.append(addIndividuals(original))
    return temp

def splitToPairs(comp):
    a=itertools.combinations(comp, 2) ##finding all possible pairs
    z = []
    for i in a:
        z.append(list(i))
    z.append(comp) ## all pairs, and the origin
    return completeCombination(comp,z) ##add to pairs, individuals

def partition2(collection):
    if not collection:
        print('There are no relevant configurations right now.')
    else:
        if len(collection) == 1:
            for c in collection[0]:
               yield c
            return
        for c in collection[0]:
            for smaller in partition2(collection[1:]):
                yield c + smaller

def simplestPartition(collection): ##first collection- all the group of components
    if not collection:
        print('There are no relevant configurations right now.')
    else:
        flat_list = []
        # Iterate through the outer list
        for element in collection:
            if type(element) is list:
                for item in element:
                    flat_list.append([item])
            else:
                flat_list.append([element])
        return [flat_list]

def separatePartitions(compList):
    return [c for c in simplestPartition(compList)]


def simplestComb(comp,app_size): ## comp- list of lists of the groups (shared/non-shared), which includes groups' components
    partitions = list(map(lambda i: separatePartitions(i), comp))  ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions)]


def OnePair(comp,app_size):
    partitions = list(map(lambda i: splitToPairs(i), comp))  ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions)]


def all_pairs(lst):
    if len(lst) < 2:
        yield []
        return
    if len(lst) % 2 == 1:
        # Handle odd length list
        for i in range(len(lst)):
            for result in all_pairs(lst[:i] + lst[i+1:]):
                yield result
    else:
        a = lst[0]
        for i in range(1,len(lst)):
            pair = [a,lst[i]]
            for rest in all_pairs(lst[1:i]+lst[i+1:]):
                yield [pair] + rest

def fillcomb(original,x):
    temp = []
    for o in original:
        for i in x:
            res = any(o in sublist for sublist in i)
            if not res:
                i.append([o])
            temp.append(i)
    return temp


def findAllPairs(comp):
    AllPairsList = []
    if len(comp) % 2 == 0:
        for x in all_pairs(comp):
            AllPairsList.append(x)
        AllPairsList.append(addIndividuals(comp))
    else:
        for x in all_pairs(comp):
            AllPairsList.append(x)
        AllPairsList = (fillcomb(comp, AllPairsList))
        AllPairsList.append(addIndividuals(comp))
    new_AllPairsList = []
    for elem in AllPairsList:
        if elem not in new_AllPairsList:
            new_AllPairsList.append(elem)
    return new_AllPairsList


def AllPairs(comp,app_size):
    partitions = list(map(lambda i: findAllPairs(i), comp))  ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions)]
