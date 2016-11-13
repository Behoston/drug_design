import os
from pathlib import Path

import numpy

from lab4 import list_dirs
import matplotlib.pyplot as plt


def parse_output(output):
    with open(output) as f:
        for line in f:
            l = line.strip().split()
            if len(l) == 3 and l[0] == 'Grid' and l[1] == 'Score:':
                return float(l[2])


if __name__ == '__main__':
    result_dir = os.path.abspath('output')
    result = []
    for d in list_dirs(result_dir):
        grid_score = parse_output(str(Path(result_dir, d, 'dock.out')))
        with Path(result_dir, d, 'ic50').open() as f:
            ic50 = int(f.readline().strip())
        result.append((ic50, grid_score))
    result.sort()
    grid_scores = [grid_score for _, grid_score in result]
    ic50s = [ic50 for ic50, _ in result]
    plt.plot(ic50s, grid_scores, 'ro')
    z = numpy.polyfit(ic50s, grid_scores, 1)
    p = numpy.poly1d(z)
    plt.plot(ic50s, p(ic50s), 'r--')
    print("y=%.6fx+(%.6f)" % (z[0], z[1]))
    plt.savefig('output/wykres.png')
