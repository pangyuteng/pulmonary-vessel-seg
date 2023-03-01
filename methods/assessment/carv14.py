
import os
import sys
import pathlib
import pandas as pd
import numpy as np
import SimpleITK as sitk
from sklearn.metrics import confusion_matrix

def main(ground_truth_dir,segmentation_dir):

    gt_dict = {}
    for anno_kind in ["CARVE14_fullAnno"]:
        gt_dict[anno_kind]={}
        full_anno_dir = os.path.join(ground_truth_dir,anno_kind)
        gt_list = [str(x) for x in pathlib.Path(full_anno_dir).rglob("*.mhd")]
        for gt_path in gt_list:
            key = os.path.basename(gt_path).split('_')[0]
            gt_dict[anno_kind][key]=gt_path

    anno_kind = "CARVE14_fullAnno"
    mylist = []
    img_list = [str(x) for x in pathlib.Path(segmentation_dir).rglob("img.nii.gz")]
    for x in img_list:
        series_instance_uid = os.path.basename(os.path.dirname(x))
        key = series_instance_uid[:36]
        knopczynski_path = x.replace("img.nii.gz","knopczynski.nii.gz")
        wasserthal_path = x.replace("img.nii.gz","wasserthal.nii.gz")
        #print(series_instance_uid)
        if key in gt_dict[anno_kind].keys():
            gt_path = gt_dict[anno_kind][key]
        else:
            gt_path = None
        if gt_path is None:
            continue

        myitem = dict(
            series_instance_uid=series_instance_uid,
            key=key,
            img_path=x,
            gt_path=gt_path,
            wasserthal_path=wasserthal_path,
            knopczynski_path=knopczynski_path,
        )

        y_obj = sitk.ReadImage(gt_path)
        y = sitk.GetArrayFromImage(y_obj)
        y_true = (y != 0).astype(np.int16)

        for method,file_path in dict(
            wasserthal=wasserthal_path,
            knopczynski=knopczynski_path,
            ).items():

            y_hat_obj = sitk.ReadImage(file_path)
            y_hat = sitk.GetArrayFromImage(y_hat_obj)
            y_pred = (y_hat > 0.5).astype(np.int16)
        
            tn, fp, fn, tp = confusion_matrix(y_true.ravel(), y_pred.ravel()).ravel()
            sensitivity = tp / (tp+fn)
            specificity = tn / (tn+fp)
            accuracy = (tp+tn) / (tp+tn+fp+fn)
            print(method,accuracy,sensitivity,specificity)
            myitem[f'{method}-accuracy']=np.round(accuracy,5)
            myitem[f'{method}-sensitivity']=np.round(sensitivity,5)
            myitem[f'{method}-specificity']=np.round(specificity,5)

        print(myitem)
        mylist.append(myitem)
        pd.DataFrame(mylist).to_csv('results.csv',index=False)

if __name__ == "__main__":
    ground_truth_dir = sys.argv[1]
    segmentation_dir = sys.argv[2]
    main(ground_truth_dir,segmentation_dir)

'''

$ground_truth_dir contains below folders:

CARV14_conAnno
CARVE14_autoResults
CARVE14_fullAnno
CARVE14_refAnno
CARVE14_semiAutoResults

$segmentation_dir contains below files
$series_instance_uid/img.nii.gz
$series_instance_uid/wasserthal.nii.gz
$series_instance_uid/knopczynski.nii.gz

export ground_truth_dir=/mnt/hd3/data/carve14/CARVE14-20230201T185159Z-002/CARVE14
export segmentation_dir=/mnt/scratch/tmp/carve14
docker run -it -u $(id -u):$(id -g) \
    -e ground_truth_dir -e segmentation_dir \
    -w $PWD -v /mnt:/mnt \
    pangyuteng/ml:latest bash

echo $ground_truth_dir $segmentation_dir

python carv14.py $ground_truth_dir $segmentation_dir


https://en.wikipedia.org/wiki/Confusion_matrix
https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html

'''