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
        #pvv_file = os.path.join(os.path.dirname(json_file),'pvv.nii.gz')
        #pvv_obj = sitk.ReadImage(pvv_file)
        #pvv = sitk.GetArrayFromImage(pvv_obj)
        #print(idx,np.unique(pvv))
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