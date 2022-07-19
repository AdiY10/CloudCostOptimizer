"""This script creates all the partitions for the fleet offers."""

from fleet_classes import Offer


def generate_all_selections(sets_generator):
    """Generate all selections."""
    """given a generator of items that are iterable (set of sets),
    yield all possible combinations that result from selecting one item from each set.
    for example: powerset({{a, b}, {c, d}, {e}}) = {{a, c, e}, {a, d, e}, {b, c, e}, {b, d, e}}
    another example: powerset({}) = {}"""
    try:
        first_set = next(sets_generator)
        # print("got head: ", first_set)
        for tail_selections in generate_all_selections(sets_generator):
            # print("got tail: ", tail_selections)
            for head_selection in first_set:
                yield head_selection + tail_selections  # maybe [head_selection] + tail_selections ?
    except StopIteration:
        yield []


def partition2(iterable, region):
    """Partition2 function."""
    collection = list(iterable)
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


# def create_partitions(comp):
#     """Create_partitions function."""
#     return [c for c in partition(comp)]


def create_groups(
    comp, app_size, region
):  ## comp- list of the groups (shared/non-shared), which includes groups' components
    """Create groups function."""
    # original:
    # partitions = list(
    #     map(lambda i: partition(i), comp)
    # )  ## list of all components in each combination

    partitions = map(lambda i: partition(i), comp)
    # original:
    # return [Offer(p, app_size) for p in partition2(partitions, region)]
    # original2:
    # for p in partition2(partitions, region):
    for p in generate_all_selections(partitions):
        yield Offer(p, app_size)
