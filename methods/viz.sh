#!/bin/bash

export OUTPUT_NIFTI_FOLDER=$1


### downsample image

export IMG_FILE=${OUTPUT_NIFTI_FOLDER}/img.nii.gz
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/img-downsampled.nii.gz


if [ ! -f ${DOWN_FILE} ]; then
    python viz_utils.py downsample $IMG_FILE $DOWN_FILE False
fi

### create stl

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski.nii.gz
export STL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski.stl

if [ ! -f ${STL_FILE} ]; then
    python viz_utils.py stl $VSL_FILE $STL_FILE
fi

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal.nii.gz
export STL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal.stl

if [ ! -f ${STL_FILE} ]; then
    python viz_utils.py stl $VSL_FILE $STL_FILE
fi

#### create downsampled stl

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski.nii.gz
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski-downsampled.nii.gz
export STL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski-downsampled.stl

if [ ! -f ${STL_FILE} ]; then
    python viz_utils.py downsample $VSL_FILE $DOWN_FILE True
    python viz_utils.py stl $DOWN_FILE $STL_FILE
fi
export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal.nii.gz
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal-downsampled.nii.gz
export STL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal-downsampled.stl
if [ ! -f ${STL_FILE} ]; then
    python viz_utils.py downsample $VSL_FILE $DOWN_FILE True
    python viz_utils.py stl $DOWN_FILE $STL_FILE
fi

