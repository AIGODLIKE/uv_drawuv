import bpy


class DrawUV_Color_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
#object override
    selection_verts_3dview: bpy.props.FloatVectorProperty(name="顶点颜色",
                                                          subtype="COLOR",
                                                          default=(
                                                              0.0, 1.0, 0.3, 1.0),
                                                          size=4,
                                                          min=0.0,
                                                          max=1.0)

    selection_edges_3dview: bpy.props.FloatVectorProperty(name="线框颜色",
                                                          subtype="COLOR",
                                                          default=(
                                                              0.0, 1.0, 0.3, 1.0),
                                                          size=4,
                                                          min=0.0,
                                                          max=1.0)

    selection_faces_3dview: bpy.props.FloatVectorProperty(name="面颜色",
                                                          subtype="COLOR",
                                                          default=(
                                                              0.0, 1.0, 0.3, 0.35),
                                                          size=4,
                                                          min=0.0,
                                                          max=1.0)
#object mode uv color
    object_draw_uv: bpy.props.FloatVectorProperty(name="UV颜色",
                                                  subtype="COLOR",
                                                  default=(
                                                      1.0, 1.0, 0.0, 1.0),
                                                  size=4,
                                                  min=0.0,
                                                  max=1.0)
    max_verts:bpy.props.IntProperty("顶点限制", default=50000)
    def draw(self,context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        # col.separator()
        col.prop(self, "max_verts", text="顶点限制")
        #view3d colors

        col.prop(self, "selection_verts_3dview",
                 text="顶点颜色")
        col.prop(self, "selection_edges_3dview",
                 text="线框颜色")
        col.prop(self, "selection_faces_3dview",
                 text="面颜色")
        col.prop(self, "object_draw_uv",
                 text="UV颜色")