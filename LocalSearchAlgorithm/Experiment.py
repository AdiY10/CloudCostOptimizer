from matplotlib import pyplot as plt
import CCO
import math
import json
import numpy as np
import os
import sqlite3
from multiprocessing import Process
from interp import average_curve
import time
import shutil


# ============================= File System Utilities =========================================

def to_json(collection, file_path: str)->None:
    with open(file_path, 'w') as file:
        json.dump(collection, file, indent=2)

def from_json(file_path: str):
    with open(file_path, 'r') as file:
        res = json.load(file)
    return res

def input_path_format(exp_dir_path: str, sample_idx: int)->str:
    return exp_dir_path+"/inputs/sample"+str(sample_idx)+".json"

def output_path_format(exp_dir_path: str, sample_idx: int, repetition: int)->str:
    return exp_dir_path+"/outputs/sample"+str(sample_idx)+"_repetition"+str(repetition)+".json"

def stats_path_format(exp_dir_path: str, sample_idx: int, repetition: int)->str:
    return exp_dir_path+"/stats/sample"+str(sample_idx)+"_repetition"+str(repetition)+".sqlite3"

def metadata_path_format(exp_dir_path: str)->str:
    return exp_dir_path+"/metadata.json"

# ============================= Names =========================================

control_parameter_names = {
    "component_count",
    "time_per_region",
    "significance"
}
search_algorithm_parameter_names = {
    "develop_mode",
    "proportion_amount_node_sons_to_develop",
    "get_next_mode",
    "get_starting_node_mode"
}
reset_algorithm_parameter_names = {
    "candidate_list_size",
    "exploitation_score_price_bias",
    "exploration_score_depth_bias",
    "exploitation_bias"
}
component_resource_type_names = {
    "cpu",
    "ram",
    "net"
}

# ============================= Implementation =========================================

def yellow(msg: str)->str:
    return '\033[93m'+msg+'\033[0m'

def red(msg: str)->str:
    return '\033[91m'+msg+'\033[0m'

def green(msg: str)->str:
    return '\033[92m'+msg+'\033[0m'

def blue(msg: str)->str:
    return '\033[94m'+msg+'\033[0m'

def bool_prompt(msg: str):
    print(green(msg+" [Y/n]"))
    i = input()
    return i == "y" or i == "Y"

def get_time_description(time_in_hours: float)->str:
    def trucated_str(num: float)->str:
        pre_dec_dot, post_dec_dot = str(num).split('.')
        return pre_dec_dot + '.' + post_dec_dot[:4]

    if time_in_hours < 1:
        time_in_minutes = time_in_hours*60
        if time_in_minutes < 1:
            return trucated_str(time_in_minutes*60) + " seconds" 
        else:
            return trucated_str(time_in_minutes) + " minutes"
    if time_in_hours > 24:
        return trucated_str(time_in_hours/24.0) + " days"
    else:
        return trucated_str(time_in_hours) + " hours"

def fetal_error(msg: str):
    print(red("Fetal Error: "+msg))
    exit(1)

class Flags:
    ALL = None
    LIST_ALL = 1
    NON_INCREASING = 2
    #'NON_INCREASING' flag means that given a set of 2d curves, take points from all functions together, 
    #sort by increasing x value and remove any points that increase the y value.
    CREATE = 3
    LOAD = 4
    
class Component:
    def __init__(self, cpu: int, ram: int, net: int):
        self.cpu = cpu
        self.ram = ram
        self.net = net

def make_experiment_dir(exp_dir_path: str):
    try:
        shutil.rmtree(exp_dir_path)
    except FileNotFoundError:
        pass
    except PermissionError:
        print("error: tried to create expriment dir at: '"+exp_dir_path+"', but got premission error.")
        exit(1)

    os.mkdir(exp_dir_path)
    for name in ["inputs", "outputs", "stats"]:
        os.mkdir(exp_dir_path+"/"+name)

