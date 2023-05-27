import os
import sys
import json
import numpy as np
import SimpleITK as sitk
from skimage.morphology import skeletonize
from skimage.segmentation import watershed
from scipy import ndimage
from skimage.measure import label, regionprops
from tqdm import tqdm

'''
https://en.wikipedia.org/wiki/Normal_distribution
https://en.wikipedia.org/wiki/Full_width_at_half_maximum
assuming vessel intensity can be fitted with a guassian distribution curve
we can use FWHM as diameter.
so if we have a sigma of 1mm, then diameter would be 2.355*1 mm

“BVX”, where “X” indicates a range of vessel sizes in mm2 (BV5 is the volume of blood contained in
vessels between 1.25 and 5 mm2 cross-sectional area, BV5-10
between 5 and 10 mm2, and BV10 > 10 mm2)
https://journals.physiology.org/doi/pdf/10.1152/japplphysiol.00458.2022

# approximate diameter using FWHM which is ~ 2.355*sigma
# https://en.wikipedia.org/wiki/Full_width_at_half_maximum

radius = sigma*2.355/2
area = pi*(radius^2)

radius = np.sqrt(area/pi)
sigma = radius*2/2.355
sigma = np.sqrt(area/pi)*2/2.355


# radius 
>>> [r for r in np.linspace(0.25,5,10)]

# area
>>> [np.pi*(r**2) for r in np.linspace(0.25,5,10)]

# sigma
>>> [r*2/2.355 for r in np.linspace(0.25,5,10)]

# area
>>> [a for a in np.linspace(1,20,20)]

# radius 
>>> [np.sqrt(a/np.pi) for a in np.linspace(1,20,20)]

# sigma
>>> [np.sqrt(a/np.pi)*2/2.355 for a in np.linspace(1,20,20)]

'''

