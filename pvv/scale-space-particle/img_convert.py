"""
https://simpleitk.readthedocs.io/en/master/IO.html
NrrdImageIO ( *.nrrd, *.nhdr )
NiftiImageIO ( *.nia, *.nii, *.nii.gz, *.hdr, *.img, *.img.gz )
MetaImageIO ( *.mha, *.mhd )
"""

import sys
import SimpleITK as sitk

input_file = sys.argv[1]
output_file = sys.argv[2]
input_io = sys.argv[3]

reader = sitk.ImageFileReader()
reader.SetImageIO(input_io)
reader.SetFileName(input_file)
image = reader.Execute()

writer = sitk.ImageFileWriter()
writer.SetFileName(output_file)
writer.Execute(image)

'''
python img_convert.py ok.mhd ok.nrrd
'''