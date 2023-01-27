
import os
import sys
import json
import random
import warnings
import numpy as np
random.seed(0)

TOTALSEG_MAXVAL = 104

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def load_json(myfile):
    with open(myfile,'r') as f:
        return json.loads(f.read())

rand_color = lambda: [np.round(random.random(),2),np.round(random.random(),2),np.round(random.random(),2)]

rand_color_with_val_infront = lambda x: [x,np.round(random.random(),2),np.round(random.random(),2),np.round(random.random(),2)]

# look-up-table creation for papaya
def create_lut(dataset_json_file,mapper_json_file,totalseg_maxval=TOTALSEG_MAXVAL):

    unsorted_dataset_dict = load_json(dataset_json_file)
    # sort by value in dict prior lut creation
    dataset_list = sorted(unsorted_dataset_dict.items(), key=lambda x: x[1]) # sort by keys
    dataset_dict = {k:v for k,v in dataset_list}
    dataset_maxval = len(dataset_dict)

    # create LUT for manual contours
    color_dict = {}
    dataset_color_list = [[0,0,0,0]]

    for k,v in dataset_dict.items():
        color_dict[v]= rand_color()
        scaled_val = np.round(v/dataset_maxval,3)
        item = list(color_dict[v])
        item.insert(0, scaled_val)
        dataset_color_list.append(item)

    with open(mapper_json_file,'r') as f:
        mapper = json.loads(f.read())
    # create matching LUT for totalsegmentator segmentations using above LUT
    totalseg_color_list = [[0,0,0,0]]
    for n,organ_name in enumerate(sorted(mapper.keys())):
        v = mapper[organ_name]
        scaled_val = np.round((n+1)/totalseg_maxval,3)
        if v == -1:
            #item=[scaled_val,0,0,0]
            item=rand_color_with_val_infront(scaled_val)
        else:
            item = list(color_dict[v])
            item.insert(0, scaled_val)
        totalseg_color_list.append(item)

    return dataset_color_list, totalseg_color_list

MYLIST = ["ped-ct-seg","amos22"]
def save_all_luts():
    for dataset_name in MYLIST:

        dataset_lut_file = os.path.join(THIS_DIR,'static',f'dataset-{dataset_name}.json')
        totalseg_lut_file = os.path.join(THIS_DIR,'static',f'totalseg-{dataset_name}.json')

        if os.path.exists(dataset_lut_file) and os.path.exists(totalseg_lut_file):
            print(dataset_lut_file)
            print(totalseg_lut_file)
            warnings.warn('luts found!!')

        assess_folder = os.path.join(os.path.dirname(os.path.dirname(THIS_DIR)),'assess',dataset_name)
        dataset_json_file = os.path.join(assess_folder,'dataset.json')
        mapper_json_file = os.path.join(assess_folder,'mapper.json')

        dataset_color_list, totalseg_color_list = create_lut(dataset_json_file,mapper_json_file)

        with open(dataset_lut_file,'w') as f:
            f.write(json.dumps(dataset_color_list,sort_keys=True,indent=4))
        with open(totalseg_lut_file,'w') as f:
            f.write(json.dumps(totalseg_color_list,sort_keys=True,indent=4))

if __name__ == "__main__":
    save_all_luts()

"""

docker run -it -u $(id -u):$(id -g) \
    -w $PWD -v /mnt:/mnt pangyuteng/ml:latest bash

python print_lut_for_papaya.py

"""