import sys
import numpy as np
import SimpleITK as sitk
import imageio

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
    resample.SetDefaultPixelValue(0)

    if is_label:
        resample.SetInterpolator(sitk.sitkNearestNeighbor)
    else:
        resample.SetInterpolator(sitk.sitkLinear)

    return resample.Execute(itk_image)

def _vrnormalize(vec,epsilon=1e-12):
    '''
    Normalize a vector.
    ref. Matlab vrnormalize.m    
    '''
    norm_vec = np.linalg.norm(vec)
    if norm_vec <= epsilon:
        vec_n = np.zeros(vec.size)
    else:
        vec_n = np.divide(vec,norm_vec)
    return vec_n

def vrrotvec(v1,v2):
    '''
    Calculate rotation between two vectors.
    ref. Matlab vrrotvec.m, vrrotvec2mat.m
    '''
    v1 = np.array(v1)
    v2 = np.array(v2)
    v1n = _vrnormalize(v1)
    v2n = _vrnormalize(v2)
    v1xv2 = _vrnormalize(np.cross(v1n,v2n))
    ac = np.arccos(np.vdot(v1n,v2n))
    # build the rotation matrix
    s = np.sin(ac)
    c = np.cos(ac)
    t = 1 - c
    n = _vrnormalize(v1xv2)
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

def get_orthonormals(slice_normal):
    epsilon = 1e-12

    k = slice_normal
    
    x = np.random.randn(3)  # take a random vector

    x -= x.dot(k) * k       # make it orthogonal to k
    x /= np.linalg.norm(x)  # normalize it
    y = np.cross(k, x)      # cross product with k

    # print(np.linalg.norm(x), np.linalg.norm(y)) # 1,1
    # print(np.cross(x, y))          # same as k
    # print(np.dot(x, y),np.dot(x, k),np.dot(y, k))
    assert(np.dot(x, y) <  1e-8)
    assert(np.dot(x, k) <  1e-8)
    assert(np.dot(y, k) <  1e-8) # move this to test case
    return x, y

def get_slice_origin(slice_center,slice_normal,slice_radius):

    epsilon = 1e-12

    image_normal = np.array([0.,0.,1.])
    slice_direction = vrrotvec(image_normal,slice_normal).ravel()

    direction_x = np.array(slice_direction[0:3])
    direction_y = np.array(slice_direction[3:6])
    direction_z = np.array(slice_direction[6:9])

    #direction_x, direction_y = get_orthonormals(slice_normal)
    vec_on_plane = _vrnormalize(direction_x+direction_y)

    # 45-45-90 triangle
    # side length ratio: 1:1:sqrt(2)
    # so the offset from center of square is...
    #
    offset = slice_radius*2/np.sqrt(2)
    slice_origin = slice_center - vec_on_plane*offset

    # slice_origin should be on the plane
    a,b,c = tuple(direction_z)
    x,y,z = tuple(slice_center)
    d = -a*x-b*y-c*z
    ox,oy,oz = slice_origin

    #print(a*ox+b*oy+c*oz+d,a*ox+b*oy+c*oz+d <= 1e-4)
    assert(a*ox+b*oy+c*oz+d <= 1e-4)

    return tuple(slice_origin)

