#!/bin/bash

img_file=$1
mask_file=$2
idx=$3
outdir=/cvibraid/cvib2/apps/personal/pteng/github/pulmonary-vessel-seg/methods/blood_volume/test/vessel12/${idx}

mkdir -p $outdir

cd /cvibraid/cvib2/apps/personal/pteng/github/pulmonary-vessel-seg/methods/blood_volume
python pvv_dist.py $mask_file $outdir
