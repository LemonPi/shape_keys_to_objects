# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2023 Sheng Zhong
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

# based on Przemysław Bągard's ApplyModifierForObjectWithShapeKeys
bl_info = {
    "name"       : "Shape keys to objects",
    "author"     : "Sheng Zhong",
    "blender"    : (3, 2, 0),
    "version"    : (0, 1, 2),
    "location"   : "Context menu",
    "description": "Create one duplicated object per shape key (excluding basis) of an object",
    "category"   : "Object Tools > Shape Keys to Objects"
}

import bpy, math
from bpy.utils import register_class
from bpy.props import *


# Algorithm:
# - Duplicate active object as many times as the number of shape keys
# - For each copy remove all shape keys except one
# - Removing last shape does not change geometry data of object
def shape_keys_to_objects(context, remove_vertex_groups=True, remove_modifiers=True):
    list_obj = []

    if context.object.data.shape_keys:
        list_shapes = [o for o in context.object.data.shape_keys.key_blocks]
    else:
        return True, None

    list_obj.append(context.view_layer.objects.active)
    for i in range(1, len(list_shapes)):
        bpy.ops.object.duplicate(linked=False)
        list_obj.append(context.view_layer.objects.active)

    for i, o in enumerate(list_obj):
        if i == 0:
            continue
        context.view_layer.objects.active = o
        key_b = o.data.shape_keys.key_blocks[i]
        # after duplication will have .001 and so on after the name
        n = o.name[:-4]
        o.name = n + "_" + key_b.name
        # also adjust the data name
        # convention is <name>_<key_b.name>Shape
        o.data.name = n + "_" + key_b.name + "Shape"
        if remove_vertex_groups:
            o.vertex_groups.clear()
        if remove_modifiers:
            o.modifiers.clear()

        for j in range(i + 1, len(list_obj))[::-1]:
            context.object.active_shape_key_index = j
            bpy.ops.object.shape_key_remove()
        for j in range(0, i):
            context.object.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove()
        # last deleted shape doesn't change object shape
        context.object.active_shape_key_index = 0
        # for some reason, changing to edit mode and return object mode
        # fix problem with mesh change when deleting last shapekey
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.shape_key_remove()

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = list_obj[0]
    list_obj[0].select_set(True)

    return True, None


class ShapeKeysToObjectsOperator(bpy.types.Operator):
    bl_idname = "object.shape_keys_to_objects"
    bl_label = "Create duplicated objects for each shape key"

    remove_vertex_groups: BoolProperty(
        name="Remove vertex groups in the copies",
        default=True,
    )
    remove_modifiers: BoolProperty(
        name="Remove modifiers in the copies",
        default=True,
    )

    def execute(self, context):
        ob = bpy.context.object
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = ob
        ob.select_set(True)
        success, error_info = shape_keys_to_objects(context, remove_vertex_groups=self.remove_vertex_groups,
                                                    remove_modifiers=self.remove_modifiers)

        if not success:
            self.report({'ERROR'}, error_info)

        return {'FINISHED'}

    def draw(self, context):
        if context.object.data.shape_keys and context.object.data.shape_keys.animation_data:
            self.layout.separator()
            self.layout.label(text="Warning:")
            self.layout.label(text="              Object contains animation data")
            self.layout.label(text="              (like drivers, keyframes etc.)")
            self.layout.label(text="              assigned to shape keys.")
            self.layout.label(text="              Those data will be lost!")
            self.layout.separator()
        self.layout.prop(self, "remove_vertex_groups")
        self.layout.prop(self, "remove_modifiers")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class DialogPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_shape_keys_to_objects"
    bl_label = "Multi Shape Keys"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    def draw(self, context):
        self.layout.operator("object.shape_keys_to_objects")


classes = [
    DialogPanel,
    ShapeKeysToObjectsOperator
]


def menu_func(self, context):
    self.layout.operator(ShapeKeysToObjectsOperator.bl_idname)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
