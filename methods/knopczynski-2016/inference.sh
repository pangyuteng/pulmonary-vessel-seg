#!/bin/bash

export INPUT_NIFTI_FILE=$1
export OUTPUT_NIFTI_FILE=$2
export LUNG_NIFTI_FILE=$3

if [ -f ${OUTPUT_NIFTI_FILE} ]; then
    echo "vessel segmentation already done. no need to run."
    exit 0
fi

cd /opt/app/scripts/UseClassifier
python classify.py ${INPUT_NIFTI_FILE} ${OUTPUT_NIFTI_FILE}
cd -
python remove_non_lung.py ${LUNG_NIFTI_FILE} ${OUTPUT_NIFTI_FILE}

echo "done"