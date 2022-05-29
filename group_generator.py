"""This script creates all the partitions for the fleet offers."""

from fleet_classes import Offer


def partition2(collection, region):
    """Partition2 function."""
    if not collection:
        print("Could not find a match in ", region, " region")
    else:
        if len(collection) == 1:
            for c in collection[0]:
                yield c
            return
        for c in collection[0]:
            for smaller in partition2(collection[1:], region):
                yield c + smaller


def partition(collection):  ##first collection- all the group of components
    """Partition function."""
    if len(collection) == 1:
        yield [collection]
        return
    first = collection[0]
    for smaller in partition(collection[1:]):
        # insert `first` in each of the subpartition's subsets
        for n, subset in enumerate(smaller):
            yield smaller[:n] + [[first] + subset] + smaller[n + 1 :]
        # put `first` in its own subset
        yield [[first]] + smaller


def create_partitions(comp):
    """Create_partitions function."""
    return [c for c in partition(comp)]


def create_groups(
    comp, app_size, region
):  ## comp- list of the groups (shared/non-shared), which includes groups' components
    """Create groups function."""
    partitions = list(
        map(lambda i: create_partitions(i), comp)
    )  ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions, region)]
