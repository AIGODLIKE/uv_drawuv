import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix
from . import shader


def tag_redraw_all_views():
    # 更新uv视图
    all_views(lambda region: region.tag_redraw())


def all_views(func):
    # 查找uv视图
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
        self.debug = 0
    def handle_uveditor(self):
        '''检测是否有uv界面，有返回True'''
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "IMAGE_EDITOR" and area.ui_type == "UV":
                    # self.renderer_3DView.uveditor = True
                    # print(f'[draw uv]:update中，检测到有uv视图')
                    return True
        # print(f'[draw uv]:update中，检测到无uv视图')
        # self.renderer_3DView.uveditor = False
        return False

class Renderer_3DView(Render):
    '''
    这个渲染器负责在场景视图中绘制选定的uv, uv边和uv面。
    '''

    def __init__(self):
        super(Renderer_3DView, self).__init__()

        self.shader = shader.view3d_gpu_shader()
        self.enabled = False
        # self.view_proj_matrix = None
        self.selected_verts = []
        self.selected_edges = []
        self.selected_faces = []

    def enable(self):
        if self.enabled:
            return
        self.enabled = True
        '''
        self.draw：这是将被调用的方法 / 函数。用于绘图。
        ()：这是传递给self.draw方法的参数。在这里，它是一个空的元组，意味着self.draw不接受任何额外的参数。
        'WINDOW'：这是绘图的目标类型。在Blender中，它表示整个3D视图窗口。
        'POST_VIEW'：这表示在所有的常规3D视图内容绘制之后，再绘制self.draw。这确保self.draw的内容被绘制在顶部，不会被其他3D内容遮挡'''
        self.handle_3dview = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_VIEW')


    def disable(self):
        if not self.enabled:
            return
        self.enabled = False
        bpy.types.SpaceView3D.draw_handler_remove(
            self.handle_3dview, 'WINDOW')
        print(self.handle_3dview)
        self.handle_3dview = None

    def draw(self):
        settings = bpy.context.scene.uv_drawuv_switch.draw_selected_in_3dview
        if not settings or bpy.context.scene.tool_settings.use_uv_select_sync or not self.handle_uveditor():
            return

        if self.debug:
            # print(len(self.selected_verts))
            pass

        mode = bpy.context.scene.tool_settings.uv_select_mode
        color = bpy.context.preferences.addons[__package__].preferences

        if mode == "VERTEX":

            batch = batch_for_shader(self.shader, 'POINTS', {"pos": self.selected_verts})
            self.shader.uniform_float("color", color.selection_verts_3dview)
        elif mode == 'EDGE':

            batch = batch_for_shader(self.shader, 'LINES', {"pos": self.selected_edges})
            self.shader.uniform_float("color", color.selection_edges_3dview)
        else:

            batch = batch_for_shader(self.shader, 'TRIS', {"pos": self.selected_faces})
            self.shader.uniform_float("color", color.selection_faces_3dview)
            gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS_EQUAL')

        self.shader.uniform_float("viewProjectionMatrix", bpy.context.region_data.perspective_matrix)
        self.shader.uniform_float("wolrdMatrix", bpy.context.active_object.matrix_world)
        self.shader.bind()

        batch.draw(self.shader)




class Renderer_UV(Render):
    def __init__(self):
        super(Renderer_UV, self).__init__()
        # self.obj_num = None
        # self.obj_name = None
        self.offset = None
        self.zoom = None
        self.obj_uv = None
        # self.edit_uv = None
        # uvedited为真，说明进入了编辑模式，可能改变了uv
        self.uv_edited = True
        self.obj_changed = True
        self.enabled = False
        # self.uveditor_space = None
        # self.uveditor_region = None
        # self.shader=self.get_shader()
        self.shader = shader.uv_gpu_shader()
        self.mvp_matrix = None
        # self.adjusted_line_coords = []

    def enable(self):
        if self.enabled:
            return
        self.enabled = True

        self.handle_uv = bpy.types.SpaceImageEditor.draw_handler_add(self.draw, (), 'WINDOW', 'POST_VIEW')

    def disable(self):
        if not self.enabled:
            return
        self.enabled = False
        bpy.types.SpaceImageEditor.draw_handler_remove(
            self.handle_uv, 'WINDOW')
        self.handle_uv = None

    def get_uv_editor_mvp_matrix(self):
        # 寻找图像编辑器区域
        area = next((a for a in bpy.context.screen.areas if a.type == 'IMAGE_EDITOR'), None)
        if not area:
            return None
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'IMAGE_EDITOR':
                    space = area.spaces.active
                    for r in area.regions:
                        if r.type == "WINDOW":
                            uveditor_region = r
                            break

        zoom = space.zoom
        x_offset, y_offset = uveditor_region.view2d.view_to_region(0, 0, clip=False)

        m = Matrix.Identity(4)
        m[0][0] = zoom[0]
        m[1][1] = zoom[1]

        m[0][3] = x_offset
        m[1][3] = y_offset
        # return Matrix(matrix)
        return m

    def draw(self):
        settings = bpy.context.scene.uv_drawuv_switch.draw_uv_in_objmode
        if not settings:
            return
        obj=bpy.context.active_object
        if not obj:
            return
        if obj.mode == 'EDIT':
            return

        batch = batch_for_shader(self.shader, 'LINES', {"pos": self.obj_uv})

        self.shader.bind()
        # 只需要传入一次变换矩阵，多次传入会有问题
        if not self.mvp_matrix:
            self.mvp_matrix = self.get_uv_editor_mvp_matrix()
            if not self.mvp_matrix:
                return
            self.shader.uniform_float("ModelViewProjectionMatrix", self.mvp_matrix)
        else:
            pass
        # print(self.mvp_matrix)
        color = bpy.context.preferences.addons[__package__].preferences
        self.shader.uniform_float("color", color.object_draw_uv)

        batch.draw(self.shader)
