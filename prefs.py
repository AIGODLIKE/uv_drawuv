import bpy


class DrawUV_Color_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__
#object override
    selection_verts_3dview: bpy.props.FloatVectorProperty(name="selection_verts_3dview",
                                                          subtype="COLOR",
                                                          default=(
                                                              1.0, 0.2, 0.0, 1.0),
                                                          size=4)

    selection_edges_3dview: bpy.props.FloatVectorProperty(name="selection_edges_3dview",
                                                          subtype="COLOR",
                                                          default=(
                                                              1.0, 0.2, 0.0, 1.0),
                                                          size=4)

    selection_faces_3dview: bpy.props.FloatVectorProperty(name="selection_faces_3dview",
                                                          subtype="COLOR",
                                                          default=(
                                                              1.0, 1.0, 0.0, 0.35),
                                                          size=4)
#object mode uv color
    object_draw_uv: bpy.props.FloatVectorProperty(name="object_draw_uv",
                                                  subtype="COLOR",
                                                  default=(
                                                      1.0, 1.0, 0.0, 0.4),
                                                  size=4)
    max_verts:bpy.props.IntProperty("max_verts", default=50000)
    def draw(self,context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        # col.separator()
        col.prop(self, "max_verts", text="Maximum verts")
        #view3d colors

        col.prop(self, "selection_verts_3dview",
                 text="uv verts color in 3dview")
        col.prop(self, "selection_edges_3dview",
                 text="uv edges color in 3dview")
        col.prop(self, "selection_faces_3dview",
                 text="uv faces color in 3dview")
        col.prop(self, "object_draw_uv",
                 text="Object mode UV color")