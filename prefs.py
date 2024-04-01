import bpy


class DrawUV_Color_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
#object override
    selection_verts_3dview: bpy.props.FloatVectorProperty(name="Vertex Color",
                                                          subtype="COLOR",
                                                          default=(
                                                              0.0, 1.0, 0.3, 1.0),
                                                          size=4,
                                                          min=0.0,
                                                          max=1.0)

    selection_edges_3dview: bpy.props.FloatVectorProperty(name="Edge Color",
                                                          subtype="COLOR",
                                                          default=(
                                                              0.0, 1.0, 0.3, 1.0),
                                                          size=4,
                                                          min=0.0,
                                                          max=1.0)

    selection_faces_3dview: bpy.props.FloatVectorProperty(name="Face Color",
                                                          subtype="COLOR",
                                                          default=(
                                                             0.0, 0.341, 0.976, 0.35),
                                                          size=4,
                                                          min=0.0,
                                                          max=1.0)
#object mode uv color
    object_draw_uv: bpy.props.FloatVectorProperty(name="UV Color",
                                                  subtype="COLOR",
                                                  default=(
                                                      0.034, 0.190, 0.328, 0.253),
                                                  size=4,
                                                  min=0.0,
                                                  max=1.0)
    max_verts:bpy.props.IntProperty("Vertex Limit", default=50000)
    def draw(self,context):
        layout = self.layout

        row = layout.row()
        col = row.column()

        col.prop(self, "max_verts", text="Vertex Limit")
        #view3d colors

        col.prop(self, "selection_verts_3dview",
                 text="Vertex Color")
        col.prop(self, "selection_edges_3dview",
                 text="Edge Color")
        col.prop(self, "selection_faces_3dview",
                 text="Face Color")
        col.prop(self, "object_draw_uv",
                 text="UV Color")