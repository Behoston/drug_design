# coding=utf-8
import os
import subprocess as sub
from collections import defaultdict
from pybel import readstring

import requests


class Ligand(object):
    def __init__(self, chembl_id, bioactivity=None):
        self.chembl_id = chembl_id
        self.bioactivity = bioactivity
        self.smile = None
        self.mol2 = None
        self.path_to_mol2 = None
        self.scaffold = None

    def download_smile(self):
        from chembl_webresource_client import CompoundResource
        cr = CompoundResource()
        self.smile = cr.get(self.chembl_id)['smiles']

    def from_smile_to_mol2(self):
        smi = readstring('smi', str(self.smile))
        smi.make3D()
        self.mol2 = smi

    def save_mol2(self, path=None):
        self.path_to_mol2 = path
        self.mol2.write('mol2', self.path_to_mol2, True)

    def make_scaffold(self):
        csv_file = 'output/scaffold.csv'
        command = 'strip-it --input ' + self.path_to_mol2 + ' --noLog --output ' + csv_file + ' 2>' + os.devnull
        sub.call(command, shell=True)
        self.scaffold = {}
        with open(csv_file) as f:
            headers = f.readline().strip().split()[2:]
            values = f.readline().strip().split()[2:]
            for j in xrange(len(headers)):
                self.scaffold[headers[j]] = values[j]
        os.remove(csv_file)


def download_ligands_with_scaffold(smile, how_many=10):
    url = 'http://zinc15.docking.org/substances.csv'
    params = {'count': how_many, 'structure-contains': smile}
    request = requests.get(url, params=params)
    return [item.strip().split(',') for item in request.text.split('\n')[1:-1]]


def get_ic50_for_chembl_id(chembl_id):
    from chembl_webresource_client import TargetResource
    result = []
    tr = TargetResource()
    activities = tr.bioactivities(chembl_id)
    for a in activities:
        if a['bioactivity_type'] == 'IC50':
            result.append(Ligand(a['ingredient_cmpd_chemblid'], a))
    return result


if __name__ == '__main__':
    chembl_id = 'CHEMBL1293196'
    ligands = get_ic50_for_chembl_id(chembl_id)
    ligands_number = len(ligands)
    result = defaultdict(int)
    for l in ligands:
        l.download_smile()
        l.from_smile_to_mol2()
        l.save_mol2(str(os.path.join('output', l.chembl_id + '.mol2')))
        l.make_scaffold()
        result[l.scaffold['RINGS_WITH_LINKERS_1']] += 1
    best = None
    print 'All scaffolds: '
    for k, v in result.items():
        print '\t', v, '', '', k
        if not best or best[0] < v:
            best = (v, k)
    print 'Best scaffold is:', best[1]
    how_may_ligands = 10
    print 'First', how_may_ligands, 'ligands with best scaffolda:'
    for row in download_ligands_with_scaffold(best[1], how_may_ligands):
        print '\t', row
