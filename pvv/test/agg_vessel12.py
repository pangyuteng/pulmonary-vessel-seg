import os
import sys
import json
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import SimpleITK as sitk
import matplotlib.pyplot as plt

def main(dist_folder,frangi_folder):
    main_dict = {}
    for method,myfolder in [('dist',dist_folder),('frangi',frangi_folder)]:
        json_file_list = sorted(list([str(x) for x in Path(myfolder).rglob("*.json")]))
        print(json_file_list)
        for json_file in json_file_list:
            idx = os.path.basename(os.path.dirname(json_file))
            mip_file = os.path.join(os.path.dirname(json_file),'mip.png')
            if idx not in main_dict.keys():
                main_dict[idx]={'idx':idx}
            with open(json_file,'r') as f:
                mydict = json.loads(f.read())
            mydict[f'{method}_mip_file']=mip_file
            main_dict[idx].update(mydict)

    mylist = list(main_dict.values())
    cols = []
    rdf = pd.DataFrame(mylist)#columns=cols)
    rdf.to_csv('results.csv',index=False,float_format='%.3f')

    x_list = []
    y_list = []
    for key_dt,key_frangi in [
        ('pvv5-dt-prct','pvv5-frangi-prct'),
        ('pvv10-dt-prct','pvv10-frangi-prct'),
        ('pvv10+-dt-prct','pvv10+-frangi-prct')]:

        x_list.extend(rdf[key_dt])
        y_list.extend(rdf[key_frangi])
        print('mean',key_dt,rdf[key_dt].mean(),key_frangi,rdf[key_frangi].mean())

    plt.scatter(x_list,y_list)
    plt.plot([0,1],[0,1],color='k',linewidth=1,label='line-of-identity')
    plt.xlabel('pvv (method: distance-transform)')
    plt.ylabel('pvv (method: vesselness)')
    plt.legend()
    plt.grid(True)
    plt.savefig('pvv-dt-frang.png')
    plt.close()

    os.makedirs('static',exist_ok=True)
    with open('viz.md','w') as f:
        f.write(f'<img load="lazy" alt="..." src="pvv-dt-frang.png" width="512"><br>\n')
        for idx,mydict in main_dict.items():
            f.write(f'{idx}: dist, frangi<br>\n')
            for method in ['dist','frangi']:
                key = f'{method}_mip_file'
                if key not in mydict.keys():
                    print(f'file not found {key} for {idx}')
                    continue
                mip_file = mydict[key]
                tgt_file = f'static/{method}-mip-{idx}.png'
                shutil.copy(mip_file,tgt_file)
                f.write(f'<img load="lazy" alt="..." src="{tgt_file}" width="256">\n')
            f.write('<br>')

if __name__ == "__main__":
    dist_folder = sys.argv[1]
    frangi_folder = sys.argv[2]
    main(dist_folder,frangi_folder)

"""
docker run -it -u $(id -u):$(id -g) -w $PWD pangyuteng/ml:latest bash
python agg_vessel12.py vessel12-dist vessel12-frangi
"""