import bpy
from . import prefs


class PT_UV_Panel(bpy.types.Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    # bl_parent_id = 'IMAGE_PT_view_display'
    bl_category = "View"
    bl_label = "绘制uv高亮"

    @classmethod
    def poll(cls, context):
        #只有uv界面显示时才渲染
        return True
        # return (context.space_data and (context.space_data.show_uvedit))

    def draw(self, context):

        layout = self.layout
        col = layout.column(align=True)
        col.prop(context.scene.uv_drawuv_switch, "draw_selected_in_3dview",  text="绘制uv顶点")
        col.prop(context.scene.uv_drawuv_switch, "draw_uv_in_objmode",  text="绘制uv")
        col.prop(context.preferences.addons[__package__].preferences, "max_verts", text="顶点限制")
        col.prop(context.preferences.addons[__package__].preferences, "object_draw_uv",
                 text="UV颜色")