def verify_dict_keys(d: dict, expected_keys: set):
        actual_keys = set(d.keys())
        if actual_keys != expected_keys:
            raise ValueError(f"Got wrong or missing dictionary keys:\n'{actual_keys=}'\n{expected_keys=}")

def dict_of_lists_to_list_of_dicts(dict_of_lists: dict)->list:
    """the function assumes all inner lists have the same lengths and there is at-least one list."""
    keys = list(dict_of_lists.keys())
    n = len(dict_of_lists[keys[0]])
    return [{key:dict_of_lists[key][idx] for key in keys} for idx in range(n)]

def invert_list(ls: list)->list:
    """turn list of lists inside out, function assumes all inner lists have same length.
        [[1,2,3], [4,5,6]] ---> [[1,4], [2,5], [3,6]]
        also, inner lists can also be tuples or sets insetead:
        [(1,2,3), (4,5,6)] ---> [[1,4], [2,5], [3,6]]
        
    When a list is longer than others, ignores all items at indices that are larger than the minimal list length."""
    min_len = min([len(l) for l in ls])
    return [[inner_list[idx] for inner_list in ls] for idx in range(min_len)]

def flatten_list_of_lists(ls: list)->list:
    res = []
    for inner_ls in ls:
        res += inner_ls
    return res

def listify(item, all_list_generator)->list:
    """if item is a list, return it.
        if 'item' is 'Flags.ALL' return the list created by second param
        otherwise - returns 'item' inside a list by itself.
        second parameter should be a function without arguments."""
    if type(item) == list:
        return item
    if item == Flags.ALL:
        return all_list_generator()
    return [item]

def run_samples(sample_list: list, retry: int, verbosealg: bool, pid: int, num_regions: int):
    print(green(f"process {pid}, starting. got {len(sample_list)} samples."))
    
    msg_head = f"process {blue(str(pid))}, "
    for sample in sample_list:
        start_time = time.time()
        sample.run(retry, verbosealg)
        time_in_hours = (time.time() - start_time)/(float(3600))
        exp_time = f"expected runtime: {blue(get_time_description(sample.expected_runtime(num_regions)))}"
        actual_time = f"actual runtime: {blue(get_time_description(time_in_hours))}"
        print(f"{msg_head}finished sample {blue(str(sample.sample_idx))}. {exp_time}, {actual_time}")

