"""This script creates all partitions for first-step/one-pair/all-pairs/BBAlgorithm."""

from fleet_classes import Offer
import itertools


def best_current_price(offers):
    """Best_current_price function."""
    sorted_list = sorted(offers, key=lambda g: g.total_price)[:1]
    return sorted_list[0].total_price


def add_individuals(original):
    """Add_individuals function."""
    return [[el] for el in original]


def complete_combination(original, pairs):
    """Complete_combination function."""
    temp = []
    for p in pairs:
        individuals = list(set(original) - set(p))
        z = [p]
        for i in individuals:
            z.append([i])
        temp.append(z)
    temp.append(add_individuals(original))
    return temp


def split_to_pairs(comp):
    """Split_to_pairs function."""
    a = itertools.combinations(comp, 2)  ##finding all possible pairs
    z = []
    for i in a:
        z.append(list(i))
    z.append(comp)  ## all pairs, and the origin
    return complete_combination(comp, z)  ##add to pairs, individuals


def partition2(collection):
    """Partition2 function."""
    if not collection:
        print("There are no relevant configurations right now.")
    else:
        if len(collection) == 1:
            for c in collection[0]:
                yield c
            return
        for c in collection[0]:
            for smaller in partition2(collection[1:]):
                yield c + smaller


def simplest_partition(collection):  ##first collection- all the group of components
    """Simplest_partition function."""
    if not collection:
        print("There are no relevant configurations right now.")
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


def separate_partitions(comp_list):
    """Separate_partitions function."""
    return [c for c in simplest_partition(comp_list)]


def simplest_comb(
    comp, app_size
):  ## comp- list of lists of the groups (shared/non-shared), which includes groups' components
    """Simplest_comb function."""
    partitions = list(
        map(lambda i: separate_partitions(i), comp)
    )  ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions)]


def one_pair(comp, app_size):
    """One_pair function."""
    partitions = list(
        map(lambda i: split_to_pairs(i), comp)
    )  ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions)]


def all_pairs(lst):
    """All_pairs function."""
    if len(lst) < 2:
        yield []
        return
    if len(lst) % 2 == 1:
        # Handle odd length list
        for i in range(len(lst)):
            for result in all_pairs(lst[:i] + lst[i + 1 :]):
                yield result
    else:
        a = lst[0]
        for i in range(1, len(lst)):
            pair = [a, lst[i]]
            for rest in all_pairs(lst[1:i] + lst[i + 1 :]):
                yield [pair] + rest


def fillcomb(original, x):
    """Fillcomb function."""
    temp = []
    for o in original:
        for i in x:
            res = any(o in sublist for sublist in i)
            if not res:
                i.append([o])
            temp.append(i)
    return temp


def find_all_pairs(comp):
    """Find_all_pairs function."""
    all_pairs_list = []
    if len(comp) % 2 == 0:
        for x in all_pairs(comp):
            all_pairs_list.append(x)
        all_pairs_list.append(add_individuals(comp))
    else:
        for x in all_pairs(comp):
            all_pairs_list.append(x)
        all_pairs_list = fillcomb(comp, all_pairs_list)
        all_pairs_list.append(add_individuals(comp))
    new_all_pairs_list = []
    for elem in all_pairs_list:
        if elem not in new_all_pairs_list:
            new_all_pairs_list.append(elem)
    return new_all_pairs_list


def find_all_poss_pairs(comp, app_size):
    """Find_all_poss_pairs function."""
    partitions = list(
        map(lambda i: find_all_pairs(i), comp)
    )  ## list of all components in each combination
    return [Offer(p, app_size) for p in partition2(partitions)]
