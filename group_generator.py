from fleet_classes import Offer

'''this file creates all the partitions for the fleet offers'''

def partition(collection):
    if len(collection) == 1:
        yield [ collection ]
        return
    first = collection[0]
    for smaller in partition(collection[1:]):
        # insert `first` in each of the subpartition's subsets
        for n, subset in enumerate(smaller):
            yield smaller[:n] + [[ first ] + subset]  + smaller[n+1:]
        # put `first` in its own subset
        yield [ [ first ] ] + smaller


def partition2(collection):
    if len(collection) == 1:
        for c in collection[0]:
           yield c
        return
    for c in collection[0]:
        for smaller in partition2(collection[1:]):
            yield c + smaller


def create_partitions(params):
    return [p for p in partition(params)]


def create_groups(params,app_size):
    partitions = list(map(lambda i: create_partitions(i),params))
    return [Offer(p, app_size) for p in partition2(partitions)]


