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
    case_folder = os.path.join(DATADIR_VESSEL12,case_id)

    image_file = os.path.join(case_folder,'img.nii.gz')
    image_downsampled_file = os.path.join(case_folder,'img-downsampled.nii.gz')
    
    knopczynski_file = os.path.join(case_folder,'knopczynski.nii.gz')
    wasserthal_file = os.path.join(case_folder,'wasserthal.nii.gz')

    knopczynski_stl_file = os.path.join(case_folder,'knopczynski.stl')
    wasserthal_stl_file = os.path.join(case_folder,'wasserthal.stl')
    
    mask_file = knopczynski_file
    stl_file = knopczynski_stl_file

    return render_template("review.html",
        case_id = case_id,
        image_file = image_file,
        mask_file = mask_file,
        stl_file = stl_file,
        image_basename = os.path.basename(image_file),
        mask_basename = os.path.basename(mask_file),
    )


@app.route('/')
def home():
    url_list = ['vessel12']
    return render_template("home.html",url_list=url_list)

@app.route('/vessel12')
def vessel12():
    case_list = [ {'case_id':x,"png_url": os.path.join(DATADIR_VESSEL12,x,"thumbnail_0.png")} \
        for x in sorted(os.listdir(DATADIR_VESSEL12)) \
        if os.path.isdir(os.path.join(DATADIR_VESSEL12,x)) ]
    df = pd.DataFrame(case_list)
    return render_template("vessel12.html",df=df)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p","--port",type=int,default=5000)
    args = parser.parse_args()
    app.run(host="0.0.0.0",port=args.port,debug=True)

"""
"""