import time
import bmesh
import bpy
import numpy as np
from bpy.app.handlers import persistent
from . import render
import gpu
class StoredSelections():
    pass


class Updater():
    '''处理更新，优化渲染'''

    def __init__(self):
        self.renderer_3DView = render.Renderer_3DView()
        self.renderer_UV = render.Renderer_UV()
        self.detect_bl_version()
        # 设置绘制颜色
        self.swtich_settings = None
        prefs = bpy.context.preferences.addons[__package__].preferences
        self.max_verts = 50000

        self.last_update = 0
        self.scene_update = False

        self.visible = False
        # self.uv_select_mode = bpy.context.scene.tool_settings.uv_select_mode
        self.uv_select_sync_mode = False
        self.is_update = False
        self.bm_instance = None
        self.obj_name = ''
        # detect mesh changes
        self.vert_select_count = 0
        self.uv_select_count = 0
        # vbo
        self.selected_verts = []
        self.selected_edges = []
        self.selected_faces = []

        self.uv_vertex_selected = np.empty(0)
        self.uv_coords = np.empty(0)
        self.uv_face_selected = np.empty(0)
        self.uv_edge_selected = np.empty(0)
        self.vert_selected = np.empty(0)

    def start(self):
        '''场景发生变化就执行deps handler'''
        # self.__init__()
        # self.renderer_3DView.enable()
        try:
            print('加入dpes handler')
            bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)
        except:
            pass
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_handler)
        # self.renderer_3DView.

    def stop(self):
        self.renderer_3DView.disable()
        pass

    def handle_uveditor(self):
        '''检测是否有uv界面，返回布尔'''
        for area in bpy.context.screen.areas:
            if area.type == "IMAGE_EDITOR" and area.ui_type == "UV":
                self.renderer_3DView.uveditor=True
                return True
        self.renderer_3DView.uveditor=False
        return False

    def detect_bl_version(self):
        if bpy.app.version[0] == 3:
            self.renderer_UV.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        elif bpy.app.version[0] > 3:
            self.renderer_UV.shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    def isEditingUVs(self):
        '''编辑模式为真'''
        context = bpy.context
        obj = context.active_object

        if obj == None or obj.mode != "EDIT":
            return False
        return True

    def update(self):
        if self.renderer_3DView.debug:
            print('update')

        if not self.isEditingUVs() or  bpy.context.scene.tool_settings.use_uv_select_sync or not self.handle_uveditor():
            if self.renderer_3DView.debug:
                print('需要模式：编辑模式')
            # 如果当前不是在UV编辑模式下，它会重置某些变量并退出
            self.renderer_3DView.disable()
            render.tag_redraw_all_views()
            return
        self.swtich_settings = bpy.context.scene.uv_drawuv_switch

        prefs = bpy.context.preferences.addons[__package__].preferences

        obj = bpy.context.active_object
        self.bm_instance=bmesh.from_edit_mesh(obj.data)

        if self.renderer_3DView.debug:
            print('断点2')

        try:

            if len(self.bm_instance.verts) > prefs.max_verts:
                if self.renderer_3DView.debug:
                    print('检测顶点数是否超标')
                return
        except:
            pass

        uv_layer = self.bm_instance.loops.layers.uv.verify()
        if updater.renderer_3DView.debug:

            print('读取uv层')

        verts_selection_changed, uv_selection_changed = self.detect_mesh_changes(self.bm_instance, uv_layer)

        if uv_selection_changed or self.uv_select_mode:  # 或者uv 选择变了
            # self.uv_select_mode定义在init.py post_load_handler
            if self.renderer_3DView.debug:
                print('uv选择变了')
            self.reset()
            # 如果UV选择发生更改，它会收集所有选择的元素。
            # 记录这个过程花了多长时间（尽管实际的时间没有在这段代码中使用）
            self.collect_selected_elements(self.bm_instance, uv_layer)

        try:
            self.bm_instance.free()
        except:
            pass

        self.renderer_3DView.enable()

    def handle_uv_select_mode(self):
        '''uv选择模式变了返回True'''
        if self.uv_select_mode!=bpy.context.scene.tool_settings.uv_select_mode:
            self.uv_select_mode=bpy.context.scene.tool_settings.uv_select_mode
            return True
        return False
    def detect_mesh_changes(self, bm, uv_layer):
        '''
        :param bm_instance:
        :param uv_layer:
        :return:返回2个布尔值，顶点选择状态是否更改、以及UV选择状态是否更改
        '''
        # 如果定点数不同，返回1
        verts_selection_changed = 0
        uv_selection_changed = 0
        # print('检测模型变化')
        verts_selected = sum([v.index for v in bm.verts if v.select])
        if verts_selected != self.vert_select_count:
            self.vert_select_count = verts_selected
            verts_selection_changed = True
            # print('verts_selection_changed', verts_selection_changed)
        # 如果选择顶点数不同，返回1
        uv_count = 0
        for f in bm.faces:
            if f.select:
                for l in f.loops:
                    if l[uv_layer].select:
                        uv_count += l.index
        # 收集uv index 避免选择相同uv数，不同uv顶点
        if self.uv_select_count != uv_count:
            self.uv_select_count = uv_count
            uv_selection_changed = True
            # print('uv_selection_changed', uv_selection_changed)
        # 更新选择uv
        return (verts_selection_changed, uv_selection_changed)

    def collect_selected_elements(self, bm, uv_layer):
        '''这个函数的目标是从bmesh中提取关于选中元素的数据，
        并将这些数据存储在VAO中，以便后续的渲染或其他操作'''
        a = time.time()
        # for face in bm.faces:
        #     if not face.select:
        #         continue
        #     start = face.loops[0]
        #     current = None
        #     face_uvs_selected = True
        #     f_verts = []
        #
        #     while start != current:
        #
        #         if current == None:
        #             current = start
        #         # 遍历uv face的uv顶点坐标
        #         uv = current[uv_layer]
        #         next_uv = current.link_loop_next[uv_layer]
        #         if uv.select:
        #             vert = current.vert.co
        #             # selected_verts.add(v)
        #             self.selected_verts.append(vert.to_tuple())
        #
        #         elif face_uvs_selected:
        #             face_uvs_selected = False
        #         if uv.select and next_uv.select:
        #             self.selected_edges.append(current.edge.verts[0].co.to_tuple())
        #             self.selected_edges.append(current.edge.verts[1].co.to_tuple())
        #         current=current.link_loop_next
        #     if face_uvs_selected and face.select:
        #         verts = [v.co for v in face.verts]
        #         if all(loop[uv_layer].select for loop in face.loops):
        #             if len(verts) == 3:
        #                 self.selected_faces.extend(verts)
        #             elif len(verts) == 4:
        #                 self.selected_faces.extend(
        #                     [face.verts[0].co, face.verts[1].co, face.verts[2].co, face.verts[0].co, face.verts[2].co,
        #                     face.verts[3].co])
        #             else:
        #                 new_verts = []
        #                 for i in range(1, len(verts) - 1):
        #                     new_verts.extend([face.verts[0].co, face.verts[i].co, face.verts[i + 1].co])
        #                 self.selected_faces.extend(new_verts)
        #         # self.selected_faces.add(f.index)

        # mode = bpy.context.scene.tool_settings.uv_select_mode
        # self.renderer_3DView.selected_verts.clear()
        # if mode == 'VERTEX':
        #     # 选择的顶点越少 越快
        #     for v in bm.verts:
        #         if v.select:
        #             for loop in v.link_loops:
        #                 if loop[uv_layer].select:
        #                     self.renderer_3DView.selected_verts.append(v.co)
        # elif mode == 'EDGE':
        #     self.renderer_3DView.selected_edges = [coord for e in bm.edges if e.select for loop in e.link_loops if loop[uv_layer].select
        #                            for coord in (e.verts[0].co, e.verts[1].co)]
        # else:
        #     for face in bm.faces:
        #         if face.select:
        #             verts = [v.co for v in face.verts]
        #             if all(loop[uv_layer].select for loop in face.loops):
        #                 if len(verts) == 3:
        #                     self.renderer_3DView.selected_faces.extend(verts)
        #                 elif len(verts) == 4:
        #                     self.renderer_3DView.selected_faces.extend(
        #                         [face.verts[0].co, face.verts[1].co, face.verts[2].co,
        #                          face.verts[0].co,
        #                          face.verts[2].co, face.verts[3].co])
        #                 else:
        #                     new_verts = []
        #                     for i in range(1, len(verts) - 1):
        #                         new_verts.extend([face.verts[0].co, face.verts[i].co,
        #                                           face.verts[i + 1].co])
        #                     self.renderer_3DView.selected_faces.extend(new_verts)
        # # self.renderer_3DView.selected_verts = np.array(self.selected_verts, dtype=np.float32)
        # # self.renderer_3DView.selected_edges = np.array(self.selected_edges, dtype=np.float32)
        # # self.renderer_3DView.selected_faces = np.array(self.selected_faces, dtype=np.float32)

        # print('render:', time.time() - a)
        # self.selected_verts.clear()
        # self.selected_edges.clear()
        # self.selected_faces.clear()
        # a=time.time()
        mode = bpy.context.scene.tool_settings.uv_select_mode
        if mode == 'VERTEX':
            # 选择的顶点越少 越快
            for v in bm.verts:
                if v.select:
                    for loop in v.link_loops:
                        if loop[uv_layer].select:
                            self.selected_verts.append(v.co.to_tuple())
        elif mode == 'EDGE':
            self.selected_edges = [coord for e in bm.edges if e.select for loop in e.link_loops if loop[uv_layer].select
                                   for coord in [e.verts[0].co.to_tuple(), e.verts[1].co.to_tuple()]]
        else:
            for face in bm.faces:
                if face.select:
                    verts = [v.co for v in face.verts]
                    if all(loop[uv_layer].select for loop in face.loops):
                        if len(verts) == 3:
                            self.selected_faces.extend([verts[0].to_tuple(),verts[1].to_tuple(),verts[2].to_tuple()])
                        elif len(verts) == 4:
                            self.selected_faces.extend(
                                [face.verts[0].co.to_tuple(), face.verts[1].co.to_tuple(), face.verts[2].co.to_tuple(), face.verts[0].co.to_tuple(),
                                 face.verts[2].co.to_tuple(), face.verts[3].co.to_tuple()])
                        else:
                            new_verts = []
                            for i in range(1, len(verts) - 1):
                                new_verts.extend([face.verts[0].co.to_tuple(), face.verts[i].co.to_tuple(), face.verts[i + 1].co.to_tuple()])
                            self.selected_faces.extend(new_verts)
        self.renderer_3DView.selected_verts = np.array(self.selected_verts, dtype=np.float32)
        self.renderer_3DView.selected_edges = np.array(self.selected_edges, dtype=np.float32)
        self.renderer_3DView.selected_faces = np.array(self.selected_faces, dtype=np.float32)
        # print('numpy per:', time.time() - a)
        # self.selected_verts.clear()
        # self.selected_edges.clear()
        # self.selected_faces.clear()
        # a = time.time()
        # for face in bm.faces:
        #     if not face.select:
        #         continue
        #     start = face.loops[0]
        #     current = None
        #     face_uvs_selected = True
        #     f_verts = []
        #
        #     while start != current:
        #
        #         if current == None:
        #             current = start
        #         # 遍历uv face的uv顶点坐标
        #         uv = current[uv_layer]
        #         next_uv = current.link_loop_next[uv_layer]
        #         if uv.select:
        #             vert = current.vert.co
        #             # selected_verts.add(v)
        #             self.selected_verts.append(vert.to_tuple())
        #
        #         elif face_uvs_selected:
        #             face_uvs_selected = False
        #         if uv.select and next_uv.select:
        #             self.selected_edges.append(current.edge.verts[0].co.to_tuple())
        #             self.selected_edges.append(current.edge.verts[1].co.to_tuple())
        #         current = current.link_loop_next
        #     if face_uvs_selected and face.select:
        #         verts = [v.co for v in face.verts]
        #         if all(loop[uv_layer].select for loop in face.loops):
        #             if len(verts) == 3:
        #                 self.selected_faces.extend([verts[0].to_tuple(), verts[1].to_tuple(), verts[2].to_tuple()])
        #             elif len(verts) == 4:
        #                 self.selected_faces.extend(
        #                     [face.verts[0].co.to_tuple(), face.verts[1].co.to_tuple(), face.verts[2].co.to_tuple(),
        #                      face.verts[0].co.to_tuple(),
        #                      face.verts[2].co.to_tuple(), face.verts[3].co.to_tuple()])
        #             else:
        #                 new_verts = []
        #                 for i in range(1, len(verts) - 1):
        #                     new_verts.extend([face.verts[0].co.to_tuple(), face.verts[i].co.to_tuple(),
        #                                       face.verts[i + 1].co.to_tuple()])
        #                 self.selected_faces.extend(new_verts)
        #         # self.selected_faces.add(f.index)
        # self.renderer_3DView.selected_verts = np.array(self.selected_verts, dtype=np.float32)
        # self.renderer_3DView.selected_edges = np.array(self.selected_edges, dtype=np.float32)
        # self.renderer_3DView.selected_faces = np.array(self.selected_faces, dtype=np.float32)
        # print('numpy:', time.time() - a)

    def create_chaches(self, bm, uv_layer):
        pass

    def reset(self):
        self.selected_verts.clear()
        self.selected_edges.clear()
        self.selected_faces.clear()


