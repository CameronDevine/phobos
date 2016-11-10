#!/usr/bin/python
# coding=utf-8

"""
Copyright 2014, University of Bremen & DFKI GmbH Robotics Innovation Center

This file is part of Phobos, a Blender Add-On to edit robot models.

Phobos is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License
as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

Phobos is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Phobos.  If not, see <http://www.gnu.org/licenses/>.

File phobosgui.py

Created on 6 Jan 2014

@author: Kai von Szadkowski
"""

import os
import bpy
import bgl
from bpy.props import *
from . import defs
from phobos.operators.io import loadModelsAndPoses


def register():
    print("Registering phobosgui...")
    bpy.types.Object.phobostype = EnumProperty(
        items=defs.phobostypes,
        name="type",
        description="Phobos object type")

    bpy.types.World.phobosexportsettings = PointerProperty(type=defs.PhobosExportSettings)

    bpy.utils.register_class(Models_Poses_UIList)
    bpy.types.Scene.active_ModelPose = bpy.props.IntProperty(name="Index of current pose", default=0,update=showPreview)
    bpy.types.Scene.preview_visible = bpy.props.BoolProperty(name="Is the draw preview operator running", default=False)
    bpy.types.Scene.redraw_preview = bpy.props.BoolProperty(name="Should we redraw the preview_template", default=False)
    loadModelsAndPoses()


def unregister():
    print("Unregistering phobosgui...")


