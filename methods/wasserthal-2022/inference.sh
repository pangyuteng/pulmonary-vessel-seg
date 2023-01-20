
#!/bin/bash

export INPUT_NIFTI_FILE=$1
export OUTPUT_NIFTI_FILE=$2

export TEMPDIR=/tmp/totalseg-$(openssl rand -hex 4)
export TEMPDIR=/tmp/totalseg-dbfea4f5
export VESSEL_FILE=${TEMPDIR}/lung_vessels.nii.gz

TotalSegmentator -i ${INPUT_NIFTI_FILE} -o ${TEMPDIR}
TotalSegmentator -i ${INPUT_NIFTI_FILE} -o ${TEMPDIR} -ta lung_vessels

if [ -f ${VESSEL_FILE} ]; then

    cp ${VESSEL_FILE} ${OUTPUT_NIFTI_FILE}
    exit 0

    # #cleanup not needed if we're in a container, otherwise:
    # rm ${TEMPDIR}/*.nii.gz && rmdir ${TEMPDIR}

else
    echo file $VESSEL_FILE not found!
    exit 1

fi