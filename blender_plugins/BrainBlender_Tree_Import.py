#    BrainBlender_Tree_Import (C) 2018, Tom Boissonnet
#    Adapted from NeuroMorph_import_obj_batch.py (C) 2014,  Diego Marcos, Corrado Cali, Biagio Nigro, Anne Jorstad
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
#

bl_info = {
    "name": "BrainBlender Tree import (.obj)",
    "author": "Tom Boissonnet",
    "version": (0, 1, 0),
    "blender": (2, 7, 0),
    "location": "Scene > Wavefront (.obj) tree Import",
    "description": "Imports .obj files organized in a tree in batch, with option of applying a Remesh modifier",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

import bpy
import os

# Define import properties
bpy.types.Scene.bb_remesh_when_importing = bpy.props.BoolProperty \
    (
    name = "Use Remesh",
    description = "Add 'Remesh' modifier to imported meshes in smooth mode",
    default = True
    )
bpy.types.Scene.bb_apply_remesh = bpy.props.BoolProperty \
    (
    name = "Finalize Remesh",
    description = "Apply 'Remesh' modifier without editable preview; original meshes will be deleted",
    default = False
    )
bpy.types.Scene.bb_use_smooth_shade = bpy.props.BoolProperty \
    (
    name = "Smooth Shading",
    description = "Smooth the output faces (recommended)",
    default = True
    )
bpy.types.Scene.bb_import_parents = bpy.props.BoolProperty \
    (
    name = "Import Parents",
    description = "Import also the parent meshes",
    default = True
    )
bpy.types.Scene.bb_remesh_octree_depth = bpy.props.IntProperty \
    (
    name = "Remesh Resolution",
    description = "Octree resolution: higher values result in finer details",
    default = 7
    )
bpy.types.Scene.bb_pix_scale = bpy.props.FloatProperty \
    (
    name = "Scale (microns per pixel)",
    description = "Scale used to resize object during in import (number of microns per pixel in the image stack)",
    default = 0.025,
    min = 1e-100,
    precision=4
    )
bpy.types.Scene.bb_tree_depth = bpy.props.IntProperty \
    (
    name = "Tree depth",
    description = "The tree maximum depth at which object are loaded",
    default = 1,
    min = -1
    )

# Highlight either use_size_rescaling or use_microns_per_pix_rescaling, but not both
def _gen_order_update(name1, name2):
        def _u(self, ctxt):
            if (getattr(self, name1)):
                setattr(self, name2, False)
            elif (getattr(self, name1) == False and getattr(self, name2) == False):
                setattr(self, name1, True)
        return _u


# Define the import panel within the Scene panel
class wavefrontPanel(bpy.types.Panel):
    bl_label = "Import Tree"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        row = self.layout.row()
        row.prop(context.scene , "bb_remesh_when_importing")
        row.prop(context.scene , "bb_apply_remesh")

        row = self.layout.row()
        row.prop(context.scene , "bb_use_smooth_shade")

        row = self.layout.row()
        row.prop(context.scene , "bb_remesh_octree_depth")

        row = self.layout.row()
        row.prop(context.scene , "bb_pix_scale")

        row = self.layout.row()
        row.prop(context.scene , "bb_tree_depth")
        row.prop(context.scene , "bb_import_parents")

        row = self.layout.row()
        row.operator("bb_tree_import.obj", text='Import Object(s)', icon='MESH_ICOSPHERE')


class importButton(bpy.types.Operator):
    """Objects will be resized by the scale provided"""
    bl_idname = "bb_tree_import.obj"
    bl_label = "Import (might take several minutes)"

    directory = bpy.props.StringProperty(subtype="FILE_PATH")
    files = bpy.props.CollectionProperty(name='File path', type=bpy.types.OperatorFileListElement)

    def execute(self, context):

        items = [file.name for file in self.files]
        bb_treeImport(self.directory,items)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

bpy.types.Scene.source =  bpy.props.StringProperty(subtype="FILE_PATH")

def remesh_when_importing(obj_to_remesh):
    obj_to_remesh.modifiers.new("import_remesh", type='REMESH')
    obj_to_remesh.modifiers['import_remesh'].octree_depth = bpy.context.scene.bb_remesh_octree_depth
    obj_to_remesh.modifiers['import_remesh'].mode = 'SMOOTH'
    obj_to_remesh.modifiers['import_remesh'].use_smooth_shade = bpy.context.scene.bb_use_smooth_shade
    obj_to_remesh.modifiers['import_remesh'].use_remove_disconnected = False
    if bpy.context.scene.bb_apply_remesh == True:
        bpy.context.scene.objects.active = obj_to_remesh
        bpy.ops.object.modifier_apply(modifier='import_remesh')

def scale_object(obj_to_scale):
    s = bpy.context.scene.bb_pix_scale

    bpy.context.scene.objects.active = obj_to_scale
    bpy.data.objects.get(obj_to_scale.name).select = True
    obj_to_scale.scale = [s, s, s]  # anisotropic image stacks should be handled by the user

    bpy.ops.object.transform_apply(scale=True)

def set_origin_and_mirror(obj_to_mirror):
    resolution = bpy.context.scene.bb_pix_scale


    obj_to_mirror.modifiers.new("mirror", type='MIRROR')
    obj_to_mirror.modifiers["mirror"].use_x = False
    obj_to_mirror.modifiers["mirror"].use_y = True

    saved_location = bpy.context.scene.cursor_location.copy()
    bpy.context.scene.objects.active = obj_to_mirror
    bpy.data.objects.get(obj_to_mirror.name).select = True
    bpy.context.scene.cursor_location = (6.6, 5.7 - resolution, 4.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.context.scene.cursor_location = saved_location

def recursive_import(depth,dir, f_names=None):
    new_meshes = []
    if not os.path.isdir(dir):
        return new_meshes

    if f_names is None:
        f_names = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f)) and f[-4:] == '.obj']
    scn = bpy.context.scene

    for f in f_names:

        childs = []
        acronym = f[f.find("(")+1:f.find(")")]
        if depth!=0 and os.path.isdir(os.path.join(dir,acronym)):

            childs = recursive_import(depth-1,os.path.join(dir,acronym))

        if depth == 0 or bpy.context.scene.bb_import_parents or not os.path.isdir(os.path.join(dir,acronym)):

            bpy.ops.import_scene.obj(filepath=os.path.join(dir, f),axis_forward="Y",axis_up="Z")
            current_mesh = bpy.context.selected_objects[0]

            if bpy.context.scene.bb_remesh_when_importing:
                remesh_when_importing(current_mesh)
            scale_object(current_mesh)

        else:
            current_mesh = bpy.data.objects.new(f[:-4], None )
            scn.objects.link(current_mesh)

        new_meshes.append(current_mesh)
        for o in childs:
            o.parent = current_mesh
        if depth == 0 or bpy.context.scene.bb_import_parents or not os.path.isdir(os.path.join(dir,acronym)):
            set_origin_and_mirror(bpy.context.selected_objects[0])
    return new_meshes

def bb_treeImport(dir,files):
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    tree_depth = bpy.context.scene.bb_tree_depth

    for f in files:
        if f[-4:] == '.obj':
            parent_structure = recursive_import(tree_depth,dir,[f])



def register():
    bpy.utils.register_module(__name__)

    pass

def unregister():
    bpy.utils.unregister_module(__name__)

    pass

if __name__ == "__main__":
    register()