def estimate_radius(image_file,lung_file,vessel_file,outdir):
    
    os.makedirs(outdir,exist_ok=True)

    image_obj = sitk.ReadImage(image_file)
    image = sitk.GetArrayFromImage(image_obj)
    
    lung_obj = sitk.ReadImage(lung_file)
    lung_mask = sitk.GetArrayFromImage(lung_obj)

    vessel_obj = sitk.ReadImage(vessel_file)
    vsl_mask = sitk.GetArrayFromImage(vessel_obj)
    spacing = image_obj.GetSpacing()
    origin = image_obj.GetOrigin()
    direction = image_obj.GetDirection()
    
    min_val,max_val = -1000,1000
    image = image.astype(np.float)
    image = (image-min_val)/(max_val-min_val)
    image = image.clip(0,1)
    image[lung_mask==0]=0
    myimg_obj = sitk.GetImageFromArray(image)
    myimg_obj.CopyInformation(image_obj)
    sitk.WriteImage(myimg_obj,f"{outdir}/myimg.nii.gz")

    radius_list = [r for r in np.linspace(0.25,5,10)]
    sigma_list = [r*2/2.355 for r in np.linspace(0.25,5,10)]
    arr_list = []
    for x_mm in sigma_list:
        print(f'sigma: {x_mm}') 
        sigma = np.ones(3)*x_mm
        # unsure if we need to adjust sigma with spacing 
        # or itk does it internally, 
        # with no adjustment, radius seem to be "less noisy".
        # sigma = sigma/np.array(spacing)
        gaussian = sitk.SmoothingRecursiveGaussianImageFilter()
        gaussian.SetSigma(sigma)
        smoothed = gaussian.Execute(myimg_obj)

        '''
        ref. on sitk.ObjectnessMeasureImageFilter
        https://simpleitk.org/doxygen/latest/html/sitkObjectnessMeasureImageFilter_8h_source.html
        https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ObjectnessMeasureImageFilter.html
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.110.7722&rep=rep1&type=pdf
        https://github.com/InsightSoftwareConsortium/ITK/blob/f84720ee0823964bd135de8eb973acc40c1e70e1/Modules/Filtering/ImageFeature/include/itkHessianToObjectnessMeasureImageFilter.h 
        https://github.com/InsightSoftwareConsortium/ITK/blob/f84720ee0823964bd135de8eb973acc40c1e70e1/Modules/Filtering/ImageFeature/include/itkHessianToObjectnessMeasureImageFilter.hxx

        per https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6214740/pdf/nihms982442.pdf
        Multiscale vessel enhancement filtering
        set alpha 0.53, beta 0.61 # gamma was not metioned.

        https://pubmed.ncbi.nlm.nih.gov/32741657
        https://pubmed.ncbi.nlm.nih.gov/25227036
        set alpha 0.5, beta 0.5, c 20 ?? likely not the same equation.

        '''
        myfilter = sitk.ObjectnessMeasureImageFilter()
        myfilter.SetBrightObject(True)
        myfilter.SetObjectDimension(1) # 1: lines (vessels),
        myfilter.SetAlpha(0.5)
        myfilter.SetBeta(0.5)
        myfilter.SetGamma(5.0)
        tmp_obj = myfilter.Execute(smoothed)
        tmp_arr = sitk.GetArrayFromImage(tmp_obj)
        min_val,max_val = np.min(tmp_arr),np.max(tmp_arr)
        tmp_arr = (tmp_arr-min_val)/(max_val-min_val)
        arr_list.append(tmp_arr)

    arr = np.argmax(np.array(arr_list),axis=0)
    arr = arr.astype(np.int16)
    arr[vsl_mask==0]=-1
    print(np.unique(arr))
    mapper_dict = {n:r for n,r in enumerate(radius_list)}
    map_func = np.vectorize(lambda x: float(mapper_dict.get(x,0)))
    radius = map_func(arr)
    print(radius.dtype)

    qia_obj = sitk.GetImageFromArray(radius)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/radius.nii.gz")

    print('skeletonize...')
    skeleton = skeletonize(vsl_mask)
    skeleton = skeleton.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(skeleton)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/skeleton.nii.gz")

    print('intersection...')
    # determine branching point
    # ref https://www.mathworks.com/matlabcentral/fileexchange/67600-branch-points-from-3d-logical-skeleton?s_tid=blogs_rc_5
    weights = np.ones((3,3,3))
    intersection = ndimage.convolve(skeleton,weights) > 3

    intersection = intersection.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(intersection)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/intersection.nii.gz")

    print('label...')
    branch = np.copy(skeleton)
    branch[intersection==1]=0
    branch = label(branch)
    branch = branch.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(branch)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/branch.nii.gz")

    print('watershed...')
    ws_branch = watershed(vsl_mask*-1, branch, mask=vsl_mask>0)
    ws_branch = ws_branch.astype(np.int16)

    qia_obj = sitk.GetImageFromArray(ws_branch)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/watershed_labels.nii.gz")

    print('regionprops...')
    props = regionprops(branch,intensity_image=radius)
    mapper_dict = {p.label:np.pi*(p.mean_intensity**2) for p in props}
    print('area...')
    map_func = np.vectorize(lambda x: float(mapper_dict.get(x,0)))
    area = map_func(ws_branch)
    print(area.dtype)
    qia_obj = sitk.GetImageFromArray(area)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/area.nii.gz")

    print('pvv...')
    pvv = np.zeros_like(area)
    pvv[np.logical_and(area>0,area<=5)]=1
    pvv[np.logical_and(area>5,area<10)]=2
    pvv[area>=10]=3
    pvv = pvv.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(pvv)
    qia_obj.CopyInformation(image_obj)

    qia_obj = sitk.GetImageFromArray(pvv)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/pvv.nii.gz")

    mydict = {
        'pvv5-frangi': float(np.sum(pvv==1)/np.sum(pvv>0)),
        'pvv10-frangi': float(np.sum(pvv==2)/np.sum(pvv>0)),
        'pvv10+-frangi': float(np.sum(pvv==3)/np.sum(pvv>0)),
    }
    json_file = f"{outdir}/frangi.json"
    with open(json_file,'w') as f:
        f.write(json.dumps(mydict))


if __name__ == "__main__":
    image_file = sys.argv[1]
    lung_file = sys.argv[2]
    vessel_file = sys.argv[3]
    outdir = sys.argv[4]
    estimate_radius(image_file,lung_file,vessel_file,outdir)

"""

docker run -it -u $(id -u):$(id -g) -w $PWD \
    -v /cvibraid:/cvibraid -v /radraid:/radraid \
    pangyuteng/ml:latest bash

python pvv_frangi.py img.nii.gz lung.nii.gz wasserthal.nii.gz outdir-frangi

"""