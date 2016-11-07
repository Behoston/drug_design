import os
from pathlib import Path
from tempfile import mkdtemp
from multiprocessing import Process
from multiprocessing import Queue
from string import Template
import subprocess
from time import time


class Simulation(Process):
    def __init__(self, ligands: Queue, default_config, dock_dir, spheres, grid_prefix):
        """
        :param ligands: must be Queue of absolute path (end with None)
        :param default_config: may be relative path
        :param dock_dir: may be relative path to dock top-level directory
        :param spheres: may be relative path to .sph file
        :param grid_prefix: prefix of grid files (with path, may be relative)
        """
        super().__init__()
        self.ligands = ligands
        self.spheres = os.path.abspath(spheres)
        self.default_config = os.path.abspath(default_config)
        self.dock_dir = os.path.abspath(dock_dir)
        self.dock_bin = Path(dock_dir, 'bin', 'dock6')
        self.dock_parameters = Path(dock_dir, 'parameters')
        self.grid_prefix = os.path.abspath(grid_prefix)

    def run(self):
        while True:
            ligand_file = self.ligands.get()
            if ligand_file is None:
                # out of ligands, terminate
                return
            tmp_dir = mkdtemp(prefix='dock_')
            with open(self.default_config) as f:
                config = Template(f.read()).substitute(
                    ligand=ligand_file,
                    parameters=self.dock_parameters,
                    spheres=self.spheres,
                    grid=self.grid_prefix
                )
            os.chdir(tmp_dir)
            with open('dock.in', 'w') as f:
                f.write(config)

            command = ' '.join([
                str(self.dock_bin),
                '-i', os.path.abspath(f.name),
                '-o', os.path.abspath('dock.out')
            ])
            subprocess.run(command, shell=True)


def list_files(directory: str, ext: str = None) -> list:
    # return [i.name for i in os.scandir(directory) if i.is_file and (ext or i.name.rsplit('.', 1)[-1] == ext)]
    files = []
    for item in os.scandir(directory):
        if item.is_file():
            if ext is None or item.name.rsplit('.', 1)[-1] == ext:
                files.append(item.path)
    return files


def prepare_queue(directory):
    ligands = Queue()
    for file in list_files(directory, 'mol2')[:4]:
        ligands.put(os.path.abspath(file))
    return ligands


if __name__ == '__main__':
    t = time()
    # TODO: args
    ligands_dir = 'output'
    config_template = 'template_dock.in'
    dock_bin = '/home/behoston/programy/dock6/'
    spheres_file = 'selected.sph'
    grid_prefix = 'grid'

    ligands = prepare_queue(ligands_dir)
    proc = []
    cpus = os.cpu_count()
    for i in range(cpus):
        ligands.put(None)
        proc.append(Simulation(ligands, config_template, dock_bin, spheres_file, grid_prefix))
        proc[-1].start()
    for p in proc:
        p.join()
    print(time() - t)
