# coding=utf-8
import os
import subprocess as sub
from collections import defaultdict


def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z


def get_ic50_for_chembl_id(chembl_id):
    from chembl_webresource_client import TargetResource
    result = []
    tr = TargetResource()
    activities = tr.bioactivities(chembl_id)
    for a in activities:
        if a['bioactivity_type'] == 'IC50':
            result.append(a)
    return result


def download_smile_by_chembl_id(chembl_id):
    from chembl_webresource_client import CompoundResource
    cr = CompoundResource()
    ligand = cr.get(chembl_id)
    return ligand


def from_smile_to_mol2(smile):
    from pybel import readstring
    smi = readstring('smi', str(smile))
    smi.make3D()
    return smi


def make_scaffold(path_to_mol3_file):
    csv = 'output/scaffold.csv'
    command = 'strip-it --input ' + path_to_mol3_file + ' --noLog --output ' + csv + ' 2>' + os.devnull
    sub.call(command, shell=True)
    scaffold = {}
    with open(csv) as f:
        headers = f.readline().strip().split()[2:]
        values = f.readline().strip().split()[2:]
        for j in xrange(len(headers)):
            scaffold[headers[j]] = values[j]
    os.remove(csv)
    return scaffold


if __name__ == '__main__':
    chembl_id = 'CHEMBL1293196'
    ligands = get_ic50_for_chembl_id(chembl_id)
    ligands_number = len(ligands)
    for i in xrange(ligands_number):
        l = ligands[i]
        ligands[i] = merge_two_dicts(download_smile_by_chembl_id(l['ingredient_cmpd_chemblid']), l)
    for i in xrange(ligands_number):
        ligands[i]['molecule'] = from_smile_to_mol2(ligands[i]['smiles'])
        ligands[i]['path_to_mol2_file'] = str(os.path.join('output', ligands[i]['ingredient_cmpd_chemblid'])) + '.mol2'
        ligands[i]['molecule'].write('mol2', ligands[i]['path_to_mol2_file'], True)
    result = defaultdict(int)
    for i in xrange(ligands_number):
        ligands[i]['scaffold'] = make_scaffold(ligands[i]['path_to_mol2_file'])
        result[ligands[i]['scaffold']['RINGS_WITH_LINKERS_1']] += 1
    for k, v in result.items():
        print v, '', '', k
