#    BrainBlender_Parent_Child_Tools (C) 2018, Tom Boissonnet
#    Adapted from NeuroMorph_Parent_Child_Tools.py (C) 2016,  Anne Jorstad
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

bl_info = {
    "name": "BrainBlender Parent-Child Tools",
    "author": "Tom Boissonnet",
    "version": (0, 1, 0),
    "blender": (2, 7, 7),
    "location": "View3D > BrainBlender > Parent-Child Tools",
    "description": "Parent-Child Tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Tool"}

import bpy
from bpy.props import *
from mathutils import Vector
import mathutils
import math
import os
import sys
import re
from os import listdir
import copy
import numpy as np  # must have Blender > 2.7

bpy.types.Scene.select_recursive = bpy.props.BoolProperty \
    (
    name = "Select recursively",
    description = "Select the children of current object recursively",
    default = True
    )

def getChildren(targetObj):
    outlist = [ob for ob in bpy.context.scene.objects if ob.parent == targetObj]
    return outlist

def selChildrenRecur(targetObj):
    family = []
    if targetObj ==[]:
        return []
    else:
        for parent in targetObj:
            childList = getChildren(parent)
            family.extend(childList)
            family.extend(selChildrenRecur(childList))
        return family

# Define the panel
class ParentChildPanel(bpy.types.Panel):
    bl_label = "Parent-Child Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "BrainBlender"

    def draw(self, context):

        # From Proximity Analysis
        split = self.layout.row().split(percentage=0.5)
        col1 = split.column()
        col1.operator("object.show_children", text='Show Children')
        col2 = split.column()
        col2.operator("object.hide_children", text='Hide Children')

        # New
        split = self.layout.row().split(percentage=0.5)
        col1 = split.column()
        col1.operator("object.select_children", text='Select Children')
        col2 = split.column()
        col2.operator("object.assign_material", text = "Color branch")

        split = self.layout.row().split(percentage=0.5)
        col1 = split.column()
        col1.prop(context.scene , "select_recursive")
        col2 = split.column()
        col2.operator("mesh.delete_all_children", text = "Delete Children")




# Show/Hide children of active object
class ShowChildren(bpy.types.Operator):
    """Show all children of active object"""
    bl_idname = "object.show_children"
    bl_label = "Show all children of active object"

    def execute(self, context):
        active_ob = bpy.context.object
        if bpy.context.scene.select_recursive:
            children = selChildrenRecur([active_ob])
        else:
            children = [ob for ob in bpy.context.scene.objects if ob.parent == active_ob]
        for ob in children:
            ob.hide = False
        return {'FINISHED'}

class AssignMaterialToChildren(bpy.types.Operator):
    """Show all children of active object"""
    bl_idname = "object.assign_material"
    bl_label = "Assign one same material to all children"

    def execute(self, context):
        active_ob = bpy.context.object

        material = bpy.data.materials.new(bpy.context.object.name)
        material.use_transparency=True
        material.transparency_method = 'Z_TRANSPARENCY'
        material.alpha = 0.5
        material.diffuse_color = (0.8,0.8,0.8)

        if bpy.context.scene.select_recursive:
            children = selChildrenRecur([active_ob])
        else:
            children = [ob for ob in bpy.context.scene.objects if ob.parent == active_ob]
        for ob in children:
            if ob.data != None:
                ob.data.materials.append(material)
                ob.show_transparent=True
        return {'FINISHED'}

class HideChildren(bpy.types.Operator):
    """Hide all children of active object"""
    bl_idname = "object.hide_children"
    bl_label = "Hide all children of active object"

    def execute(self, context):
        active_ob = bpy.context.object
        if bpy.context.scene.select_recursive:
            children = selChildrenRecur([active_ob])
        else:
            children = [ob for ob in bpy.context.scene.objects if ob.parent == active_ob]
        for ob in children:
            ob.hide = True
        return {'FINISHED'}


# Select children of active object
class SelectChildren(bpy.types.Operator):
    """Select all children of active object"""
    bl_idname = "object.select_children"
    bl_label = "Select all children of active object"

    def execute(self, context):
        active_ob = bpy.context.object
        if bpy.context.scene.select_recursive:
            children = selChildrenRecur([active_ob])
        else:
            children = [ob for ob in bpy.context.scene.objects if ob.parent == active_ob]
        bpy.ops.object.select_all(action='DESELECT')
        for ob in children:
            ob.select = True
        return {'FINISHED'}


# Delete children of active object
class DeleteChildren(bpy.types.Operator):
    """Delete all children of active object (parent must be visible)"""
    bl_idname = "mesh.delete_all_children"
    bl_label = "Delete all children of active object (parent must be visible)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
        active_ob = bpy.context.object
        if bpy.context.scene.select_recursive:
            children = selChildrenRecur([active_ob])
        else:
            children = [ob for ob in bpy.context.scene.objects if ob.parent == active_ob]
        bpy.ops.object.select_all(action='DESELECT')

        for child in children:
            child.hide = False
            child.select = True
            bpy.context.scene.objects.active = child
            bpy.ops.object.delete()

        return {'FINISHED'}

if __name__ == "__main__":
    register()

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)
