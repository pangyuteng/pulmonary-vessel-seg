import os
import sys
import traceback
import numpy as np
import SimpleITK as sitk
from skimage.morphology import skeletonize
from skimage.measure import label, regionprops
from scipy import ndimage
import networkx as nx
import matplotlib.pyplot as plt

mask_file = sys.argv[1]
g_file = "test.gpickle"
if not os.path.exists(g_file):
    mask_obj = sitk.ReadImage(mask_file)
    vsl_mask = sitk.GetArrayFromImage(mask_obj)
        
    print('skeletonize...')
    skeleton = skeletonize(vsl_mask)
    skeleton = skeleton.astype(np.int16)
    print(f'skeleton voxel count: {np.sum(skeleton)}')
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

    G=nx.Graph()
    indices = zip(*np.where(skeleton==1))

    for x,y,z in indices:
        try:
            idx = branch[x,y,z]
            #G.add_node(idx,pos=(x,y,z))
            G.add_node(idx,pos=(x,y))
            for ox in [-1,1]:
                for oy in [-1,1]:
                    for oz in [-1,1]:
                        mx,my,mz = x+ox,y+oy,z+oz
                        nidx = branch[mx,my,mz]
                        if nidx == 0:
                            continue
                        #G.add_node(nidx,pos=(mx,my,mz))
                        G.add_node(nidx,pos=(mx,my))
                        if idx == nidx:
                            weight = 0
                        else:
                            weight = 1
                        G.add_edge(idx,nidx,weight=weight)
                        print(weight,idx,nidx,x,y,z,mx,my,mz)

        except:
            traceback.print_exc()
        
    nx.write_gpickle(G, g_file)
G = nx.read_gpickle(g_file)
print(G)
pos=nx.get_node_attributes(G,'pos')
nx.draw(G,pos)
plt.savefig('ok.png')


'''

https://www.nature.com/articles/s41598-023-31470-6

https://github.com/amy-tabb/CurveSkel-Tabb-Medeiros-2018

https://github.com/vmtk/SlicerExtension-VMTK/blob/master/Docs/CenterlineComputation.md


'''