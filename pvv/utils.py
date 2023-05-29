import sys
import numpy as np
import SimpleITK as sitk

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

def _vrnormalize(vec,maxzero):
    '''
    Normalize a vector.
    ref. Matlab vrnormalize.m    
    '''
    norm_vec = np.linalg.norm(vec)
    if (norm_vec) <= maxzero:
        vec_n = np.zeros(vec.size)
    else:
        vec_n = np.divide(vec,norm_vec)
    return vec_n

def vrrotvec(v1,v2,epsilon=1e-12):
    '''
    Calculate rotation between two vectors.
    ref. Matlab vrrotvec.m, vrrotvec2mat.m
    '''
    v1 = np.array(v1)
    v2 = np.array(v2)
    v1n = _vrnormalize(v1,epsilon)
    v2n = _vrnormalize(v2,epsilon)
    v1xv2 = _vrnormalize(np.cross(v1n,v2n),epsilon)
    ac = np.arccos(np.vdot(v1n,v2n))    
    # build the rotation matrix
    s = np.sin(ac)
    c = np.cos(ac)
    t = 1 - c
    n = _vrnormalize(v1xv2, epsilon)
    x = n[0]
    y = n[1]
    z = n[2]
    m = [ [t*x*x + c,    t*x*y - s*z,  t*x*z + s*y],
          [t*x*y + s*z,  t*y*y + c,    t*y*z - s*x],
          [t*x*z - s*y,  t*y*z + s*x,  t*z*z + c], ]
    return np.array(m)

#
# see doc for more detail https://itk.org/ItkSoftwareGuide.pdf
#
def extract_slice(itk_image,slice_center,slice_normal,slice_spacing,slice_size,is_label):
    
    ref_normal=(0.,0.,1.) # probably we should use image_normal as ref.
    image_normal = list(itk_image.GetDirection())[6:]

    slice_direction = vrrotvec(image_normal,slice_normal)
    slice_direction= tuple(slice_direction.ravel())
    
    slice_size_mm = np.array(slice_size)*np.array(slice_spacing)
    slice_origin = np.array(slice_center) - np.array(slice_size_mm)/2.0

    resample = sitk.ResampleImageFilter()
    resample.SetOutputOrigin(slice_origin)
    resample.SetOutputDirection(slice_direction)
    resample.SetOutputSpacing(slice_spacing)
    resample.SetSize(slice_size) # unit is voxel

    axis = slice_normal
    rotation_center = slice_center # remember to set center in case you want update the angle
    angle = 0
    translation = (0,0,0)
    scale_factor = 1
    similarity = sitk.Similarity3DTransform(
        scale_factor, axis, angle, translation, rotation_center
    )

    affine = sitk.AffineTransform(3)
    affine.SetMatrix(similarity.GetMatrix())
    affine.SetTranslation(similarity.GetTranslation())
    affine.SetCenter(similarity.GetCenter())

    resample.SetTransform(affine)
    resample.SetDefaultPixelValue(itk_image.GetPixelIDValue())

    if is_label:
        resample.SetInterpolator(sitk.sitkNearestNeighbor)
    else:
        resample.SetInterpolator(sitk.sitkLinear)

    return resample.Execute(itk_image)

if __name__ == "__main__":

    img_file = sys.argv[1]
    itk_image = sitk.ReadImage(img_file)
    
    aorta_coord = [253,172,150]
    slice_center = itk_image.TransformContinuousIndexToPhysicalPoint(aorta_coord)
    print('aorta_coord',slice_center)
    slice_normal = (0.0,0.0,1.0)
    slice_spacing = (2.0,2.0,2.0) # 1mm isotropic
    slice_size = (50,50,1) # unit is voxels
    is_label = False

    slice_file = 'slice.nii.gz'
    print(slice_center,slice_normal,slice_size)
    slice_obj = extract_slice(itk_image,slice_center,slice_normal,slice_spacing,slice_size,is_label)
    sitk.WriteImage(slice_obj,slice_file)

