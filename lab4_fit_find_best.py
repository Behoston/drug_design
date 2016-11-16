from pathlib import Path

from drawing_lab4 import parse_output
from lab4 import list_dirs

if __name__ == '__main__':
    results = 'fit'
    best_grid_score = None
    best_config = None
    for d in list_dirs(results):
        try:
            result_dir = Path(d)
            docking_result = str(result_dir / 'dock.out')
            docking_result = parse_output(docking_result)
            docking_gs = docking_result['grid score']
            if best_grid_score is None or best_grid_score > docking_gs:
                best_grid_score = docking_gs
                best_config = str(result_dir)
        except:
            print('Missing:', d)
    print(best_grid_score)
    print(best_config)