class Sample:
    @staticmethod
    def metadata_dict_format(
            control_parameters,
            search_algorithm_parameters,
            reset_algorithm_parameters,
            bruteforce
    ):
        return {
            "control_parameters" : control_parameters,
            "search_algorithm_parameters" : search_algorithm_parameters,
            "reset_algorithm_parameters" : reset_algorithm_parameters,
            "bruteforce" : bruteforce
        }

    @staticmethod
    def create(
            exp_dir_path: str, 
            sample_idx: int, 
            components: list, 
            control_parameters: dict,
            search_algorithm_parameters: dict,
            reset_algorithm_parameters: dict,
            region: str,
            bruteforce: bool = False
    ):
        verify_dict_keys(control_parameters, control_parameter_names)
        verify_dict_keys(search_algorithm_parameters, search_algorithm_parameter_names)
        verify_dict_keys(reset_algorithm_parameters, reset_algorithm_parameter_names)

        #create the algorithm input file:
        comp_dicts = [{
            "name"		:"component_"+str(idx),
            "vCPUs"		:comp.cpu,
            "memory"	:comp.ram,
            "network"	:comp.net
        } for idx, comp in enumerate(components)]

        algorithm_input_json_dict = {
            "selectedOs"		:"linux",
            "region"			:region,
            "spot/onDemand"		:"onDemand",
            "AvailabilityZone"	:"all",
            "Architecture"		:"all",
            "filterInstances"	:["a1", "t4g","i3","t3a","c5a.xlarge"],
            "apps" 				:[{
                "app"		:"App",
                "share"		:True,
                "components":comp_dicts
            }]
        }
        to_json(algorithm_input_json_dict, input_path_format(exp_dir_path, sample_idx))

        #create Sample object
        metadata = Sample.metadata_dict_format(
                control_parameters, 
                search_algorithm_parameters, 
                reset_algorithm_parameters, 
                bruteforce
        )
        return Sample(metadata, sample_idx, exp_dir_path)
    
    @staticmethod
    def load(
            exp_dir_path: str,
            sample_idx: int
    ):
        return Sample(from_json(metadata_path_format(exp_dir_path))[sample_idx], sample_idx, exp_dir_path)

    def __init__(self, metadata: dict, sample_idx: int, exp_dir_path: str):
        self.metadata = metadata
        self.sample_idx = sample_idx
        self.exp_dir_path = exp_dir_path
        
        self.component_count = self.metadata["control_parameters"]["component_count"]
        self.time_per_region = self.metadata["control_parameters"]["time_per_region"]
        self.segnificance = self.metadata["control_parameters"]["significance"]

    def run(self, retry: int, verbosealg: bool):
        search_algorithm_parameters = self.metadata["search_algorithm_parameters"]
        reset_algorithm_parameters = self.metadata["reset_algorithm_parameters"]
        control_parameters = self.metadata["control_parameters"]
        for repetition in range(control_parameters["significance"]):
            sample_attempts_left = retry
            def run_alg():
                CCO.run_optimizer(
                    **search_algorithm_parameters,
                    **reset_algorithm_parameters,
                    time_per_region = control_parameters["time_per_region"],
                    input_file_name = input_path_format(self.exp_dir_path, self.sample_idx),
                    output_file_name = output_path_format(self.exp_dir_path, self.sample_idx, repetition),
                    sql_path = stats_path_format(self.exp_dir_path, self.sample_idx, repetition),
                    verbose = verbosealg,
                    bruteforce = self.metadata["bruteforce"]
                )
            if retry > 0:
                while True: # This loop will end when no exceptions happen, or retried too many times.
                    try:
                        run_alg()
                    except Exception as e:
                        print(yellow("Error: Unknown exception occured:"))
                        print(e)
                        if sample_attempts_left <= 0:
                            print(yellow("too many errors, stopping run."))
                            raise e
                        sample_attempts_left -= 1
                        continue
                    break
            else:
                run_alg()

    def expected_runtime(self, num_regions: int)->float:
        return self.time_per_region*self.segnificance*float(num_regions)/3600.0
    
    def query_repetition(self, repetition: int, query: str)->list:
        db_path = stats_path_format(self.exp_dir_path, self.sample_idx, repetition)
        with sqlite3.connect(db_path) as conn:
            res = conn.execute(query)
        return list(res)

    def query_stats(self, query: str)->list:
        #old: return [self.query_repetition(repetition, query) for repetition in range(self.segnificance)]
        res = []
        for repetition in range(self.segnificance):
            try:
                res.append(self.query_repetition(repetition, query))
            except:
                print(yellow(f"Warning: could not query stats sample number {self.sample_idx} from experiment '{self.exp_dir_path}'."))
        return res

    def get_plot_axis(self, 
            region: str,
            x_variable: str = "INSERT_TIME", 
            y_variable: str = "BEST_PRICE", 
            normalize: bool = True,
            repetition: int = Flags.ALL,
            y_filter_func = lambda y: y != np.inf and y != math.inf
    )->tuple:
        """queries all entries related to this sample to create a plot describing the relation between
            the first and second query variables.
            'y_filter_func' should recive a 'y' value and return bool.
            any (x,y) pair where the filter outputs 'False' on 'y' will be removed from result."""
        query = f"SELECT {x_variable},{y_variable} FROM STATS WHERE REGION_SOLUTION = '{region}' ORDER BY {x_variable};"
        
        entries = flatten_list_of_lists(self.query_stats(query)) if repetition is Flags.ALL else self.query_repetition(repetition, query)
        entries = [(x,y) for x,y in entries if y_filter_func(y)]
        if normalize:
            min_y = min([y for x, y in entries])
            entries = [(x, y/min_y) for (x, y) in entries]
        if len(entries) == 0:#this happends when errors occur when loading the samples or the samples are empty. 'inver_list' cannot handle this case.
            return [[], []]
        return invert_list(entries)

