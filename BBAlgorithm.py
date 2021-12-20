from fleet_classes import Offer

def bestCurrentPrice(offers):
    sortedList = sorted(offers,key=lambda g: g.total_price)[:1]
    return sortedList[0].total_price

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
        return flat_list

def separate_partitions(comp):
    return [[c for c in simplestPartition(comp)]]


def simplestComb(comp,app_size): ## comp- list of the groups (shared/non-shared), which includes groups' components
    partitions = list(map(lambda i: separate_partitions(i), comp))  ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions)]