class Models_Poses_UIList(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_show = False
        im = item
        modelsPosesColl = bpy.context.user_preferences.addons["phobos"].preferences.models_poses
        if im.name in modelsPosesColl.keys():
            coll_item = modelsPosesColl[im.name]
            if coll_item.type == "robot_name":
                layout.label(text=coll_item.label, translate=False, icon=coll_item.icon)
            else:
                sLayout = layout.split(0.1)
                sLayout.label(text="")
                if im.filepath != '':
                    sLayout.label(text=coll_item.label, translate=False,icon_value=icon)
                else:
                    sLayout.label(text=coll_item.label, translate=False, icon=coll_item.icon)

    def filter_items(self, context, data, propname):
        images = getattr(data, propname)
        flt_flags = [self.bitflag_filter_item] * len(images)

        modelsPosesColl = bpy.context.user_preferences.addons["phobos"].preferences.models_poses

        # Filter items. Only show robots. Hide all other images
        for idx, im in enumerate(images):
            if im.name in modelsPosesColl.keys():
                curr_model = modelsPosesColl[im.name]
                if curr_model.hide and not (curr_model.type == "robot_name"):
                    flt_flags[idx] &= ~self.bitflag_filter_item
            else:
                flt_flags[idx] &= ~self.bitflag_filter_item

        helper_funcs = bpy.types.UI_UL_list
        # Reorder by name
        flt_neworder = []
        noPreviewIndex = 0
        for im in images:
            newIndex = 0
            if im.name in modelsPosesColl.keys():
                newIndex = modelsPosesColl.keys().index(im.name)
            else:
                newIndex = len(modelsPosesColl) + noPreviewIndex
                noPreviewIndex += 1
            flt_neworder.append(newIndex)

        return flt_flags, flt_neworder


class MessageOperator(bpy.types.Operator):
    bl_idname = "error.message"
    bl_label = "Display a message in a window"
    type = StringProperty()
    message = StringProperty()

    def execute(self, context):
        self.report({'INFO'}, self.message)
        print(self.message)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        result = wm.invoke_popup(self, width=400, height=200)
        return result

    def draw(self, context):
        self.layout.label("Phobos")
        row = self.layout  # .split(0.25)
        row.prop(self, "type")
        row.prop(self, "message")
        # row = self.layout#.split(0.80)
        row.label("")
        row.operator("error.ok")


class OkOperator(bpy.types.Operator):
    bl_idname = "error.ok"
    bl_label = "OK"

    def execute(self, context):
        return {'FINISHED'}

def showPreview(self,value):
    bpy.ops.scene.change_preview()


class PhobosToolsPanel(bpy.types.Panel):
    """A Custom Panel in the Phobos viewport toolbar"""
    bl_idname = "TOOLS_PT_PHOBOS_TOOLS"
    bl_label = "Editing Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Phobos'
    #bl_context = ''

    def draw(self, context):
        layout = self.layout

        # Tools & Selection Menu
        #layout.separator()
        tsinlayout = layout.split()
        tsc1 = tsinlayout.column(align=True)
        tsc1.label(text="Select...", icon='HAND')
        tsc1.operator('phobos.select_root', text='Root')
        tsc1.operator('phobos.select_model', text='Robot')
        tsc1.operator('phobos.select_objects_by_phobostype', text="by Phobostype")
        tsc1.operator('phobos.select_objects_by_name', text="by Name")
        tsc2 = tsinlayout.column(align=True)
        tsc2.label(text="Tools", icon='MODIFIER')
        tsc2.operator('phobos.sort_objects_to_layers', text="Set Objects to Layers", icon='IMGDISPLAY')
        tsc2.operator('phobos.set_xray', text='X-Ray Vision')
        tsc2.operator('phobos.toggle_namespaces', text='Toggle Namespace')
        tsc2.operator('phobos.show_distance', text='Measure Distance')
        tsc2.operator('phobos.check_dict', text='Validate')


class PhobosModelPanel(bpy.types.Panel):
    """A Custom Panel in the Phobos viewport toolbar"""
    bl_idname = "TOOLS_PT_PHOBOS_MODEL"
    bl_label = "Model Editing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Phobos'
    #bl_context = ''

    def draw_header(self, context):
        self.layout.label(icon='OUTLINER_DATA_ARMATURE')

    def draw(self, context):
        layout=self.layout

        # Robot Model Menu
        inlayout = layout.split()
        rc1 = inlayout.column(align=True)
        rc2 = inlayout.column(align=True)
        rc1.operator('phobos.name_model', text='Name Robot')
        rc2.operator('phobos.set_version', text='Set Version')

        inlayout = layout.split()
        c1 = inlayout.column(align=True)
        c2 = inlayout.column(align=True)
        c1.operator('phobos.set_phobostype', text='Set Phobostype')
        c1.operator('phobos.batch_rename')
        c1.operator('phobos.edityamldictionary', text='Edit Object Dictionary', icon='TEXT')
        c2.operator('phobos.batch_property', text='Edit Custom Property', icon='GREASEPENCIL')
        c2.operator('phobos.copy_props', text='Copy Custom Property', icon='GHOST')
        c2.operator('phobos.rename_custom_property', text='Rename Custom Property', icon='SYNTAX_OFF')

        layout.separator()
        kinlayout = layout.split()
        kc1 = kinlayout.column(align=True)
        kc2 = kinlayout.column(align=True)
        kc1.label(text='Kinematics', icon='POSE_DATA')
        kc1.operator("phobos.create_link", text="Create Link(s)")
        kc1.operator('phobos.define_joint_constraints', text="Define Joint(s)")
        kc1.operator('phobos.create_inertial_objects', text="Create Inertial Object(s)")
        kc1.operator("phobos.create_mimic_joint", text="Mimic Joint")
        kc1.operator('phobos.add_chain', text='Define Kinematic Chain', icon='CONSTRAINT')
        kc2.label(text='Visual/Collision', icon='GROUP')
        kc2.operator('phobos.create_collision_objects', text="Create Collision Object(s)")
        kc2.operator('phobos.set_geometry_type', text="Set Geometry Type(s)")
        kc2.operator('phobos.set_collision_group', text="Set Collision Group")
        kc2.operator('phobos.smoothen_surface', text="Smoothen Surface")
        kc2.operator('phobos.refine_lod', text="Refine LoD")
        #kc1.operator('phobos.set_origin_to_com', text="Set Origin to COM")

        # Masses, Inertia & Hardware
        layout.separator()
        minlayout = layout.split()
        hw1 = minlayout.column(align=True)
        hw1.label(text="Hardware", icon='MOD_SCREW')
        hw1.operator('phobos.attach_motor', text="Add/Edit Motor")
        hw1.operator('phobos.add_sensor', text="Add/Edit Sensor")
        hw1.operator("phobos.add_controller", text="Add/Edit Controller")
        mc1 = minlayout.column(align=True)
        mc1.label(text="Masses & Inertia", icon='PHYSICS')
        mc1.operator('phobos.calculate_mass', text='Show Mass')
        mc1.operator('phobos.set_mass', text='Set Mass')
        mc1.operator('phobos.sync_masses', text='Sync Masses')
        mc1.operator('phobos.edit_inertia', text='Edit Inertia')


class PhobosScenePanel(bpy.types.Panel):
    """A Custom Panel in the Phobos viewport toolbar"""
    bl_idname = "TOOLS_PT_PHOBOS_SCENE"
    bl_label = "Scene Editing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Phobos'

    def draw_header(self, context):
        self.layout.label(icon='SCENE_DATA')

    def draw(self, context):
        layout = self.layout
        layout.label(text="Scene Editing", icon="WORLD")
        iinlayout = layout.split()
        ic1 = iinlayout.column(align=True)
        ic1.operator("phobos.add_heightmap", text="Create Heightmap")
        ic2 = iinlayout.column(align=True)
        ic2.operator('phobos.define_entity', text='Define Entity')

        layout.label(text="Robotmodels and Poses", icon="MOD_ARMATURE")
        #layout.operator("scene.load_backed_models_operator", text="Load Models", icon="LIBRARY_DATA_DIRECT")
        #layout.operator("scene.reload_models_and_poses_operator", text="Reload Models and Poses", icon="LIBRARY_DATA_DIRECT")


        modelsPosesColl = bpy.context.user_preferences.addons["phobos"].preferences.models_poses
        for model_pose in modelsPosesColl:
            if not model_pose.name in bpy.data.images.keys():
                if model_pose.type == 'robot_name':
                    bpy.data.images.new(model_pose.name,0,0)
                elif 'robot_pose':
                    if model_pose.preview != '':
                        if os.path.split(model_pose.preview)[-1] in bpy.data.images.keys():
                            bpy.data.images[os.path.split(model_pose.preview)[-1]].reload()
                        im = bpy.data.images.load(model_pose.preview)
                        model_pose.name  = im.name
                        #im.name = model_pose.name
                        im.gl_load(0, bgl.GL_LINEAR, bgl.GL_LINEAR)
                    else:
                        print(model_pose.name)
                        bpy.data.images.new(model_pose.name, 0, 0)

        layout.template_list("Models_Poses_UIList", "",  bpy.data, "images", context.scene, "active_ModelPose")

#        layout.template_preview(bpy.data.textures[context.scene.active_bakeModel])
#        layout.template_preview(preview_mat.active_texture,
#                                parent=preview_mat,
#                                slot=preview_mat.texture_slots[preview_mat.active_texture_index],
#                                preview_id="phobos_model_preview")

        layout.operator('scene.phobos_import_selected_lib_robot', text="Import Selected Robot Bake", icon="COPYDOWN")
        pinlayout = layout.split()
        pc1 = pinlayout.column(align=True)
        pc1.operator('phobos.store_pose2', text='Store Current Pose')
        pc2 = pinlayout.column(align=True)
        pc2.operator('phobos.load_pose2', text='Load Selected Pose')

        layout.operator("phobos.export_current_poses", text="Export Selected Pose", icon="OUTLINER_OB_ARMATURE")
        layout.operator("phobos.export_all_poses", text="Export All Poses", icon="OUTLINER_OB_ARMATURE")


class PhobosExportPanel(bpy.types.Panel):
    """A Custom Panel in the Phobos viewport toolbar"""
    bl_idname = "TOOLS_EXPORT_PT_PHOBOS"
    bl_label = "phobos: Export & Import"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Phobos'

    def draw_header(self, context):
        self.layout.label(icon='FILESEL')

    def draw(self, context):
        expsets = bpy.data.worlds[0].phobosexportsettings
        layout = self.layout

        #export robot model options
        self.layout.label(text="Model Export Settings")
        pathlayout = self.layout.split(percentage=0.85)
        p1 = pathlayout.column(align=False)
        p2 = pathlayout.column(align=False)
        p1.prop(expsets, "path")
        p2.operator('phobos.choose_export_path', text='', icon='FILE_FOLDER')
        ginlayout = self.layout.split()
        g1 = ginlayout.column(align=True)
        g1.prop(expsets, "relativePath")
        g1.prop(expsets, "structureExport", text="Structure Export")
        g2 = ginlayout.column(align=True)
        g2.prop(expsets, "decimalPlaces")

        layout.separator()

        inlayout = self.layout.split()
        c1 = inlayout.column(align=True)
        c1.label(text="Mesh export")
        c1.prop(expsets, "exportMeshes", text="Export Meshes")

        c1.prop(expsets, "useBobj", text="Use .bobj format")
        c1.prop(expsets, "useObj", text="Use .obj format")
        c1.prop(expsets, "useStl", text="Use .stl format")
        c1.prop(expsets, "useDae", text="Use .dae format")
        if expsets.useObj:
            labeltext = "URDF uses .obj"
        elif expsets.useBobj:
            labeltext = "URDF uses .bobj"
        elif expsets.useStl:
            labeltext = "URDF uses .stl"
        elif expsets.useDae:
            labeltext = "URDF uses .dae"
        else:
            labeltext = "URDF uses .obj"
        c1.label(text=labeltext)
        c2 = inlayout.column(align=True)
        c2.label(text="Robot Data Export")
        #c2.prop(expsets, "exportMARSscene", text="as MARS scene")
        c2.prop(expsets, "exportSMURF", text="As SMURF")
        c2.prop(expsets, "exportURDF", text="As URDF")
        c2.prop(expsets, "exportSRDF", text="With SRDF")
        c2.prop(expsets, "exportYAML", text="As YAML dump")
        c2.prop(expsets, "exportTextures", text="Export textures")
        c2.prop(expsets, "exportCustomData", text="Export custom data")

        ec1 = layout.column(align=True)
        ec1.operator("phobos.export_robot", text="Export Robot Model", icon="PASTEDOWN")
        ec2 = layout.column(align=True)
        ec2.operator("phobos.import_robot_model", text="Import Robot Model", icon="COPYDOWN")

#        layout.separator()
#        layout.label(text="Baking")
#        layout.operator("phobos.export_bake", text="Bake Robot Model", icon="OUTLINER_OB_ARMATURE")
#        layout.operator("phobos.create_robot_instance", text="Create Robot Lib Instance", icon="RENDERLAYERS")

        layout.separator()

        layout.label(text="Export Scene")
        self.layout.prop(expsets, "sceneName", text="Name")
        self.layout.prop(expsets, "heightmapMesh", text="export heightmap as mesh")
        layout.operator("phobos.export_scene", text="Export SMURF Scene", icon="WORLD_DATA")


class PhobosObjectPanel(bpy.types.Panel):
    bl_idname = "phobos.PT_PHOBOS"
    bl_label = "phobos: Object Panel Displaying Custom Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    bl_category = 'Phobos'

    def draw_header(self, context):
        self.layout.label(icon='SMOOTH')

    def draw(self, context):

        layout = self.layout

        #the following is used for real pre-defined rather than custom properties
        #row_type.prop(bpy.context.active_object, "type")
        row_type = layout.row()
        row_type.label(icon="OBJECT_DATA")
        #row_type.prop_enum(bpy.context.active_object, '["type"]', "node")
        #row_type.prop_enum(bpy.context.active_object, 'phobostype')
        row_type.prop(bpy.context.active_object, 'phobostype')

        box_props = layout.box()
        try:
            for prop in defs.type_properties[bpy.context.active_object.phobostype]:
                #box_props.label(prop)
                if prop in bpy.context.active_object:
                    box_props.prop(bpy.context.active_object, '["' + prop + '"]')
        except KeyError:
            print("Key could not be found.")
            #else:
            #    bpy.context.active_object[prop] = defs.type_properties[bpy.context.active_object.phobostype+"_default"]


# if script is run directly, register contained classes
if __name__ == "__main__":
    register()
