import bpy
class DrawUV_Switch_Settings(bpy.types.PropertyGroup):
    draw_selected_in_3dview:bpy.props.BoolProperty(default=True,
                                                   description="在3d视图中绘制选择的uv顶点（需要禁用uv同步）")
    draw_uv_in_objmode:bpy.props.BoolProperty(default=True,
                                              description="在物体模式下绘制物体的uv")
    # draw_preselected:bpy.props.BoolProperty(default=True, update=toggle_preselection)