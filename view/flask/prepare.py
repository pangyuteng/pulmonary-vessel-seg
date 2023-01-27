"""
util to run to view Totalsegmentator_dataset with itksnap:
itksnap -g ct.nii.gz -s segmentations.nii.gz -l totalsegmentator_label.txt
"""
import os
import sys
import random
from tqdm import tqdm
import numpy as np
import SimpleITK as sitk

from mod_preview import generate_mip


EXPECTED_COUNT = 104
random.seed(EXPECTED_COUNT)
color = lambda : [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

def imread(fpath):
    reader= sitk.ImageFileReader()
    reader.SetFileName(fpath)
    img = reader.Execute()
    return img

def imwrite(fpath,arr,img_obj,use_compression=True):
    img = sitk.GetImageFromArray(arr)
    img.SetSpacing(img_obj.GetSpacing())
    img.SetOrigin(img_obj.GetOrigin())
    img.SetDirection(img_obj.GetDirection())
    writer = sitk.ImageFileWriter()    
    writer.SetFileName(fpath)
    writer.SetUseCompression(use_compression)
    writer.Execute(img)

def prepare_label_file(root_dir):
    case0_seg = os.path.join(root_dir,'s0001','segmentations')
    seg_list = sorted([x.replace('.nii.gz','') for x in os.listdir(case0_seg)])
    assert(len(seg_list)==EXPECTED_COUNT)
    label_file = 'label.txt'
    if not os.path.exists(label_file):
        with open(label_file,'w') as f:
            f.write('0     0    0    0        0  0  0    "Clear Label"\n')
            for n,x in enumerate(seg_list):
                r,g,b = color()
                f.write(f'{n+1}     {r}    {g}    {b}        1  1  1    "{x}"\n')

def main(root_dir):
    case_list = sorted([x for x in os.listdir(root_dir)])
    for case_id in tqdm(case_list):
        case_folder = os.path.join(root_dir,case_id)
        if not os.path.isdir(case_folder):
            continue
        image_file = os.path.join(case_folder,'ct.nii.gz')
        dest_mask_file = os.path.join(case_folder,'segmentations.nii.gz')
        segmentation_folder = os.path.join(case_folder,'segmentations')
        thumbnail_file = os.path.join(case_folder,'thumbnail_0.png')
        if os.path.exists(thumbnail_file):
            continue
        seg_file_list = sorted(os.listdir(segmentation_folder))
        
        assert(EXPECTED_COUNT==len(seg_file_list))
        assert(os.path.exists(image_file))
        
        img_obj = imread(image_file)
        img = sitk.GetArrayFromImage(img_obj)
        mask = np.zeros_like(img).astype(np.uint8)
        print(case_id,mask.shape)
        for n,seg_file in enumerate(seg_file_list):
            seg_file = os.path.join(case_folder,'segmentations',seg_file)
            seg_obj = imread(seg_file)
            item_mask = sitk.GetArrayFromImage(seg_obj)
            mask[item_mask==1]=n+1

        imwrite(dest_mask_file,mask,img_obj,use_compression=True)
        generate_mip(img, mask, thumbnail_file)

if __name__ == "__main__":
    datadir_totalseg = sys.argv[1]
    prepare_label_file(datadir_totalseg)
    main(datadir_totalseg)

"""

"""