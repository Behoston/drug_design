import os
from pathlib import Path

import numpy

from lab4 import list_dirs
import matplotlib.pyplot as plt


def parse_output(output):
    result = {}
    with open(output) as f:
        for line in f:
            l = line.strip().split()
            if len(l) == 3 and l[0] == 'Grid' and l[1] == 'Score:':
                result['grid score'] = float(l[2])
            if len(l) == 2 and l[0] == 'Grid_vdw:':
                result['grid vdw'] = float(l[1])
            if len(l) == 2 and l[0] == 'Grid_es:':
                result['grid es'] = float(l[1])
    return result


def parse_ligand(ligand):
    atoms = False
    atoms_number = 0
    with open(ligand) as f:
        for line in f:
            l = line.strip().split()
            if len(l) == 0:
                continue
            if l[0] == '@<TRIPOS>ATOM':
                atoms = True
                continue
            elif atoms and l[0] == '@<TRIPOS>BOND':
                break
            elif atoms and l[1] != 'H':
                atoms_number += 1
    return atoms_number


def add_trend_line(x, y):
    z = numpy.polyfit(x, y, 1)
    p = numpy.poly1d(z)
    plt.plot(x, p(x), 'r--')
    trend_expression = "y=%.6fx+(%.6f)" % (z[0], z[1])
    plt.annotate(trend_expression, xy=(x[int(len(x) / 2)], p(x[0]) + 1.1))


if __name__ == '__main__':
    result_dir = os.path.abspath('output')
    result = []
    for d in list_dirs(result_dir):
        dock_result = parse_output(str(Path(result_dir, d, 'dock.out')))
        atoms = parse_ligand(str(Path(result_dir, d, 'ligand.mol2')))
        with Path(result_dir, d, 'ic50').open() as f:
            ic50 = int(f.readline().strip())
        if ic50 < 10 ** 6:
            result.append((ic50, dock_result, atoms))
    result.sort()
    grid_scores = [dock_result['grid score'] for _, dock_result, __ in result]
    grid_vdw = [dock_result['grid vdw'] for _, dock_result, __ in result]
    grid_es = [dock_result['grid es'] for _, dock_result, __ in result]
    atoms = [ato for _, __, ato in result]
    ic50s = [ic50 for ic50, _, __ in result]

    # Grid Score
    plt.ylabel('Grid Score')
    plt.xlabel('IC 50')
    plt.grid(True)
    plt.plot(ic50s, grid_scores, 'ro')
    add_trend_line(ic50s, grid_scores)
    plt.savefig('output/gs.png')

    # Grid VDW
    plt.close()
    plt.ylabel('Grid VDW')
    plt.xlabel('IC 50')
    plt.grid(True)
    plt.plot(ic50s, grid_vdw, 'ro')
    add_trend_line(ic50s, grid_vdw)
    plt.savefig('output/gvdw.png')

    # Grid ES
    plt.close()
    plt.ylabel('Grid ES')
    plt.xlabel('IC 50')
    plt.grid(True)
    plt.plot(ic50s, grid_es, 'ro')
    add_trend_line(ic50s, grid_es)
    plt.savefig('output/ges.png')

    # Atoms
    plt.close()
    plt.ylabel('Grid Score')
    plt.xlabel('Atoms')
    plt.grid(True)
    plt.plot(atoms, grid_scores, 'ro')
    add_trend_line(atoms, grid_scores)
    plt.savefig('output/atoms.png')
