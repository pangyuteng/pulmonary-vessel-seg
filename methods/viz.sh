#!/bin/bash

export OUTPUT_NIFTI_FOLDER=$1

export IMG_FILE=${OUTPUT_NIFTI_FOLDER}/img.nii.gz
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/img-downsampled.nii.gz

python viz_utils.py downsample $IMG_FILE $DOWN_FILE False

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski.nii.gz
export STL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski.stl
python viz_utils.py stl $IMG_FILE $STL_FILE

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal.nii.gz
export STL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal.stl
python viz_utils.py stl $IMG_FILE $STL_FILE