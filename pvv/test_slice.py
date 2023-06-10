import os
import sys
import ast
import json
import numpy as np
import SimpleITK as sitk
from skimage.morphology import skeletonize
from skimage.segmentation import watershed
from scipy import ndimage
from scipy.ndimage import distance_transform_edt
from skimage.measure import label, regionprops
from tqdm import tqdm
import imageio
from pvv_dist import resample_img

def estimate_radius(image_file,lung_file,vessel_file,outdir,debug):
    
    os.makedirs(outdir,exist_ok=True)

    og_image_obj = sitk.ReadImage(image_file)
    lung_obj = sitk.ReadImage(lung_file)
    vessel_obj = sitk.ReadImage(vessel_file)
    
    out_spacing = [1.0,1.0,1.0]
    image_obj = resample_img(og_image_obj, out_spacing, is_label=False)
    lung_obj = resample_img(lung_obj, out_spacing, is_label=True)
    vessel_obj = resample_img(vessel_obj, out_spacing, is_label=True)

    image = sitk.GetArrayFromImage(image_obj)
    lung_mask = sitk.GetArrayFromImage(lung_obj)
    vsl_mask = sitk.GetArrayFromImage(vessel_obj)

    spacing = image_obj.GetSpacing()
    origin = image_obj.GetOrigin()
    direction = image_obj.GetDirection()
    
    if debug:
        sitk.WriteImage(image_obj,f"{outdir}/debug-myimg.nii.gz")

    print('bs_field (appx radius)...')
    bs_field = distance_transform_edt(vsl_mask>0)
    bs_field = bs_field.astype(float)*out_spacing[0]
    print(bs_field.dtype)
    qia_obj = sitk.GetImageFromArray(bs_field)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-bs_field.nii.gz")

    print('skeletonize...')
    skeleton = skeletonize(vsl_mask)
    skeleton = skeleton.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(skeleton)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-skeleton.nii.gz")

    print('intersection...')
    # determine branching point
    # ref https://www.mathworks.com/matlabcentral/fileexchange/67600-branch-points-from-3d-logical-skeleton?s_tid=blogs_rc_5
    weights = np.ones((3,3,3))
    intersection = ndimage.convolve(skeleton,weights) > 3

    intersection = intersection.astype(np.int32)
    qia_obj = sitk.GetImageFromArray(intersection)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-intersection.nii.gz")

    print('label...')
    branch = np.copy(skeleton)
    branch[intersection==1]=0
    branch = label(branch)
    branch = branch.astype(np.int32)
    qia_obj = sitk.GetImageFromArray(branch)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/debug-branch.nii.gz")

    print('watershed...')
    ws_branch = watershed(vsl_mask*-1, branch, mask=vsl_mask>0)
    ws_branch = ws_branch.astype(np.int32)

    qia_obj = sitk.GetImageFromArray(ws_branch)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-watershed_labels.nii.gz")

from utils import extract_slice

