import os
import sys
import warnings
import json

data_dir = os.path.abspath(sys.argv[1])
out_dir = os.path.abspath(sys.argv[2])

sub_folders = [os.path.join(data_dir,x) for x in ['VESSEL12_01-05','VESSEL12_06-10','VESSEL12_11-15','VESSEL12_16-20']]
img_mhd_list = []
for s in sub_folders:
    tmp_list = [os.path.join(s,x) for x in os.listdir(s) if x.endswith('.mhd')]
    img_mhd_list.extend(tmp_list)

mylist = []
for x in sorted(img_mhd_list):
    source_img_mhd_path = x
    uid = os.path.basename(source_img_mhd_path).replace("VESSEL12_","").replace(".mhd","")
    source_lung_path = os.path.join(data_dir,'VESSEL12_01-20_Lungmasks',f'VESSEL12_{uid}.mhd')
    target_folder_path = os.path.join(out_dir,uid)
    target_img_path = os.path.join(target_folder_path,'img.nii.gz')
    item = dict(
        uid=uid,
        source_img_path=source_img_mhd_path,
        source_lung_path=source_lung_path,
        target_img_path=target_img_path,
        target_folder_path=target_folder_path,
    )
    mylist.append(item)

with open('wasserthal.args','w') as f:
    for n,x in enumerate(mylist):
        vsl = os.path.join(x['target_folder_path'],'wasserthal.nii.gz')
        myline = f"{x['source_img_path']} {x['target_img_path']} {x['target_folder_path']} {vsl}\n"
        f.write(myline)

with open('knopczynski.args','w') as f:
    for n,x in enumerate(mylist):
        vsl = os.path.join(x['target_folder_path'],'knopczynski.nii.gz')
        lung = source_lung_path
        myline = f"{x['source_img_path']} {vsl} {x['source_lung_path']}\n"
        f.write(myline)

"""
"""