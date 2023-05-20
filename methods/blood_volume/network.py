import sys
import traceback
import numpy as np
import SimpleITK as sitk
from skimage.morphology import skeletonize
from skimage.measure import label, regionprops
from scipy import ndimage
import networkx as nx

mask_file = sys.argv[1]

mask_obj = sitk.ReadImage(mask_file)
vsl_mask = sitk.GetArrayFromImage(mask_obj)
    
print('skeletonize...')
skeleton = skeletonize(vsl_mask)
skeleton = skeleton.astype(np.int16)

print('intersection...')
weights = np.ones((3,3,3))
intersection = ndimage.convolve(skeleton,weights) > 3
intersection = label(intersection)
intersection = intersection.astype(np.int16)

print('label...')
branch = np.copy(skeleton)
branch[intersection>0]=0
branch = label(branch)
branch = branch.astype(np.int16)

FG=nx.Graph()
for x,y,z in np.where(skeleton==1):
    try:
        idx = branch[x,y,z]
        G.add_node(idx,pos=(x,y,z))
        for ox in [-1,1]:
            for oy in [-1,1]:
                for oz in [-1,1]:
                    nx,ny,nz = x+ox,y+oy,z+oz
                    nidx = branch[nx,ny,nz]
                    if nidx == 0:
                        continue
                    G.add_node(nidx,pos=(nx,ny,nz))
                    if idx == nidx:
                        weight = 0
                    else:
                        weight = 1
                    G.add_edge(idx,nidx,weight=weight)
                    print(idx,nidx,weight)
                    

        
        

    except:
        traceback.print_exc()
    
