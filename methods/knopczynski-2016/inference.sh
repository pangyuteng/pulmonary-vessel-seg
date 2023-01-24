#!/bin/bash

export INPUT_NIFTI_FILE=$1
export OUTPUT_NIFTI_FILE=$2

if [ -f ${OUTPUT_NIFTI_FILE} ]; then
    echo "vessel segmentation already done. no need to run."
    exit 0

cd /opt/app/scripts/UseClassifier
python classify.py ${INPUT_NIFTI_FILE} ${OUTPUT_NIFTI_FILE}

echo "done"