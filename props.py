import bpy
class DrawUV_Switch_Settings(bpy.types.PropertyGroup):
    draw_selected_in_3dview:bpy.props.BoolProperty(default=True)
    draw_uv_in_objmode:bpy.props.BoolProperty(default=True)
    # draw_preselected:bpy.props.BoolProperty(default=True, update=toggle_preselection)