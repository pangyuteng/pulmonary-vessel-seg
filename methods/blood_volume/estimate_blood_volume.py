import sys
import numpy as np
import SimpleITK as sitk
from skimage.morphology import skeletonize
from skimage.segmentation import watershed

def resample_img(itk_image, out_spacing, is_label=False):
    
    # Resample images to 2mm spacing with SimpleITK
    original_spacing = itk_image.GetSpacing()
    original_size = itk_image.GetSize()

    out_size = [
        int(np.round(original_size[0] * (original_spacing[0] / out_spacing[0]))),
        int(np.round(original_size[1] * (original_spacing[1] / out_spacing[1]))),
        int(np.round(original_size[2] * (original_spacing[2] / out_spacing[2])))]

    resample = sitk.ResampleImageFilter()
    resample.SetOutputSpacing(out_spacing)
    resample.SetSize(out_size)
    resample.SetOutputDirection(itk_image.GetDirection())
    resample.SetOutputOrigin(itk_image.GetOrigin())
    resample.SetTransform(sitk.Transform())
    resample.SetDefaultPixelValue(itk_image.GetPixelIDValue())

    if is_label:
        resample.SetInterpolator(sitk.sitkNearestNeighbor)
    else:
        resample.SetInterpolator(sitk.sitkLinear)

    return resample.Execute(itk_image)

