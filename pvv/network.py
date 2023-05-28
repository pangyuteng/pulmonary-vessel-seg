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
from tqdm import tqdm

mask_file = sys.argv[1]
g_file = "graph.gpickle"
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
    
    os.makedirs('tabb',exist_ok=True)
    with open('tabb/0.txt','w') as f:
        f.write(f'{np.sum(skeleton)}\n')
        for x,y,z in tqdm(np.argwhere(skeleton==1)):
            f.write(f'{x} {y} {z}\n')
    with open('tabb/BB.txt','w') as f:
        x,y,z = vsl_mask.shape
        f.write(f'1\n')
        f.write(f'0 0 0 \n')
        f.write(f'{x} {y} {z}\n')

    # following methodology by Chapman 2016 https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4547695
    G=nx.Graph()
    for x,y,z in tqdm(np.argwhere(skeleton==1)):
        #idx = np.ravel_multi_index([x,y,z],skeleton.shape)
        idx = (x,y,z)
        G.add_node(idx,pos=(z,x))
        for ox in [-1,1]:
            for oy in [-1,1]:
                for oz in [-1,1]:
                    try:
                        mx,my,mz = x+ox,y+oy,z+oz
                        #midx = np.ravel_multi_index([mx,my,mz],skeleton.shape)
                        midx = mx,my,mz
                        if skeleton[mx,my,mz]==0:
                            continue
                        G.add_node(midx,pos=(mz,mx))
                        G.add_edge(idx,midx)
                    except:
                        traceback.print_exc()
        
    nx.write_gpickle(G, g_file)

G = nx.read_gpickle(g_file)

mask_obj = sitk.ReadImage(mask_file)
vsl_mask = sitk.GetArrayFromImage(mask_obj)
mygraph = np.zeros_like(vsl_mask)
node_color = []
for item in tqdm(G.degree):
    k,v = item
    x,y,z = k
    if v == 0:
        c = (0,1,0)
    elif v == 1:
        c = (1,0,0)
    else:
        c = (0,0,1)

    mygraph[x,y,z] = v+1
    node_color.append(c)

graph_obj = sitk.GetImageFromArray(mygraph)
graph_obj.CopyInformation(mask_obj)
sitk.WriteImage(graph_obj,'graph.nii.gz')

pos=nx.get_node_attributes(G,'pos')
nx.draw(G,pos,node_size=1,alpha=0.5,node_color=node_color)
plt.savefig('graph.png')


'''

python network.py wasserthal.nii.gz

docker run -it -v $PWD/tabb:/write_directory -e DO_DEMO=0 -e CC_FLAG=1 amytabb/curveskel-tabb-medeiros-2018-docker

https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4547695

https://www.nature.com/articles/s41598-023-31470-6

https://github.com/amy-tabb/CurveSkel-Tabb-Medeiros-2018

https://github.com/vmtk/SlicerExtension-VMTK/blob/master/Docs/CenterlineComputation.md


'''