updater = Updater()


@persistent
def depsgraph_handler(dummy):
    # 设置渲染开关
    # if not updater.handle_uveditor():
    #     render.tag_redraw_all_views()
    #     return
    if not updater.swtich_settings:
        updater.swtich_settings = bpy.context.scene.uv_drawuv_switch
        updater.renderer_UV.switch_settings = updater.swtich_settings
        updater.renderer_3DView.switch_settings = updater.swtich_settings

    # depsgragh = bpy.context.evaluated_depsgraph_get()
    # 通过updates查看更新项目，检查是否能跳过更新
    # for update in depsgragh.updates:
        # print('update:',f"{update.id.name}")
    try:


        delta = (time.perf_counter() - updater.last_update)
        # 每隔0.1s更新一次
        if updater.renderer_3DView.debug:
            print('时间间隔:',delta,updater.scene_update)

        if delta > 0.2 and updater.scene_update:
                if updater.renderer_3DView.debug:
                    print('udpde:更新一次数据处理')
                updater.scene_update = False

                updater.update()
                return

        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj = bpy.context.active_object
        if updater.renderer_3DView.debug:
            print('当前激活物体:',obj)
        if obj is not None:
            for update in depsgraph.updates:
                if updater.renderer_3DView.debug:
                    print('update id:', update.id)
                if update.id.name == obj.name and update.is_updated_geometry:

                    updater.last_update = time.perf_counter()
                    # 场景被更新
                    updater.scene_update = True
                    if updater.renderer_3DView.debug:
                        print('update id :', update.id,',',updater.scene_update)

    except :
        pass