def main(image_file,mask_file,qia_file):
    
    image_obj = sitk.ReadImage(mask_file)
    mask_obj = sitk.ReadImage(mask_file)

    # https://pubmed.ncbi.nlm.nih.gov/23656466/
    # https://www.atsjournals.org/doi/full/10.1164/rccm.201301-0162OC
    # https://www.atsjournals.org/doi/suppl/10.1164/rccm.201301-0162OC?role=tab

    out_spacing = [0.625,0.625,0.625]
    image_obj = resample_img(image_obj, out_spacing, is_label=False)
    mask_obj = resample_img(mask_obj, out_spacing, is_label=True)
    spacing = mask_obj.GetSpacing()
    origin = mask_obj.GetOrigin()
    direction = mask_obj.GetDirection()
    vsl_mask = sitk.GetArrayFromImage(mask_obj)
    
    raise NotImplementedError("different from scale-space-particles")

    arr_list = [np.zeros_like(vsl_mask)]
    '''
    https://en.wikipedia.org/wiki/Normal_distribution
    https://en.wikipedia.org/wiki/Full_width_at_half_maximum
    assuming vessel intensity can be fitted with a guassian distribution curve
    we can use FWHM as diameter.
    so if we have a sigma of 1mm, then diameter would be 2.355*1 mm
    '''
    # np.linspace(0,6,5) 
    for x_mm in np.arange(0.2,4,0.3):
        print(f'sigma: {x_mm}') 
        # since the image is not 1mm isotropic
        # we adjust the sigma per image spacing
        sigma = np.ones(3)*x_mm
        adjusted_sigma = sigma/np.array(spacing)
        gaussian = sitk.SmoothingRecursiveGaussianImageFilter()
        gaussian.SetSigma(adjusted_sigma)
        smoothed = gaussian.Execute(image_obj)
        '''
        ref. on sitk.ObjectnessMeasureImageFilter
        https://simpleitk.org/doxygen/latest/html/sitkObjectnessMeasureImageFilter_8h_source.html
        https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ObjectnessMeasureImageFilter.html
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.110.7722&rep=rep1&type=pdf
        https://github.com/InsightSoftwareConsortium/ITK/blob/f84720ee0823964bd135de8eb973acc40c1e70e1/Modules/Filtering/ImageFeature/include/itkHessianToObjectnessMeasureImageFilter.h 
        https://github.com/InsightSoftwareConsortium/ITK/blob/f84720ee0823964bd135de8eb973acc40c1e70e1/Modules/Filtering/ImageFeature/include/itkHessianToObjectnessMeasureImageFilter.hxx

        per https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6214740/pdf/nihms982442.pdf
        set alpha 0.53, beta 0.61 # gamma was not metioned.

        # alternative to frangi-filter, diameter can be estimated with "distance transform" if speed is a concern.
        from scipy.ndimage.morphology import distance_transform_edt
        skeleton = skeletonize(vsl_mask)
        bs_field = distance_transform_edt(vessel>0)

        '''
        myfilter = sitk.ObjectnessMeasureImageFilter()
        myfilter.SetBrightObject(True)
        myfilter.SetObjectDimension(1) # 1: lines (vessels),
        myfilter.SetAlpha(0.53)
        myfilter.SetBeta(0.61)
        myfilter.SetGamma(5.0)
        tmp_obj = myfilter.Execute(smoothed)
        arr_list.append(sitk.GetArrayFromImage(tmp_obj))

    '''
    “BVX”, where “X” indicates a range of vessel sizes in mm2 (BV5 is the volume of blood contained in
    vessels between 1.25 and 5 mm2 cross-sectional area, BV5-10
    between 5 and 10 mm2, and BV10 > 10 mm2)
    https://journals.physiology.org/doi/pdf/10.1152/japplphysiol.00458.2022

    circle area is pi*r^2
    channel 0 -> sigma 1 -> diameter 2.355*1 mm -> radius 1.1775 -> pi*r^2 = 4.35

    #sigma
    >>> np.arange(0.2,4,0.3)
    array([0.2, 0.5, 0.8, 1.1, 1.4, 1.7, 2. , 2.3, 2.6, 2.9, 3.2, 3.5, 3.8])
    #diameter
    >>> [s*2.355 for s in np.arange(0.2,4,0.3)]
    [0.47100000000000003, 1.1775, 1.8840000000000001, 2.5904999999999996, 3.2969999999999997, 4.0035, 4.709999999999999, 5.416500000000001, 6.123, 6.8294999999999995, 7.5360000000000005, 8.2425, 8.949]
    #area
    >>> [np.pi*((s*2.355/2)**2) for s in np.arange(0.2,4,0.3)]
    [0.17423351396625336, 1.0889594622890832, 2.787736223460054, 5.270563797479162, 8.53744218434641, 12.588371384061803, 17.423351396625325, 23.04238222203701, 29.44546386029681, 36.632596311404754, 44.60377957536086, 53.35901365216508, 62.89829854181745]

    '''
    arr = np.argmax(np.array(arr_list),axis=0)
    arr = arr.astype(np.uint8)
    arr[vsl_mask==0]=0

    qia_obj = sitk.GetImageFromArray(arr)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,"raw.nii.gz")

    # categorize per area
    myclass = np.zeros_like(arr)
    myclass[np.logical_and(arr>2,arr<=3)]=1 # BV5
    myclass[np.logical_and(arr>3,arr<=5)]=2 # BV5-10
    myclass[arr>5]=3 # B10

    # for ease of compuation and visualization,
    # we create a vessel mask with classification of bv5 (1), bv5-10(2), and bv10 (3)
    labels = myclass.astype(np.uint8)
    skeleton = skeletonize(vsl_mask).astype(np.uint8)
    # TODO: noisy? some small vessel due to branching may
    # have label that is larger than expected.
    labels[skeleton==0]=0

    # watershed
    bv = watershed(vsl_mask*-1, labels, mask=vsl_mask>0)
    bv = bv.astype(np.uint8)

    qia_obj = sitk.GetImageFromArray(myclass)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,"classes.nii.gz")

    qia_obj = sitk.GetImageFromArray(labels)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,"labels.nii.gz")

    qia_obj = sitk.GetImageFromArray(bv)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,qia_file)

if __name__ == "__main__":
    image_file = sys.argv[1]
    mask_file = sys.argv[2]
    qia_file = sys.argv[3]
    main(image_file,mask_file,qia_file)
