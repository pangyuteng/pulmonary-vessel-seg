
import os
import sys
from pathlib import Path

#/scratch2/personal/pteng/dataset/vessel12/VESSEL12/VESSEL12_01-05/VESSEL12_01.mhd
#/radraid/pteng/tmp/vessel12/01/wasserthal.nii.gz 01
img_root = sys.argv[1]
seg_root = sys.argv[2]
code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

img_file_list = sorted([str(x) for x in Path(img_root).rglob("VESSEL12_*.mhd")])
mylist = []
for img_file in img_file_list:
    if "Lungmasks" in img_file:
        continue
    idx = os.path.basename(img_file).replace("VESSEL12_","").replace(".mhd","")
    print(idx,img_file)
    seg_folder = os.path.join(seg_root,idx,"segmentations")
    vessel_file = os.path.join(seg_folder,"lung_vessels.nii.gz")
    lung_file = os.path.join(seg_folder,"lung.nii.gz")
    assert(os.path.exists(vessel_file))
    assert(os.path.exists(lung_file))
    cmd = f'{idx} {img_file} {lung_file} {vessel_file} {code_dir}'
    mylist.append(cmd)

with open('vessel12.args','w') as f:
    for item in mylist:
        f.write(item+"\n")

'''

docker run -it -u $(id -u):$(id -g) -w $PWD \
    -v /scratch2:/scratch2 -v /dingo_data:/dingo_data \
    -v /cvibraid:/cvibraid -v /radraid:/radraid pangyuteng/ml:latest bash

python gen_args.py /scratch2/personal/pteng/dataset/vessel12/VESSEL12 /radraid/pteng/tmp/vessel12

condor_submit submit.condor

'''