def partition_tuples_list_by_field(entries: list, unique_field_idx: int):
    field_values = {entry[unique_field_idx] for entry in entries}
    return {value:[entry for entry in entries if entry[unique_field_idx] == value] for value in field_values}

# stat fields are: 0:INSERT_TIME, 1:NODES_COUNT, 2:BEST_PRICE, 3:DEPTH_BEST, 4:ITERATION, 5:REGION_SOLUTION

class Experiment:
    default_experiments_root_dir = "../experiments"

    def get_num_samples(self)->int:
        return len(self.samples)

    def query_each_sample(self, query: str)->list:
        return [sample.query_stats(query) for sample in self.samples]

    def get_regions_list(self)->list:
        regions = set()
        for sample_regions in self.query_each_sample("SELECT DISTINCT REGION_SOLUTION FROM STATS;"): 
            for repetition_regions in sample_regions:
                for region in repetition_regions:
                    regions.add(region[0])
        return list(regions)

    def get_static_region(self)->list:
        json_dict = from_json(input_path_format(self.exp_dir_path, 0))
        return json_dict["region"]

    ALL = None
    def plot(self, 
            x_variable: str = "INSERT_TIME",
            y_variable: str = "BEST_PRICE",
            regions: str = Flags.ALL,
            sample_indices = Flags.ALL,
            normalize: bool = True,
            repetition: int = Flags.ALL,
            granularity: int = 50,
            regions_aggregate = Flags.NON_INCREASING
    ):
        curves = self.get_plot_curves(x_variable, y_variable, regions, sample_indices, normalize, repetition, granularity, regions_aggregate)
        for xs, ys in curves:
            plt.plot(xs, ys)

        repetition_title = "all repetitions" if repetition == Flags.ALL else f"repeition:{repetition}"
        
        sample_indices = listify(sample_indices, lambda:list(range(self.get_num_samples())))
        regions = listify(regions, lambda:self.get_regions_list())# this is just so we know length
        region_tile = f"region:{regions[0]}" if len(regions) == 1 else f"{len(regions)} regions"
        
        plt.title(f"{repetition_title}, with {len(sample_indices)} samples, in {region_tile}")
        plt.xlabel(x_variable.lower().replace('_', ' '))
        plt.ylabel(y_variable.lower().replace('_', ' '))
        plt.show()

    def get_plot_curves(self, 
            x_variable: str = "INSERT_TIME",
            y_variable: str = "BEST_PRICE",
            regions: str = Flags.ALL,
            sample_indices = Flags.ALL,
            normalize: bool = True,
            repetition: int = Flags.ALL,
            granularity: int = 50,
            regions_aggregate = Flags.NON_INCREASING
    )->list:
        regions = listify(regions, lambda:self.get_regions_list())
        sample_indices = listify(sample_indices, lambda:list(range(self.get_num_samples())))

        all_times, all_prices = [], []
        for region in regions:
            region_curves = []
            for sample in [self.samples[idx] for idx in sample_indices]:
                sample_times, sample_prices = sample.get_plot_axis(region, x_variable, y_variable, normalize, repetition)
                #check and extrapolate (as straight line) if there is only one point:
                if len(sample_times)==1:
                    sample_times.append(sample_times[0]+1)#TODO: maybe add something other than '1' here?
                    sample_prices.append(sample_prices[0])

                sample_curve = np.array([[time, price] for time, price in zip(sample_times, sample_prices)])
                region_curves.append(sample_curve)    
            # return region_curves#fix!!!
            times, prices = average_curve(granularity, *region_curves)
            all_times.append(times)
            all_prices.append(prices)
        
        #aggregate different regions (as needed):
        if regions_aggregate == Flags.NON_INCREASING and len(all_times) > 1:
            all_times = flatten_list_of_lists(all_times)
            all_prices = flatten_list_of_lists(all_prices)
            flat_all_curves = sorted(list(zip(all_times, all_prices)), key = lambda t: t[0])
            min_price = math.inf
            for idx in range(len(flat_all_curves)):
                min_price = min(min_price, flat_all_curves[idx][1])
                flat_all_curves[idx] = (flat_all_curves[idx][0], min_price)
            all_curves = [([time for time,_ in flat_all_curves], [price for _,price in flat_all_curves])]
        else:
            all_curves = list(zip(all_times, all_prices))
        return all_curves
        

    def __init__(self, experiment_name: str, experiments_root_dir: str, samples: list):
        """this method is for internal use only, 'Experiment' objects should be created with the static methods 'create, load'."""
        self.experiment_name = experiment_name
        self.exp_dir_path = experiments_root_dir+"/"+self.experiment_name
        self.samples = samples

    @staticmethod
    def create(
            experiment_name: str,
            control_parameter_lists: dict,
            search_algorithm_parameter_lists: dict,
            reset_algorithm_parameter_lists: dict,
            component_resource_distirubtions: dict,
            bruteforce: bool = False,
            use_existing_inputs = False,
            experiments_root_dir: str = default_experiments_root_dir,
            force: bool = False,
            unique_sample_inputs: bool = True,
            region = "all"
    ):
        """use existing inputs is either false - meaning a neew set of intputs is created; otherwise it's
            the name of the experiment (name only) from which to take the input samples."""
        #verify input correctness:
        verify_dict_keys(control_parameter_lists, control_parameter_names)
        verify_dict_keys(search_algorithm_parameter_lists, search_algorithm_parameter_names)
        verify_dict_keys(reset_algorithm_parameter_lists, reset_algorithm_parameter_names)

        verify_dict_keys(component_resource_distirubtions, component_resource_type_names)

        control_parameter_dicts = dict_of_lists_to_list_of_dicts(control_parameter_lists)
        search_algorithm_parameter_dicts = dict_of_lists_to_list_of_dicts(search_algorithm_parameter_lists)
        reset_algorithm_parameter_dicts = dict_of_lists_to_list_of_dicts(reset_algorithm_parameter_lists)
        
        exp_dir_path = experiments_root_dir+"/"+experiment_name
        
        lengths = [len(ls) for ls in (
                list(control_parameter_lists.values())+
                list(search_algorithm_parameter_lists.values())+
                list(reset_algorithm_parameter_lists.values())
        )]
        if any([n != lengths[0] for n in lengths]):
            raise ValueError("expected all parameter lists to have same lengths.")
        num_samples = lengths[0]

        #create experiment files and objects
        sample_hw_requirments = lambda : {resource_name:component_resource_distirubtions[resource_name]() for resource_name in component_resource_type_names}
        if os.path.exists(exp_dir_path) and not force:
            if not bool_prompt(f"an experiment by the name '{experiment_name}' exists. override old experiment?"):
                exit(0)
        make_experiment_dir(exp_dir_path)

        if not use_existing_inputs:

            samples = []

            component_set_generator = lambda : [Component(**(sample_hw_requirments())) for _ in range(max(control_parameter_lists["component_count"]))]
            if not unique_sample_inputs:
                static_component_set = component_set_generator()
                component_set_generator = lambda : static_component_set

            for sample_idx in range(num_samples):
                num_sample_components = control_parameter_lists["component_count"][sample_idx]
                sample_components = component_set_generator()[:num_sample_components]
                samples.append(Sample.create(
                        exp_dir_path, 
                        sample_idx, 
                        sample_components, 
                        control_parameter_dicts[sample_idx],
                        search_algorithm_parameter_dicts[sample_idx],
                        reset_algorithm_parameter_dicts[sample_idx],
                        region=region
                ))
            to_json([sample.metadata for sample in samples], metadata_path_format(exp_dir_path))
            return Experiment(experiment_name, experiments_root_dir, samples)
        else: #if using existing inputs, 'use_existing_inputs' is the name of the experiment to copy inputs from.
            original_experiment = Experiment.load(experiments_root_dir+"/"+use_existing_inputs)
            #create input files:
            metadata = []
            for sample_idx in range(len(original_experiment.samples)):
                shutil.copyfile(
                        input_path_format(experiments_root_dir+"/"+use_existing_inputs, sample_idx),
                        input_path_format(exp_dir_path, sample_idx)
                )
                #create metadata file:
                metadata.append(Sample.metadata_dict_format(
                    control_parameter_dicts[sample_idx],
                    search_algorithm_parameter_dicts[sample_idx],
                    reset_algorithm_parameter_dicts[sample_idx],
                    bruteforce
                ))
            to_json(metadata, metadata_path_format(exp_dir_path))
            return Experiment.load(experiment_name, experiments_root_dir)
            

    def get_num_regions(self)->int:
        region = self.get_static_region()
        if region == "all":
            return 21 #assuming there are 21 regions here
        return len(region)

    def calc_expected_time(self, num_cores: int):
        return sum([sample.expected_runtime(self.get_num_regions()) for sample in self.samples])/float(num_cores)

    def print_expected_runtime(self, multiprocess: int = 1):
        print(yellow(f" Expected runtime is {get_time_description(self.calc_expected_time(multiprocess)*1.1)}."))

    @staticmethod
    def load(
            experiment_name: str, 
            experiments_root_dir: str = default_experiments_root_dir
    ):
        exp_dir_path = experiments_root_dir+"/"+experiment_name
        exp_metadata = from_json(metadata_path_format(exp_dir_path))
        samples = [Sample(metadata, sample_idx, exp_dir_path) for sample_idx, metadata in enumerate(exp_metadata)]
        return Experiment(experiment_name, experiments_root_dir, samples)

    def run(self, 
            verbosealg: bool = False, 
            retry: int = 0, 
            force: bool = False,
            multiprocess: int = 1
    ):
        if (type(multiprocess) is not int) or (multiprocess <= 0):
            fetal_error("multiprocess argument must be a postive integer ('int').")
        if os.path.exists(output_path_format(self.exp_dir_path, 0, 0)) and not force:
            if not bool_prompt("this experiment has already been run. override results?"):
                return
        
        print(yellow(f"Running '{self.experiment_name}'."))
        self.print_expected_runtime(multiprocess)
        num_regions = self.get_num_regions()
        if multiprocess == 1:
            run_samples(self.samples, retry, verbosealg, None, num_regions)
        else:
            samples_each_process = [self.samples[pid:self.get_num_samples():multiprocess] for pid in range(multiprocess)]
            ps = [Process(
                    target=run_samples, args=(samples_each_process[pid], retry, verbosealg, pid, num_regions)
                )
                for pid in range(multiprocess)
            ]
            for p in ps:
                p.start()
            for p in ps:
                p.join()
        print(yellow(f"finished running experiment: \"{self.experiment_name}\""))

class Series:

    def __init__(self, experiments):
        """instances of this class represent a series of experiments (instances of Experiments),
            and enable aggerated actions over those experiments.
            
        In practice a 'Series' is essentially a list of experiments with instance methods."""
        self.experiments = experiments
    
    def create(experiment_creators: list, series_name: str, *creator_args):
        """'experiment_creators' is a list of functions that create experiments when loaded.
            they are each expected to be able to take the experiments/series root dir as first argument,
            followed by the list of arguments given in 'creator_args'."""
        series_root_dir = "../experiments/"+series_name
        if not os.path.isdir(series_root_dir):
            os.mkdir(series_root_dir)
        return Series([creator(series_root_dir, *creator_args) for creator in experiment_creators])
        
    def load(experiment_names: list, series_name: str):
        return Series([Experiment.load(name) for name in experiment_names])

    def run(self, **kw_every_exp):
        for e in self.experiments:
            e.run(**kw_every_exp)

    def plot(self, **kw_every_exp):
        for e in self.experiments:
            times, prices = e.get_plot_curves(**kw_every_exp)[0]
            plt.plot(times, prices, label=e.experiment_name)
        plt.show()