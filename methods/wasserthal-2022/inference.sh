#!/bin/bash
export INPUT_MHD_FILE=$1
export INPUT_NIFTI_FILE=$2
export OUTPUT_NIFTI_FOLDER=$3
export OUTPUT_VESSEL_FILE=$4

export ORIGINAL_VESSEL_FILE=${OUTPUT_NIFTI_FOLDER}/lung_vessels.nii.gz

if [ -f ${OUTPUT_VESSEL_FILE} ]; then
    echo "vessel segmentation already done. no need to run."
    exit 0
fi

python mhd2niigz.py ${INPUT_MHD_FILE} ${INPUT_NIFTI_FILE}

if [ ! -f ${ORIGINAL_VESSEL_FILE} ]; then
    #TotalSegmentator --fast -i ${INPUT_NIFTI_FILE} -o ${OUTPUT_NIFTI_FOLDER}
    TotalSegmentator -i ${INPUT_NIFTI_FILE} -o ${OUTPUT_NIFTI_FOLDER}
    TotalSegmentator -i ${INPUT_NIFTI_FILE} -o ${OUTPUT_NIFTI_FOLDER} -ta lung_vessels
fi

cp ${ORIGINAL_VESSEL_FILE} ${OUTPUT_VESSEL_FILE}


echo "done"
