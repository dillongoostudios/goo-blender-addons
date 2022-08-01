# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from ...base_rig import BaseRig

from ...utils.naming import strip_org, make_deformer_name
from ...utils.widgets import layout_widget_dropdown, create_registered_widget
from ...utils.widgets_basic import create_bone_widget

from .raw_copy import RelinkConstraintsMixin


class Rig(BaseRig, RelinkConstraintsMixin):
    """ A "copy" rig.  All it does is duplicate the original bone and
        constrain it.
        This is a control and deformation rig.

    """
    def find_org_bones(self, pose_bone):
        return pose_bone.name


    def initialize(self):
        """ Gather and validate data about the rig.
        """
        self.org_name     = strip_org(self.bones.org)

        self.make_control = self.params.make_control
        self.make_widget  = self.params.make_widget
        self.make_deform  = self.params.make_deform


    def generate_bones(self):
        bones = self.bones

        # Make a control bone (copy of original).
        if self.make_control:
            bones.ctrl = self.copy_bone(bones.org, self.org_name, parent=True)

        # Make a deformation bone (copy of original, child of original).
        if self.make_deform:
            bones.deform = self.copy_bone(bones.org, make_deformer_name(self.org_name), bbone=True)


    def parent_bones(self):
        bones = self.bones

        if self.make_deform:
            self.set_bone_parent(bones.deform, bones.org, use_connect=False)

        new_parent = self.relink_bone_parent(bones.org)

        if self.make_control and new_parent:
            self.set_bone_parent(bones.ctrl, new_parent)


    def configure_bones(self):
        bones = self.bones

        if self.make_control:
            self.copy_bone_properties(bones.org, bones.ctrl)


    def rig_bones(self):
        bones = self.bones

        self.relink_bone_constraints(bones.org)

        if self.make_control:
            self.relink_move_constraints(bones.org, bones.ctrl, prefix='CTRL:')

            # Constrain the original bone.
            self.make_constraint(bones.org, 'COPY_TRANSFORMS', bones.ctrl, insert_index=0)

        if self.make_deform:
            self.relink_move_constraints(bones.org, bones.deform, prefix='DEF:')


    def generate_widgets(self):
        bones = self.bones

        if self.make_control:
            # Create control widget
            if self.make_widget:
                create_registered_widget(self.obj, bones.ctrl, self.params.super_copy_widget_type or 'circle')
            else:
                create_bone_widget(self.obj, bones.ctrl)


    @classmethod
    def add_parameters(self, params):
        """ Add the parameters of this rig type to the
            RigifyParameters PropertyGroup
        """
        params.make_control = bpy.props.BoolProperty(
            name        = "Control",
            default     = True,
            description = "Create a control bone for the copy"
        )

        params.make_widget = bpy.props.BoolProperty(
            name        = "Widget",
            default     = True,
            description = "Choose a widget for the bone control"
        )

        params.super_copy_widget_type = bpy.props.StringProperty(
            name        = "Widget Type",
            default     = 'circle',
            description = "Choose the type of the widget to create"
        )

        params.make_deform = bpy.props.BoolProperty(
            name        = "Deform",
            default     = True,
            description = "Create a deform bone for the copy"
        )

        self.add_relink_constraints_params(params)


    @classmethod
    def parameters_ui(self, layout, params):
        """ Create the ui for the rig parameters.
        """
        layout.prop(params, "make_control")

        row = layout.split(factor=0.3)
        row.prop(params, "make_widget")
        row.enabled = params.make_control

        row2 = row.row(align=True)
        row2.enabled = params.make_widget
        layout_widget_dropdown(row2, params, "super_copy_widget_type", text="")

        layout.prop(params, "make_deform")

        self.add_relink_constraints_ui(layout, params)

        if params.relink_constraints and (params.make_control or params.make_deform):
            col = layout.column()
            if params.make_control:
                col.label(text="'CTRL:...' constraints are moved to the control bone.", icon='INFO')
            if params.make_deform:
                col.label(text="'DEF:...' constraints are moved to the deform bone.", icon='INFO')


def create_sample(obj):
    """ Create a sample metarig for this rig type.
    """
    # generated by rigify.utils.write_metarig
    bpy.ops.object.mode_set(mode='EDIT')
    arm = obj.data

    bones = {}

    bone = arm.edit_bones.new('Bone')
    bone.head[:] = 0.0000, 0.0000, 0.0000
    bone.tail[:] = 0.0000, 0.0000, 0.2000
    bone.roll = 0.0000
    bone.use_connect = False
    bones['Bone'] = bone.name

    bpy.ops.object.mode_set(mode='OBJECT')
    pbone = obj.pose.bones[bones['Bone']]
    pbone.rigify_type = 'basic.super_copy'
    pbone.lock_location = (False, False, False)
    pbone.lock_rotation = (False, False, False)
    pbone.lock_rotation_w = False
    pbone.lock_scale = (False, False, False)
    pbone.rotation_mode = 'QUATERNION'

    bpy.ops.object.mode_set(mode='EDIT')
    for bone in arm.edit_bones:
        bone.select = False
        bone.select_head = False
        bone.select_tail = False
    for b in bones:
        bone = arm.edit_bones[bones[b]]
        bone.select = True
        bone.select_head = True
        bone.select_tail = True
        arm.edit_bones.active = bone

    return bones
