#    Brain structures export (C) 2018, Tom Boissonnet
#    Wrapper for Allen brain institute API
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/


from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from skimage import measure
from skimage.draw import ellipsoid

from allensdk.core.reference_space import ReferenceSpace
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.config.manifest import Manifest
from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.core.structure_tree import StructureTree

import os
import nrrd
import numpy as np

# Need to download http://help.brain-map.org/display/mouseconnectivity/API

def export_obj(structure_id, name, path):
    """Export given structure id to the give path"""
#    acronym = tree.get_structures_by_id([structure_id])[0]["acronym"]
#    acronym = acronym.replace("/","-")
    structure_mask = rsp.make_structure_mask([structure_id])
    half_mask = structure_mask[:,:228,:]
#    half_mask[:,228,:] = 0
    try:
        verts, faces, normals, values = measure.marching_cubes_lewiner(half_mask, 0)
    except (RuntimeError):
        return

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path+name+".obj",'w') as file:
        for vert in verts:
            file.write("v "+str(vert[0])+" "+str(vert[1])+" "+str(vert[2])+"\n")
        for face in faces:
            file.write("f "+str(face[0]+1)+" "+str(face[1]+1)+" "+str(face[2]+1)+"\n")

graph_id = 1 # Graph_id is the id of the structure we want to load. 1 is the id of the adult mouse structure graph

oapi = OntologiesApi()
structure_graph = oapi.get_structures_with_sets([graph_id])
# This removes some unused fields returned by the query
structure_graph = StructureTree.clean_structures(structure_graph)
tree = StructureTree(structure_graph)

# the annotation download writes a file, so we will need somwhere to put it
annotation_dir = 'E:\\Histology\\allen_rsp'

annotation_path = os.path.join(annotation_dir, 'annotation_10.nrrd')

# this is a string which contains the name of the latest ccf version
annotation_version = MouseConnectivityApi.CCF_VERSION_DEFAULT

mcapi = MouseConnectivityApi()
#Next line commented because the annotation volume is already downloaded
mcapi.download_annotation_volume(annotation_version, 10, annotation_path)

annotation, meta = nrrd.read(annotation_path)

swapped_ann = np.swapaxes(annotation,1,2)
swapped_ann = swapped_ann[:,:,::-1] #Revert the z axis so the 0 is the ventral part

rsp = ReferenceSpace(tree, swapped_ann, [10, 10, 10])

root_path = "E:\\Histology\\brain_structures_half_not_close_10\\"
##Here comes the obj creation
for struct in structure_graph[:1]:
    path_parent = ""
    for parent_id in struct["structure_id_path"][:-1]:
        name_parent = tree.get_structures_by_id([parent_id])[0]["acronym"]
        name_parent = name_parent.replace("/","-")
        path_parent = path_parent + name_parent + "\\"
    struct_id = struct["id"]
    name = tree.get_structures_by_id([struct_id])[0]["name"] + " ("+ tree.get_structures_by_id([struct_id])[0]["acronym"] + ")"
    name = name.replace("/","-")
    export_obj(struct_id,name, root_path+path_parent)
    print(struct["name"])