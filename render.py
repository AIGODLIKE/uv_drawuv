
import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from . import shader

def tag_redraw_all_views():
    #更新uv视图
    all_views(lambda region: region.tag_redraw())


def all_views(func):
    #查找uv视图
    context = bpy.context
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D' or area.type == 'IMAGE_EDITOR':
                    # print('redraw')
                area.tag_redraw()
                for region in area.regions:
                    if region.type == 'WINDOW':
                        func(region)

class Render():
    def __init__(self):
        self.switch_settings = None
        self.prefs_color = None
        self.debug = 0
    def load_prefs_color(self):
        if not self.prefs_color:
            self.prefs_color = bpy.context.preferences.addons[__package__].preferences


class Renderer_3DView(Render):
    '''
    这个渲染器负责在场景视图中绘制选定的uv, uv边和uv面。
    '''

    def __init__(self):
        super(Renderer_3DView, self).__init__()

        self.shader = shader.gpu_shader()
        self.enabled = False
        self.view_proj_matrix=None
        self.selected_verts = None
        self.selected_edges = None
        self.selected_faces = None
        # self.uv_select_mode=bpy.context.scene.tool_settings.uv_select_mode
    def enable(self):
        if self.enabled:
            return
        self.enabled = True
        # self.draw：这是将被调用的方法 / 函数。它应该是这个类的一个方法，用于绘图。
        # ()：这是传递给self.draw方法的参数。在这里，它是一个空的元组，意味着self.draw不接受任何额外的参数。
        # 'WINDOW'：这是绘图的目标类型。在Blender中，它表示整个3D视图窗口。
        # 'POST_VIEW'：这表示在所有的常规3D视图内容绘制之后，再绘制self.draw。这确保self.draw的内容被绘制在顶部，不会被其他3D内容遮挡
        self.handle_3dview = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_VIEW')
        # tag_redraw_all_views()
    def disable(self):
        if not self.enabled:
            return
        self.enabled=False
        bpy.types.SpaceView3D.draw_handler_remove(
            self.handle_3dview, 'WINDOW')
        self.handle_3dview = None
    def draw(self):
        # print('verts',verts)
        # print('edges',edges)
        # print('faces',faces)
        if self.debug:
            print(len(self.selected_verts))
        obj = bpy.context.active_object
        # if obj.mode != 'EDIT' or bpy.context.scene.tool_settings.use_uv_select_sync or not self.uveditor:
        #     return
        if self.switch_settings and not self.switch_settings.draw_selected_in_3dview:
                print('没初始化')
                return

        mode = bpy.context.scene.tool_settings.uv_select_mode

        if mode == "VERTEX":
            # print('render:',self.selected_verts)
            # print(self.selected_verts)
            batch = batch_for_shader(self.shader, 'POINTS', {"pos": self.selected_verts})
        elif mode == 'EDGE':
            # print('e')
            batch = batch_for_shader(self.shader, 'LINES', {"pos": self.selected_edges})
        else:
            # print('f')
            batch = batch_for_shader(self.shader, 'TRIS', {"pos": self.selected_faces})
            gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS_EQUAL')

        # self.view_proj_matrix = bpy.context.region_data.perspective_matrix
        # wolrdMatrix = obj.matrix_world
        self.shader.uniform_float("viewProjectionMatrix", bpy.context.region_data.perspective_matrix)
        self.shader.uniform_float("wolrdMatrix", bpy.context.active_object.matrix_world)
        self.shader.bind()
        self.shader.uniform_float("color", (0, 1, 0.3, 0.3))
        batch.draw(self.shader)
        # tag_redraw_all_views()

# render3d=Renderer_3DView()
class Renderer_UV(Render):
    def __init__(self):
        super(Renderer_UV, self).__init__()
        self.obj_uv=None
        self.edit_uv=None
        self.uveditor_space=None
        self.uveditor_region=None
        pass
    def get_uvscale_offset(self):
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    self.uveditor_space = area.spaces.active
                    for r in area.regions:
                        if r.type == "WINDOW":
                            self.uveditor_region = r
                            break
    def caculate_uv_loc(self,uv_lines,zoom,offset):
        if self.uveditor_space.image:

            image_width, image_height = self.uveditor_space.image.size

            # adjusted_coords = [((Vector(coord) * Vector((image_width,image_height))) * zoom + offset).to_tuple() for coord in uv_coords]
            self.adjusted_line_coords = [((Vector(vert) * Vector((image_width, image_height))) * zoom + offset).to_tuple()
                                    for line in uv_lines for vert in line]

            # print('final coords image',adjusted_coords)
            # print('final lines image',adjusted_line_coords)

        else:
            # adjusted_coords = [((Vector(coord) * 256 ) * zoom + offset).to_tuple() for coord in uv_coords]
            self.adjusted_line_coords = [((Vector(vert) * 256) * zoom + offset).to_tuple() for line in uv_lines for vert in
                                    line]
    def draw(self):
        self.get_uvscale_offset()
        zoom = Vector((self.uveditor_space.zoom[0], self.uveditor_space.zoom[1]))
        offset = Vector((self.uveditor_region.view2d.view_to_region(0, 0, clip=False)))
        obj=bpy.context.active_object

        if obj.type=='MESH':
            if obj.mode=='OBJECT':
                self.caculate_uv_loc(self.obj_uv,zoom,offset)
            else:
                self.caculate_uv_loc(self.edit_uv, zoom, offset)
        batch = batch_for_shader(shader, 'LINES', {"pos": self.adjusted_line_coords})
        # batch = batch_for_shader(shader, 'LINES', {"pos": adjusted_coords})
        shader.bind()
        shader.uniform_float("color", (0.1, 0.5, 0.1, 1.0))
        batch.draw(shader)
