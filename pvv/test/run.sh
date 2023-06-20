#!/bin/bash

idx=$1
img_file=$2
lung_file=$3
vessel_file=$4
code_dir=$5

cd $code_dir

outdir=$code_dir/test/vessel12-dist/${idx}
mkdir -p $outdir
python pvv_dist.py $vessel_file $outdir True

outdir=$code_dir/test/vessel12-frangi/${idx}
mkdir -p $outdir
python pvv_frangi.py $img_file $lung_file $vessel_file $outdir True

outdir=$code_dir/test/vessel12-fwhm/${idx}
mkdir -p $outdir
python pvv_fwhm.py $img_file $vessel_file $outdir True
