import bpy
from . import prefs


class PT_UV_Panel(bpy.types.Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "settings"

    @classmethod
    def poll(cls, context):

        return True
        # return (context.space_data and (context.space_data.show_uvedit))

    def draw(self, context):

        layout = self.layout
        col = layout.column(align=True)
        col.prop(context.scene.uv_drawuv_switch, "draw_selected_in_3dview",  text="Draw selected in 3d_view")
        col.prop(context.scene.uv_drawuv_switch, "draw_uv_in_objmode",  text="Draw uv in obj_mode")
        col.prop(context.preferences.addons[__package__].preferences, "max_verts", text="Vertex Limit")
        col.prop(context.preferences.addons[__package__].preferences, "object_draw_uv",
                 text="UV Color")