# test  image
# debug-myimg.nii.gz
# 
# test vessel coordinate
# start itk-coord 56,62,160 intensity -270
# end itk-coord 50,55,162 intensity -591
# mid 55,61,161 intensity -594
def develper(outdir):

    og_image_obj = sitk.ReadImage(f"{outdir}/debug-myimg.nii.gz")
    image = sitk.GetArrayFromImage(og_image_obj)
    image_obj = sitk.GetImageFromArray(image)
    image_obj.CopyInformation(og_image_obj)

    manual_points = False
    if manual_points:

        mystart = [160-1,62-1,56-1]
        myend = [162-1,55-1,50-1]
        mycenter = [161-1,61-1,55-1]

        #print(image.shape)
        #print(mystart,image[mystart[0],mystart[1],mystart[2]])
        assert(image[mystart[0],mystart[1],mystart[2]]==-270)
        #print(myend,image[myend[0],myend[1],myend[2]])
        print(mycenter,image[mycenter[0],mycenter[1],mycenter[2]])

        image[mycenter[0],mycenter[1],mycenter[2]]=1000
        print(image[mycenter[0],mycenter[1],mycenter[2]])
        
        # SimpleITK uses x-y-z. Numpy uses z-y-x
        mystart = image_obj.TransformContinuousIndexToPhysicalPoint([mystart[2],mystart[1],mystart[0]])
        myend = image_obj.TransformContinuousIndexToPhysicalPoint([myend[2],myend[1],myend[0]])
        slice_normal = np.array(myend) - np.array(mystart)
        slice_center = image_obj.TransformContinuousIndexToPhysicalPoint([mycenter[2],mycenter[1],mycenter[0]])
        slice_spacing = [.1,.1,.1]
        slice_radius = 10

        is_label = False
        print('slice_center,slice_normal,slice_spacing,slice_radius')
        print(slice_center,slice_normal,slice_spacing,slice_radius)
        slice_obj = extract_slice(image_obj,slice_center,slice_normal,slice_spacing,slice_radius,is_label)

        n=0
        png_file = os.path.join(outdir,f'slice{n:05d}.png')
        nii_file = os.path.join(outdir,f'slice{n:05d}.nii.gz')

        sitk.WriteImage(slice_obj,nii_file)
        slice_arr = sitk.GetArrayFromImage(slice_obj)
        print('np.max(slice_arr)',np.max(slice_arr))
        print('shape',slice_arr.shape)
        slice_arr = slice_arr[0,:,:].astype(float).squeeze()
        min_val,max_val = -1000,1000
        slice_arr = 255*(slice_arr-min_val)/(max_val-min_val)
        slice_arr = slice_arr.clip(0,255).astype(np.uint8)
        imageio.imwrite(png_file,slice_arr)
        print('manual_points! exit')
        sys.exit(1)


    branch_obj = sitk.ReadImage(f"{outdir}/debug-branch.nii.gz")
    branch =sitk.GetArrayFromImage(branch_obj)

    bsfield_obj = sitk.ReadImage(f"{outdir}/debug-bs_field.nii.gz")
    bs_field =sitk.GetArrayFromImage(bsfield_obj)
    print(len(np.unique(branch)))

    og_image_obj = sitk.ReadImage(f"{outdir}/debug-myimg.nii.gz")
    image = sitk.GetArrayFromImage(og_image_obj)
    #image[branch>0]=1000
    image_obj = sitk.GetImageFromArray(image)
    image_obj.CopyInformation(og_image_obj)

    props = regionprops(branch,intensity_image=bs_field)
    png_file_list = []
    for n,p in enumerate(props):
        if n == 0 :
            continue
        if len(p.coords) < 10:
            continue

        png_file = os.path.join(outdir,f'slice{n:05d}.png')
        nii_file = os.path.join(outdir,f'slice{n:05d}.nii.gz')
        # assume sorted coords        
        centroid = p.coords[int(len(p.coords)/2)]
        slice_spacing = [1,1,1]
        slice_radius = bs_field[centroid[0],centroid[1],centroid[2]]

        print('slice_radius',slice_radius)
        print('branch-id',branch[centroid[0],centroid[1],centroid[2]])
        mystart = [int(p.coords[0][0]),int(p.coords[0][1]),int(p.coords[0][2])]
        print('mystart',p.coords[0],mystart)
        myend = [int(p.coords[-1][0]),int(p.coords[-1][1]),int(p.coords[-1][2])]
        print('myend',p.coords[-1],myend)
        cidx = int(len(p.coords)/2)
        mycenter = [int(p.coords[cidx][0]),int(p.coords[cidx][1]),int(p.coords[cidx][2])]
        print('mycenter',p.coords[cidx],mycenter)

        mystart = image_obj.TransformContinuousIndexToPhysicalPoint([mystart[2],mystart[1],mystart[0]])
        myend = image_obj.TransformContinuousIndexToPhysicalPoint([myend[2],myend[1],myend[0]])
        slice_center = image_obj.TransformContinuousIndexToPhysicalPoint([mycenter[2],mycenter[1],mycenter[0]])
        slice_normal = np.array(myend) - np.array(mystart)
        slice_spacing = [.1,.1,.1]
        slice_radius = slice_radius*5

        is_label = False
        print('slice_center,slice_normal,slice_spacing,slice_radius')
        print(slice_center,slice_normal,slice_spacing,slice_radius)
        slice_obj = extract_slice(image_obj,slice_center,slice_normal,slice_spacing,slice_radius,is_label)
        sitk.WriteImage(slice_obj,nii_file)
        slice_arr = sitk.GetArrayFromImage(slice_obj)
        slice_arr = slice_arr[0,:,:].astype(float).squeeze()
        print('shape',slice_arr.shape)
        min_val,max_val = -1300,100 # -600,1500
        slice_arr = 255*(slice_arr-min_val)/(max_val-min_val)
        slice_arr = slice_arr.clip(0,255).astype(np.uint8)
        imageio.imwrite(png_file,slice_arr)
        png_file_list.append(png_file)

        if n > 5000:
            break
    print("hohoho",n)
    with open(f'{outdir}/index.html','w') as f:
        for x in png_file_list:
            f.write(f'<img src="{os.path.basename(x)}">\n')

if __name__ == "__main__":
    image_file = sys.argv[1]
    lung_file = sys.argv[2]
    vessel_file = sys.argv[3]
    outdir = sys.argv[4]
    debug = ast.literal_eval(sys.argv[5])
    if not os.path.exists(f"{outdir}/debug-watershed_labels.nii.gz"):
        estimate_radius(image_file,lung_file,vessel_file,outdir,debug)
    develper(outdir)
"""

docker run -it -u $(id -u):$(id -g) -w $PWD \
    -v /cvibraid:/cvibraid -v /radraid:/radraid \
    pangyuteng/ml:latest bash

python test_slice.py img.nii.gz lung.nii.gz wasserthal.nii.gz hola True

"""