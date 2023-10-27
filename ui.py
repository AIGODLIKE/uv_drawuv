import bpy
class PT_UV_Panel(bpy.types.Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = 'IMAGE_PT_view_display'
    bl_category = "View"
    bl_label = "Draw UV"

    @classmethod
    def poll(cls, context):
        #只有uv界面显示时才渲染
        return (context.space_data and (context.space_data.show_uvedit))

    def draw(self, context):

        layout = self.layout
        col = layout.column(align=True)
        col.prop(context.scene.uv_drawuv_switch, "draw_selected_in_3dview",  text="Draw selected UV in the 3D view")
        col.prop(context.scene.uv_drawuv_switch, "draw_uv_in_objmode",  text="Draw UV in object mode")
        # col.prop(context.scene.uv_highlight, "draw_preselected", text="Draw Preselection")
        # col.prop(context.scene.uv_highlight, "show_uv_seams", text="Show UV Seams")