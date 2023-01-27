import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
from flask import (
    Flask, render_template, request, jsonify
)
from utils import TOTALSEG_MAXVAL,load_json

DATADIR_VESSEL12 = os.environ.get('DATADIR_VESSEL12')
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    static_url_path='/static',
    static_folder='static',
    template_folder='templates',
)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route('/review')
def review():
    case_id = request.args.get('case_id')
    kind = request.args.get('kind')
    case_folder = os.path.join(DATADIR_VESSEL12,case_id)

    image_file = os.path.join(case_folder,'img.nii.gz')
    image_downsampled_file = os.path.join(case_folder,'img-downsampled.nii.gz')

    if kind == 'image':

        image_file = image_file
        mask_file = None
        stl_file = None
        image_basename = None
        mask_basename = None
        origial_note='na'
        nifti_note='original resolution'
        stl_note='na'

    elif kind == 'knopczynski':

        knopczynski_file = os.path.join(case_folder,'knopczynski.nii.gz')
        knopczynski_stl_file = os.path.join(case_folder,'knopczynski.stl')
        knopczynski_downsampled_file = os.path.join(case_folder,'knopczynski-downsampled.nii.gz')
        knopczynski_stl_downsampled_file = os.path.join(case_folder,'knopczynski-downsampled-222.stl')

        image_file = image_downsampled_file
        mask_file = knopczynski_downsampled_file
        stl_file = knopczynski_stl_downsampled_file
        image_basename = os.path.basename(image_file)
        mask_basename = os.path.basename(mask_file)
        origial_note='na'
        nifti_note='downsampled voxel size1 1x1x10mm'
        stl_note='downsampled voxel size1 2x2x2mm'

    elif kind == 'wasserthal':

        wasserthal_file = os.path.join(case_folder,'wasserthal.nii.gz')
        wasserthal_stl_file = os.path.join(case_folder,'wasserthal.stl')
        wasserthal_downsampled_file = os.path.join(case_folder,'wasserthal-downsampled.nii.gz')
        wasserthal_stl_downsampled_file = os.path.join(case_folder,'wasserthal-downsampled-222.stl')

        image_file = image_downsampled_file
        mask_file = wasserthal_downsampled_file
        stl_file = wasserthal_stl_downsampled_file
        image_basename = os.path.basename(image_file)
        mask_basename = os.path.basename(mask_file)
        origial_note='na'
        nifti_note='downsampled voxel size1 1x1x10mm'
        stl_note='downsampled voxel size1 2x2x2mm'

    else:
        return jsonify({"message":"not supported"})

    return render_template("review.html",
        kind = kind,
        case_id = case_id,
        image_file = image_file,
        mask_file = mask_file,
        stl_file = stl_file,
        image_basename = image_basename,
        mask_basename = mask_basename,
        origial_note=origial_note,
        nifti_note=nifti_note,
        stl_note=stl_note,
    )


@app.route('/')
def home():
    url_list = ['vessel12']
    return render_template("home.html",url_list=url_list)

@app.route('/vessel12')
def vessel12():
    case_list = []
    for x in sorted(os.listdir(DATADIR_VESSEL12)):
        case_dir = os.path.join(DATADIR_VESSEL12,x)
        if not os.path.isdir(case_dir):
            continue
        item = {
            'case_id':x,
            "img_url": os.path.join(DATADIR_VESSEL12,x,"img-mip.png"),
            "knopczynski_url": os.path.join(DATADIR_VESSEL12,x,"knopczynski-mip.png"),
            "wasserthal_url": os.path.join(DATADIR_VESSEL12,x,"wasserthal-mip.png"),
        }
        case_list.append(item)    
    df = pd.DataFrame(case_list)
    return render_template("vessel12.html",df=df)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p","--port",type=int,default=5000)
    args = parser.parse_args()
    app.run(host="0.0.0.0",port=args.port,debug=True)

"""
"""
