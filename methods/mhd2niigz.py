import sys
import SimpleITK as sitk
infile = sys.argv[1]
outfile = sys.argv[2]
img_obj = sitk.ReadImage(infile)
sitk.WriteImage(img_obj,outfile)