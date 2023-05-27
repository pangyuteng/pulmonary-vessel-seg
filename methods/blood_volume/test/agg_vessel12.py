import os
import sys
import json
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import SimpleITK as sitk

def main(myfolder):
    json_file_list = sorted(list(Path(myfolder).rglob("*.json")))
    mylist = []
    for json_file in json_file_list:
        idx = os.path.basename(os.path.dirname(json_file))
        with open(json_file,'r') as f:
            mydict = json.loads(f.read())
        mydict['idx']=idx
        if False:
            print('-----------------------')
            print(f'{idx}:')
            nii_file = os.path.join(os.path.dirname(json_file),'debug-area.nii.gz')
            nii_obj = sitk.ReadImage(nii_file)
            arr = sitk.GetArrayFromImage(nii_obj)
            arr = np.round(arr,0)
            area_list = sorted(list(set([x for x in np.unique(arr) if x>0 ])))
            for x in area_list:
                print(x,np.sum(arr==x)/np.sum(arr>0))
        mylist.append(mydict)
    #cols = ['idx','pvv5-dt','pvv10-dt','pvv10+-dt']
    rdf = pd.DataFrame(mylist)#,columns=cols)
    rdf.to_csv('results.csv',index=False)

    os.makedirs('static',exist_ok=True)
    png_file_list = sorted(list(Path(myfolder).rglob("*.png")))
    with open('README.md','w') as f:
        for png_file in png_file_list:
            idx = os.path.basename(os.path.dirname(png_file))
            tgt_file = f'static/mip-{idx}.png'
            shutil.copy(png_file,tgt_file)
            f.write(f'<img src="{tgt_file}" width="256"><br>\n')

if __name__ == "__main__":
    myfolder = sys.argv[1]
    main(myfolder)

"""
docker run -it -u $(id -u):$(id -g) -w $PWD pangyuteng/ml:latest bash


"""