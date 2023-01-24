#!/bin/bash

export INPUT_NIFTI_FILE=$1
export OUTPUT_NIFTI_FOLDER=$2

export VESSEL_FILE=${OUTPUT_NIFTI_FOLDER}/lung_vessels.nii.gz

if [ -f ${VESSEL_FILE} ]; then
    echo "vessel segmentation already done. no need to run."
    exit 0

TotalSegmentator -i ${INPUT_NIFTI_FILE} -o ${OUTPUT_NIFTI_FOLDER}
TotalSegmentator -i ${INPUT_NIFTI_FILE} -o ${OUTPUT_NIFTI_FOLDER} -ta lung_vessels

echo "done"