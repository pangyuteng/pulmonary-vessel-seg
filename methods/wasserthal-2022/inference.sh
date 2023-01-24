#!/bin/bash
export INPUT_MHD_FILE=$1
export OUTPUT_NIFTI_FOLDER=$2

export INPUT_NIFTI_FILE=/tmp/$(openssl rand -hex 4).nii.gz
export VESSEL_FILE=${OUTPUT_NIFTI_FOLDER}/lung_vessels.nii.gz

if [ -f ${VESSEL_FILE} ]; then
    echo "vessel segmentation already done. no need to run."
    exit 0
fi

python mhd2niigz.py ${INPUT_MHD_FILE} ${INPUT_NIFTI_FILE}

TotalSegmentator -i ${INPUT_NIFTI_FILE} -o ${OUTPUT_NIFTI_FOLDER}
TotalSegmentator -i ${INPUT_NIFTI_FILE} -o ${OUTPUT_NIFTI_FOLDER} -ta lung_vessels

echo "done"