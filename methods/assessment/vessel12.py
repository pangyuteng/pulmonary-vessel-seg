
import os
import sys
import pathlib
import pandas as pd
import numpy as np
import SimpleITK as sitk
from sklearn.metrics import confusion_matrix

results_csv_file = "results-vessel12.csv"
compiled_csv_file = "compiled-vessel12.csv"
def assess(ground_truth_dir,segmentation_dir):
    gt_dict = {
        '21': os.path.join(ground_truth_dir,'VESSEL12_ExampleScans','Annotations','VESSEL12_21_Annotations.csv'),
        '22': os.path.join(ground_truth_dir,'VESSEL12_ExampleScans','Annotations','VESSEL12_22_Annotations.csv'),
        '23': os.path.join(ground_truth_dir,'VESSEL12_ExampleScans','Annotations','VESSEL12_23_Annotations.csv'),
    }

    mylist = []
    img_list = [str(x) for x in pathlib.Path(segmentation_dir).rglob("img.nii.gz")]
    for x in img_list:
        key = os.path.basename(os.path.dirname(x))
        knopczynski_path = x.replace("img.nii.gz","knopczynski.nii.gz")
        wasserthal_path = x.replace("img.nii.gz","wasserthal.nii.gz")
        if key in gt_dict.keys():
            gt_path = gt_dict[key]
        else:
            gt_path = None
        if gt_path is None:
            continue

        myitem = dict(
            key=key,
            img_path=x,
            gt_path=gt_path,
            wasserthal_path=wasserthal_path,
            knopczynski_path=knopczynski_path,
        )
        print(myitem)

        wasserthal_obj = sitk.ReadImage(wasserthal_path)
        wasserthal_hat = sitk.GetArrayFromImage(wasserthal_obj)
        wasserthal_list = []
        knopczynski_obj = sitk.ReadImage(knopczynski_path)
        knopczynski_hat = sitk.GetArrayFromImage(knopczynski_obj)
        knopczynski_list = []

        df = pd.read_csv(gt_path,header=None)
        y_true = []
        for n,row in df.iterrows():
            x,y,z,v=row[0],row[1],row[2],row[3]
            w = wasserthal_hat[z,y,x] #??? z,y,x
            k = knopczynski_hat[z,y,x]
            y_true.append(v)
            wasserthal_list.append(w)
            knopczynski_list.append(int(k))
            print(x,y,z,v,w,k)
        y_true = np.array(y_true)
        wasserthal_list = np.array(wasserthal_list)
        knopczynski_list = np.array(knopczynski_list)

        for method,y_pred in [
            ('wasserthal',wasserthal_list),
            ('knopczynski',knopczynski_list),
            ]:
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

export ground_truth_dir=/scratch2/personal/pteng/dataset/vessel12/VESSEL12
export segmentation_dir=/radraid/pteng/tmp/vessel12

docker run -it -u $(id -u):$(id -g) \
    -e ground_truth_dir -e segmentation_dir \
    -w $PWD -v /mnt:/mnt \
    pangyuteng/ml:latest bash

echo $ground_truth_dir $segmentation_dir

python vessel12.py $ground_truth_dir $segmentation_dir

https://en.wikipedia.org/wiki/Confusion_matrix
https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html
https://en.wikipedia.org/wiki/S%C3%B8rensen%E2%80%93Dice_coefficient

'''