def extract_slice(itk_image,slice_center,slice_normal,slice_spacing,slice_radius,is_label):

    image_normal = (0,0,1)
    rotation_matrix = vrrotvec(image_normal,slice_normal)

    slice_direction = rotation_matrix.ravel()

    direction_x = np.array(slice_direction[0:3])
    direction_y = np.array(slice_direction[3:6])
    direction_z = np.array(slice_direction[6:9])

    slice_direction = []
    slice_direction.extend(direction_x)
    slice_direction.extend(direction_y)
    slice_direction.extend(direction_z*-1) # what???
    slice_direction = np.array(slice_direction)


    slice_origin = get_slice_origin(slice_center,slice_normal,slice_radius)
    radius_voxel = int(np.array(slice_radius)/np.array(slice_spacing[0]))
    factor = 2
    slice_size = (radius_voxel*factor,radius_voxel*factor,1)
    resample = sitk.ResampleImageFilter()
    
    resample.SetOutputOrigin(slice_origin)
    resample.SetOutputDirection(slice_direction)
    resample.SetOutputSpacing(slice_spacing)
    resample.SetSize(slice_size) # unit is voxel
    resample.SetTransform(sitk.Transform())
    resample.SetDefaultPixelValue(itk_image.GetPixelIDValue())

    if is_label:
        resample.SetInterpolator(sitk.sitkNearestNeighbor)
    else:
        resample.SetInterpolator(sitk.sitkLinear)

    itk_image = resample.Execute(itk_image)
    
    if False:
        print('slice_origin patient space',slice_origin)
        print('slice_origin, patient space',itk_image.TransformContinuousIndexToPhysicalPoint([0,0,0]))
        print('slice_origin image space', itk_image.TransformPhysicalPointToContinuousIndex(slice_origin))
        print('---')
        print('slice_center, patient space',slice_center)
        print('slice_center, patient space',itk_image.TransformContinuousIndexToPhysicalPoint([radius_voxel,radius_voxel,0]))
        print('slice_center image space',itk_image.TransformPhysicalPointToContinuousIndex(slice_center))
        
        
        print('GetOrigin',itk_image.GetOrigin())
        print('slice_origin',slice_origin)
        print('GetOrigin',itk_image.GetOrigin())
        print('GetDirection',itk_image.GetDirection())
        print('GetSpacing',itk_image.GetSpacing())
        print('GetSize',itk_image.GetSize())
        print('return!')
    return itk_image




import scipy.optimize as opt
# ref  https://gist.github.com/nvladimus/fc88abcece9c3e0dc9212c2adc93bfe7
"""Function to fit, returns 2D gaussian function as 1D array"""
def twoD_GaussianScaledAmp(xy, xo, yo, sigma_x, sigma_y, amplitude, offset):
    (x, y) = xy
    xo = float(xo)
    yo = float(yo)    
    g = offset + amplitude*np.exp( - (((x-xo)**2)/(2*sigma_x**2) + ((y-yo)**2)/(2*sigma_y**2)))
    return g.ravel()

"""Get FWHM(x,y) of a blob by 2D gaussian fitting
Parameter:
    img - image as numpy array
Returns: 
    FWHMs in pixels, along x and y axes.
"""
#def getFWHM_GaussianFitScaledAmp(img):
def estimate_radius_fwhm(img,minval,maxval):
    x = np.linspace(0, img.shape[1], img.shape[1])
    y = np.linspace(0, img.shape[0], img.shape[0])
    x, y = np.meshgrid(x, y)
    #Parameters: xpos, ypos, sigmaX, sigmaY, amp, baseline
    initial_guess = (img.shape[1]/2,img.shape[0]/2,10,10,1,0)
    # subtract background and rescale image into [0,1], with floor clipping
    img_scaled = ( (img - minval) / (maxval-minval)).clip(0,1)
    popt, pcov = opt.curve_fit(twoD_GaussianScaledAmp, (x, y), 
                               img_scaled.ravel(), p0=initial_guess,
                               bounds = ((img.shape[1]*0.4, img.shape[0]*0.4, 1, 1, 0.5, -0.1),
                                     (img.shape[1]*0.6, img.shape[0]*0.6, img.shape[1]/2, img.shape[0]/2, 1.5, 0.5)))
    xcenter, ycenter, sigmaX, sigmaY, amp, offset = popt[0], popt[1], popt[2], popt[3], popt[4], popt[5]
    FWHM_x = np.abs(4*sigmaX*np.sqrt(-0.5*np.log(0.5)))
    FWHM_y = np.abs(4*sigmaY*np.sqrt(-0.5*np.log(0.5)))
    return FWHM_x, FWHM_y