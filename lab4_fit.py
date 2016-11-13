import argparse
import subprocess
from multiprocessing import Process, Queue, cpu_count
import os
from pathlib import Path
from string import Template


class FitDocking(Process):
    def __init__(self, params: Queue, output: Queue, default_config, spheres, grid_prefix, dock_dir, ligand):
        super().__init__()
        self.params = params
        self.output = output
        self.default_config = default_config
        self.spheres = spheres
        self.grid_prefix = grid_prefix
        self.dock_dir = dock_dir
        self.dock_bin = Path(dock_dir, 'bin', 'dock6')
        self.dock_parameters = Path(dock_dir, 'parameters')
        self.ligand = ligand
        self.main_dir = os.getcwd()

    def run(self):
        param = self.params.get()
        while param is not None:
            with open(self.default_config) as f:
                config = Template(f.read()).substitute(
                    max_orientations=param['max_orientations'],
                    min_anchor_size=param['min_anchor_size'],
                    use_clash_overlap=param['use_clash_overlap'],
                    atom_model=param['atom_model'],
                    ligand=self.ligand,
                    spheres=self.spheres,
                    grid=self.grid_prefix,
                    parameters=self.dock_parameters
                )
            working_dir = str(hash(str(param)))
            os.mkdir(working_dir)
            os.chdir(working_dir)
            with open('dock.in', 'w') as f:
                f.write(config)
            command = ' '.join([
                str(self.dock_bin),
                '-i', os.path.abspath(f.name),
                '-o', os.path.abspath('dock.out')
            ])
            subprocess.call(command, shell=True)
            print(command)
            os.chdir(self.main_dir)
            param = self.params.get()
            self.output.put(working_dir)


def prepare_params() -> (Queue, int):
    q = Queue()
    q_size = 0
    for max_orientations in range(1000, 11000, 1000):
        for min_anchor_size in (6, 12, 24):
            for use_clash_overlap in (0, 5):
                for atom_model in ('all', 'united'):
                    params = {
                        'max_orientations': max_orientations,
                        'min_anchor_size': min_anchor_size,
                        'use_clash_overlap': use_clash_overlap,
                        'atom_model': atom_model,
                    }
                    q.put(params)
                    q_size += 1
    return q, q_size


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fit docking parameters')
    parser.add_argument('ligand', help='localization of ligand file in mol2 format')
    parser.add_argument('gird_prefix', help='localization of gird files with gird files prefix')
    parser.add_argument('spheres', help='localization of spheres file')
    parser.add_argument('dock6_dir', help='localization of bin directory of dock6')
    parser.add_argument('--template', '-t', help='localization of template input file',
                        default=str(Path(__file__).parent / 'template_dock_fit.in'))
    args = parser.parse_args()
    ligand = os.path.abspath(args.ligand)
    config_template = os.path.abspath(args.template)
    dock_dir = os.path.abspath(args.dock6_dir)
    spheres_file = os.path.abspath(args.spheres)
    grid_prefix = os.path.abspath(args.gird_prefix)

    # prepare
    cpus = cpu_count()
    docking = []
    output = Queue()
    params, params_number = prepare_params()

    # run
    for i in range(cpus):
        docking.append(FitDocking(params, output, config_template, spheres_file, grid_prefix, dock_dir, ligand))
        docking[-1].start()

    # display results
    print(params_number)
    for _ in range(params_number):
        output.get()

    # end
    output.close()
    params.close()
    for process in docking:
        process.join()
