#!/bin/bash

export OUTPUT_NIFTI_FOLDER=$1


### downsample image

export IMG_FILE=${OUTPUT_NIFTI_FOLDER}/img.nii.gz
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/img-downsampled.nii.gz

if [ ! -f ${DOWN_FILE} ]; then
    python viz_utils.py downsample $IMG_FILE $DOWN_FILE False
fi

### downsample mask

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski.nii.gz
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski-downsampled.nii.gz
if [ ! -f ${DOWN_FILE} ]; then
    python viz_utils.py downsample $VSL_FILE $DOWN_FILE True
fi

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal.nii.gz
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal-downsampled.nii.gz
if [ ! -f ${DOWN_FILE} ]; then
    python viz_utils.py downsample $VSL_FILE $DOWN_FILE True
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
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski-downsampled-222.nii.gz
export STL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski-downsampled-222.stl

if [ ! -f ${STL_FILE} ]; then
    python viz_utils.py downsample222 $VSL_FILE $DOWN_FILE True
    python viz_utils.py stl $DOWN_FILE $STL_FILE
fi

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal.nii.gz
export DOWN_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal-downsampled-222.nii.gz
export STL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal-downsampled-222.stl
if [ ! -f ${STL_FILE} ]; then
    python viz_utils.py downsample222 $VSL_FILE $DOWN_FILE True
    python viz_utils.py stl $DOWN_FILE $STL_FILE
fi

export FLIP=0
export IMG_FILE=${OUTPUT_NIFTI_FOLDER}/img.nii.gz
export LUNG_FILE=${OUTPUT_NIFTI_FOLDER}/segmentations/lung.nii.gz
export PNG_FILE=${OUTPUT_NIFTI_FOLDER}/img-mip.png
if [ ! -f ${PNG_FILE} ]; then
    python viz_utils.py thumbnail $IMG_FILE $LUNG_FILE $FLIP $PNG_FILE
fi

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski.nii.gz
export LUNG_FILE=${OUTPUT_NIFTI_FOLDER}/segmentations/lung.nii.gz
export PNG_FILE=${OUTPUT_NIFTI_FOLDER}/knopczynski-mip.png
if [ ! -f ${PNG_FILE} ]; then
    python viz_utils.py thumbnail $VSL_FILE $LUNG_FILE $FLIP $PNG_FILE
fi

export VSL_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal.nii.gz
export LUNG_FILE=${OUTPUT_NIFTI_FOLDER}/segmentations/lung.nii.gz
export PNG_FILE=${OUTPUT_NIFTI_FOLDER}/wasserthal-mip.png
if [ ! -f ${PNG_FILE} ]; then
    python viz_utils.py thumbnail $VSL_FILE $LUNG_FILE $FLIP $PNG_FILE
fi