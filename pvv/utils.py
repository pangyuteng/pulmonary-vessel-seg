import sys
import numpy as np
import SimpleITK as sitk
import imageio
import scipy.optimize as opt
import traceback

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

def extract_slice(itk_image,slice_center,slice_normal,slice_spacing,slice_radius,is_label,factor=3):

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

approximate diameter using FWHM which is ~ 2.355*sigma
https://en.wikipedia.org/wiki/Full_width_at_half_maximum

diameter = 2*radius = 2.355*sigma

radius = sigma*2.355/2
area = pi*(radius^2)

radius = np.sqrt(area/pi)
sigma = radius*2/2.355
sigma = np.sqrt(area/pi)*2/2.355

'''

#
# ref
# https://en.wikipedia.org/wiki/Gaussian_function
# https://en.wikipedia.org/wiki/Full_width_at_half_maximum
# https://stackoverflow.com/questions/27539933/2d-gaussian-fit-for-intensities-at-certain-coordinates-in-python
# https://www.astro.rug.nl/~vogelaar/Gaussians2D/2dgaussians.html
#

def gauss2d(xy, amp, x0, y0, sigma_x, sigma_y, theta):
    x, y = xy
    theta = np.radians(theta)
    sigx2 = sigma_x**2
    sigy2 = sigma_y**2
    a = np.cos(theta)**2/(2*sigx2) + np.sin(theta)**2/(2*sigy2)
    b = np.sin(theta)**2/(2*sigx2) + np.cos(theta)**2/(2*sigy2)
    c = np.sin(2*theta)/(4*sigx2) - np.sin(2*theta)/(4*sigy2)
    expo = -a*(x-x0)**2 - b*(y-y0)**2 - 2*c*(x-x0)*(y-y0)
    return amp*np.exp(expo)

def estimate_radius_fwhm(img,appx_radius):

    x = np.arange(0,img.shape[0],1)
    y = np.arange(0,img.shape[1],1)
    xy = np.meshgrid(x,y)
    xy = [xy[0].ravel(),xy[1].ravel()]
    zobs = img.ravel()

    x_coord, y_coord = int(img.shape[0]/2), int(img.shape[1]/2)
    intensity = img[x_coord,y_coord]
    try:

        appx_theta = 0 # no rotation
        guess = [intensity, x_coord, y_coord, appx_radius, appx_radius, appx_theta]
        pred_params, uncert_cov = opt.curve_fit(gauss2d, xy, zobs, p0=guess)
        zpred = gauss2d(xy, *pred_params)

        rms = np.sqrt(np.mean((zobs - zpred)**2))
        _,_,_,sigma_x,sigma_y,theta = pred_params
        fwhm_x = 2*np.sqrt(2*np.log(2))*sigma_x
        fwhm_y = 2*np.sqrt(2*np.log(2))*sigma_y

        if fwhm_x/fwhm_y > 1.5 or fwhm_y/fwhm_x > 1.5:
            raise ValueError("rejecting since not circular enough")

        pred_radius = np.mean([fwhm_x, fwhm_y])/2

        if False:
            print('guess',guess)
            print('Initial params:', guess)
            print('Predicted params:', pred_params)
            print('Residual, RMS(obs - pred):', rms)
            print("initial radius",appx_radius,"pred_radius",pred_radius)
        
        pred_mask = np.reshape(zpred,img.shape)
        pred_mask = 255*(pred_mask > pred_params[0]/2)
        return pred_radius, pred_mask.astype(np.uint8)
    except:
        if False:
            traceback.print_exc()
        return appx_radius, np.zeros_like(img).astype(np.uint8)

if __name__ == "__main__":
    

    img = imageio.imread('outdir-fwhm/slice-9998.png')
    x = np.arange(0,img.shape[0],1)
    y = np.arange(0,img.shape[1],1)
    xy = np.meshgrid(x,y)
    xy = [xy[0].ravel(),xy[1].ravel()]
    zobs = img.ravel()
    appx_radius = 1
    x_coord, y_coord = int(img.shape[0]/2), int(img.shape[1]/2)
    intensity = img[x_coord,y_coord]
    guess = [intensity, x_coord, y_coord, appx_radius, appx_radius, 1]
    pred_params, uncert_cov = opt.curve_fit(gauss2d, xy, zobs, p0=guess)
    zpred = gauss2d(xy, *pred_params)
    print('Predicted params:', pred_params)
    _,_,_,sigma_x,sigma_y,theta = pred_params

    print('Residual, RMS(obs - pred):', np.sqrt(np.mean((zobs - zpred)**2)))
    fwhm_x = 2*np.sqrt(2*np.log(2))*sigma_x
    fwhm_y = 2*np.sqrt(2*np.log(2))*sigma_y
    print(img.shape)
    print(fwhm_x,fwhm_y)