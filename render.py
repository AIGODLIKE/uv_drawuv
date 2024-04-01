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
        self.selected_verts = {}
        self.selected_edges = {}
        self.selected_faces = {}
    def coords_clear(self):
        self.selected_verts.clear()
        self.selected_edges.clear()
        self.selected_faces.clear()
    def enable(self):
        if self.enabled:
            return
        self.enabled = True

        self.handle_3dview = bpy.types.SpaceView3D.draw_handler_add(self.draw, (), 'WINDOW', 'POST_VIEW')

    def disable(self):
        if not self.enabled:
            return
        self.enabled = False
        bpy.types.SpaceView3D.draw_handler_remove(
            self.handle_3dview, 'WINDOW')

        self.handle_3dview = None

    def draw(self):
        settings = bpy.context.scene.uv_drawuv_switch.draw_selected_in_3dview
        if not settings or bpy.context.scene.tool_settings.use_uv_select_sync or not self.handle_uveditor():
            return

        if self.debug:

            pass

        mode = bpy.context.scene.tool_settings.uv_select_mode
        color = bpy.context.preferences.addons[__package__].preferences
        objs_name = []
        for o in bpy.context.selected_objects:
            if o.type == 'MESH':
                objs_name.append(o.name)
        if mode == "VERTEX":
            self.set_batch(objs_name, color.selection_verts_3dview, 'POINTS', self.selected_verts)
        elif mode == 'EDGE':
            self.set_batch(objs_name, color.selection_edges_3dview, 'LINES', self.selected_edges)
        else:
            self.set_batch(objs_name, color.selection_faces_3dview, 'TRIS', self.selected_faces)

    def set_batch(self, objs_name, color, render_type, coords):
        context = bpy.context
        for name in objs_name:
            if name not in self.selected_verts:
                return
            batch = batch_for_shader(self.shader, f'{render_type}', {"pos": coords[name]})
            self.shader.uniform_float("color", color)
            if render_type == 'TRIS':
                gpu.state.blend_set('ALPHA')
            gpu.state.depth_test_set('LESS_EQUAL')
            self.shader.uniform_float("viewProjectionMatrix", context.region_data.perspective_matrix)
            self.shader.uniform_float("wolrdMatrix", bpy.data.objects[name].matrix_world)
            self.shader.bind()
            batch.draw(self.shader)


class Renderer_UV(Render):
    def __init__(self):
        super(Renderer_UV, self).__init__()

        self.offset = None
        self.zoom = None
        self.obj_uv = None

        self.uv_edited = True
        self.obj_changed = True
        self.enabled = False

        self.shader = shader.uv_gpu_shader()
        self.mvp_matrix = None


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

        return m

    def draw(self):
        settings = bpy.context.scene.uv_drawuv_switch.draw_uv_in_objmode
        if not settings:
            return
        obj = bpy.context.active_object
        if not obj:
            return
        if obj.mode == 'EDIT':
            return

        batch = batch_for_shader(self.shader, 'LINES', {"pos": self.obj_uv})

        self.shader.bind()
        # Only pass in the transformation matrix once; passing it multiple times will cause problems
        if not self.mvp_matrix:
            self.mvp_matrix = self.get_uv_editor_mvp_matrix()
            if not self.mvp_matrix:
                return
            self.shader.uniform_float("ModelViewProjectionMatrix", self.mvp_matrix)
        else:
            pass

        color = bpy.context.preferences.addons[__package__].preferences
        self.shader.uniform_float("color", color.object_draw_uv)

        batch.draw(self.shader)
