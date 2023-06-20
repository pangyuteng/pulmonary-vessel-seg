import os
import sys
import json
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import SimpleITK as sitk
import matplotlib.pyplot as plt

def main(dist_folder,frangi_folder,fwhm_folder):
    mylist = []
    for myfolder in [dist_folder,frangi_folder,fwhm_folder]:
        json_file_list = sorted(list([str(x) for x in Path(myfolder).rglob("*.json")]))
        print(len(json_file_list))
        for json_file in json_file_list:
            idx = os.path.basename(os.path.dirname(json_file))
            if 'dist' in os.path.basename(json_file):
                method = 'dist'
            elif 'frangi' in os.path.basename(json_file):
                method = 'frangi'
            elif 'bcsa' in os.path.basename(json_file):
                method = 'bcsa'
            elif 'fwhm' in os.path.basename(json_file):
                method = 'fwhm'
            else:
                raise NotImplementedError()

            mip_file = os.path.join(os.path.dirname(json_file),f'mip_{method}.png')
            myitem = {'idx':idx,'method':method,'mip_file':mip_file}
            with open(json_file,'r') as f:
                mydict = json.loads(f.read())
                newdict = {}
                for k,v in mydict.items():
                    if 'area-lt' in k:
                        nk = k.replace(f'-{method}','')
                    else:
                        nk = k
                    newdict[nk]=v
            myitem.update(newdict)
            mylist.append(myitem)

    rdf = pd.DataFrame(mylist)
    rdf.to_csv('results.csv',index=False,float_format='%.3f')
    colormapper = dict(dist='red',frangi='green',bcsa='blue',fwhm='orange')
    for n,row in rdf.iterrows():
        x_tmp =  list(np.arange(2,22,2))
        method = row.method
        col_str = [x for x in row.keys() if 'area-lt' in x]
        kwargs = dict(color=colormapper[method],alpha=0.5,)
        if row.idx == '01':
            kwargs['label']=method
        plt.plot(x_tmp,(100*row[col_str]).tolist(),**kwargs)

    plt.title("vessel12 dataset (n=23)")
    plt.ylabel('blood vessel volume(%)')
    plt.xlabel('estimated vascular crossectional area (mm2)')
    plt.legend()
    plt.grid(True)
    plt.savefig('area-hist.png')
    plt.close()

    x_list = []
    y_list = []
    
    for key_dt,key_frangi,unit in [
        ('pvv5-dist-prct','pvv5-frangi-prct','fraction'),
        ('pvv10-dist-prct','pvv10-frangi-prct','fraction'),
        ('pvv10+-dist-prct','pvv10+-frangi-prct','fraction'),
        ('pvv5-dist-cc','pvv5-frangi-cc','cc'),
        ('pvv10-dist-cc','pvv10-frangi-cc','cc'),
        ('pvv10+-dist-cc','pvv10+-frangi-cc','cc')]:
        if unit == 'cc':
            x_list.extend(rdf[key_dt])
            y_list.extend(rdf[key_frangi])
        if unit == 'fraction':
            unit = "prct"
            print('mean',key_dt,(rdf[key_dt].mean()*100).round(2),unit,key_frangi,(rdf[key_frangi].mean()*100).round(2),unit)
        else:
            print('mean',key_dt,rdf[key_dt].mean().round(2),unit,key_frangi,rdf[key_frangi].mean().round(2),unit)
    print(f'n={len(rdf)}')

    plt.scatter(x_list,y_list)
    plt.plot([0,400],[0,400],color='k',linewidth=1,label='line-of-identity')
    plt.xlabel('pvv (cc, method: distance-transform)')
    plt.ylabel('pvv (cc, method: vesselness)')
    plt.legend()
    plt.grid(True)
    plt.savefig('pvv-dist-frangi.png')
    plt.close()

    os.makedirs('static',exist_ok=True)
    with open('viz.md','w') as f:
        f.write(f'<img load="lazy" alt="..." src="pvv-dist-frangi.png" width="512"><br>\n')
        f.write(f'<img load="lazy" alt="..." src="area-hist.png" width="512"><br>\n')
        for idx in rdf['idx'].unique():
            f.write(f'{idx}: dist, frangi, bcsa, fwhm<br>\n')
            for method in ['dist','frangi','bcsa','fwhm']:
                tmp = rdf[(rdf.idx==idx)&(rdf.method==method)]
                if len(tmp)==0:
                    continue
                mip_file = tmp['mip_file'].tolist()[0]
                print(mip_file)
                tgt_file = f'static/{method}-mip-{idx}.png'
                shutil.copy(mip_file,tgt_file)
                f.write(f'<img load="lazy" alt="..." src="{tgt_file}" width="256">\n')
            f.write('<br>')

if __name__ == "__main__":
    main('vessel12-dist','vessel12-frangi','vessel12-fwhm')

"""
docker run -it -u $(id -u):$(id -g) -w $PWD pangyuteng/ml:latest bash
python agg_vessel12.py
"""