from fleet_classes import Offer

'''
This script creates all the partitions for the fleet offers
'''

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

def partition(collection): ##first collection- all the group of components
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


def create_partitions(comp):
    return [c for c in partition(comp)]


def create_groups(comp,app_size): ## comp- list of the groups (shared/non-shared), which includes groups' components
    partitions = list(map(lambda i: create_partitions(i),comp)) ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions)]


