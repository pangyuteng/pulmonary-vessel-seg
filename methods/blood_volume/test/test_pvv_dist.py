import os
import sys
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(THIS_DIR))

import pandas as pd
import tempfile
import json
import shutil
from pvv_dist import main as pvv_dist_main

def main():
    df = pd.read_csv('vessel12.csv')
    mylist = []
    for n,row in df.iterrows():
        assert(os.path.exists(row.image_path))
        assert(os.path.exists(row.mask_path))
        with tempfile.TemporaryDirectory() as tmpdir:
            pvv_dist_main(row.image_path,row.mask_path,tmpdir)
            mip_file = os.path.join(tmpdir,'mip.png')
            tgt_file = os.path.join(THIS_DIR,f'mip-{n:02d}.png')
            shutil.copy(mip_file,tgt_file)
            json_file = os.path.join(tmpdir,'dist_transform.json')
            with open(json_file,'r') as f:
                myitem = json.loads(f.read())
            myitem['mask_path']=row.mask_path
            mylist.append(myitem)

    rdf = pd.DataFrame(mylist)
    rdf.to_csv('results.csv',index=False)

if __name__ == "__main__":
    main()
    