
import os
import sys
import pathlib
import pandas as pd
import numpy as np
import SimpleITK as sitk
from sklearn.metrics import confusion_matrix

results_csv_file = "results-carve14.csv"
compiled_csv_file = "compiled-carve14.csv"
def assess(ground_truth_dir,segmentation_dir):

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
        print(np.unique(y))
        y_true = (y != 0).astype(np.int16)
        # -999 (not labeled),0,1,2 # gonna assume -999s are vessel that has been reviewed, just not labeled as Artery or Vein yet?

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
            dice = 2*tp / (2*tp +fp+fn)
            print(method,dice,accuracy,sensitivity,specificity)
            myitem[f'{method}-dice']=np.round(dice,5)
            myitem[f'{method}-accuracy']=np.round(accuracy,5)
            myitem[f'{method}-sensitivity']=np.round(sensitivity,5)
            myitem[f'{method}-specificity']=np.round(specificity,5)

        print(myitem)
        mylist.append(myitem)
        pd.DataFrame(mylist).to_csv(results_csv_file,index=False)

def compile(csv_file):
    df = pd.read_csv(csv_file)
    score_name_list = ["dice","accuracy","sensitivity","specificity"]
    method_list = ["wasserthal","knopczynski"]
    mylist = []
    for score_name in score_name_list:
        for method in method_list:
            values = df[f'{method}-{score_name}']
            myitem=dict(
                method=method,
                score_name=score_name,
                mean_val=values.mean().round(5),
                std_val=values.std().round(5),
                n=len(values),
            )
            mylist.append(myitem)
    pd.DataFrame(mylist).to_csv(compiled_csv_file,index=False)

if __name__ == "__main__":
    ground_truth_dir = sys.argv[1]
    segmentation_dir = sys.argv[2]
    if not os.path.exists(results_csv_file):
        assess(ground_truth_dir,segmentation_dir)
    if not os.path.exists(compiled_csv_file):
        compile(results_csv_file)


'''
"""
Annotations
This page contains the manual annotation that were used to evaluate the 
method as presented in our paper. Three different sets of annotations are available 
for downloading, i.e. the reference set, the consensus set, and the set of full 
annoations. Each set can be downloaded as a zip file containing all the scans 
(see section All annotations in one file), or as two seperate files per case (.mdh and .zraw). 
The reference set (see section Reference Annotations) and consensus set (see section Consensus Annotations) 
both contain annotations for all 55 scans. 
The set of full annotations (see section Full Annotations) contain 
annoations of a randomly selected subset of ten scans.  
The voxel in these images can have one of the following values:
•	0 (background)
•	1 (artery)
•	2 (vein)
•	-999 (not labeled)
"""

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
https://en.wikipedia.org/wiki/S%C3%B8rensen%E2%80%93Dice_coefficient

'''