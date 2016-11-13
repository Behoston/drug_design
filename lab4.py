import os
from pathlib import Path
from multiprocessing import Process
from multiprocessing import Queue
from string import Template
import subprocess
from time import time


class Simulation(Process):
    def __init__(self, ligands: Queue, output: Queue, default_config, dock_dir, spheres, grid_prefix):
        """
        :param ligands: must be Queue of absolute path (end with None)
        :param output: output Queue
        :param default_config: may be relative path
        :param dock_dir: may be relative path to dock top-level directory
        :param spheres: may be relative path to .sph file
        :param grid_prefix: prefix of grid files (with path, may be relative)
        """
        super().__init__()
        self.ligands = ligands
        self.output = output
        self.spheres = os.path.abspath(spheres)
        self.default_config = os.path.abspath(default_config)
        self.dock_dir = os.path.abspath(dock_dir)
        self.dock_bin = Path(dock_dir, 'bin', 'dock6')
        self.dock_parameters = Path(dock_dir, 'parameters')
        self.grid_prefix = os.path.abspath(grid_prefix)

    def run(self):
        while True:
            ligand_dir = self.ligands.get()
            if ligand_dir is None:
                # out of ligands, terminate
                return
            with open(self.default_config) as f:
                config = Template(f.read()).substitute(
                    ligand=str(Path(ligand_dir, 'ligand.mol2')),
                    parameters=self.dock_parameters,
                    spheres=self.spheres,
                    grid=self.grid_prefix
                )
            os.chdir(ligand_dir)
            with open('dock.in', 'w') as f:
                f.write(config)

            command = ' '.join([
                str(self.dock_bin),
                '-i', os.path.abspath(f.name),
                '-o', os.path.abspath('dock.out')
            ])
            subprocess.call(command, shell=True)
            self.output.put(ligand_dir)


def list_dirs(d: str) -> list:
    return [os.path.join(d, o) for o in os.listdir(d) if os.path.isdir(os.path.join(d, o))]


def prepare_queue(directory):
    ligands = Queue()
    output = Queue()
    number_of_ligands = 0
    for file in list_dirs(directory):
        ligands.put(os.path.abspath(file))
        number_of_ligands += 1
    return ligands, output, number_of_ligands


if __name__ == '__main__':
    t = time()
    # TODO: args
    ligands_dir = 'output'
    config_template = 'template_dock.in'
    dock_bin = '/home/behoston/programy/dock6/'
    spheres_file = 'selected.sph'
    grid_prefix = 'grid'

    ligands, output, number_of_ligands = prepare_queue(ligands_dir)
    proc = []
    cpus = os.cpu_count()
    for i in range(cpus):
        ligands.put(None)
        proc.append(Simulation(ligands, output, config_template, dock_bin, spheres_file, grid_prefix))
        proc[-1].start()

    results = []
    for i in range(number_of_ligands):
        results.append(output.get())

    # end
    for p in proc:
        p.join()
    output.close()
    ligands.close()
