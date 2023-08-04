import os
import sys
import pandas as pd

'''
input csv file needs to have 2 columns
output_folder_path
nifti_image_path
'''
csv_file = os.path.abspath(sys.argv[1])
df = pd.read_csv(csv_file)

mylist = []
for n,row in df.iterrows():
    totalseg_folder = os.path.join(row.output_folder_path,'segmentations')
    nifti_lung_path = os.path.join(row.output_folder_path,'segmentations','lung.nii.gz')
    item = dict(
        output_folder_path=row.output_folder_path,
        nifti_image_path=row.nifti_image_path,
        totalseg_folder=totalseg_folder,
        nifti_lung_path=nifti_lung_path,
    )
    mylist.append(item)

with open('wasserthal.args','w') as f:
    for n,x in enumerate(mylist):
        vsl = os.path.join(x['output_folder_path'],'wasserthal.nii.gz')
        if not os.path.exists(vsl):
            myline = f"na {x['nifti_image_path']} {x['totalseg_folder']} {vsl}\n"
            f.write(myline)

with open('knopczynski.args','w') as f:
    for n,x in enumerate(mylist):
        vsl = os.path.join(x['output_folder_path'],'knopczynski.nii.gz')
        if not os.path.exists(vsl):
            myline = f"{x['nifti_image_path']} {vsl} {x['nifti_lung_path']}\n"
            f.write(myline)

with open('viz.args','w') as f:
    for n,x in enumerate(mylist):
        myline = f"{x['output_folder_path']}\n"
        f.write(myline)

"""
python gen_args.py tl.csv
"""