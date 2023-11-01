import time
import bmesh
import bpy
import numpy as np
from bpy.app.handlers import persistent
from .render import tag_redraw_all_views, Renderer_UV, Renderer_3DView


class Modal_settings():
    def __init__(self):
        pass
        self.mouse_update = False
        # self.translate_active=False
        self.init = None


modal_settings = Modal_settings()


class Update_Operator(bpy.types.Operator):
    """ 鼠标捕捉，在uv视图的时候更新选择的uv顶点
    """
    bl_idname = "uv.uv_mouse_position"
    bl_label = "UV Mouse location"
    bl_options = {"REGISTER", "INTERNAL"}
    last_mouse_move_time = 0.0
    cooldown = 0.2
    _is_running = True
    is_start = False

    # @classmethod
    # def is_runing(cls):
    #     return cls._is_running
    #
    @classmethod
    def stop(cls):
        cls._is_running = False

    def modal(self, context, event):
        # if self.is_start:
        # print('模态中',self.is_start)
        if not self._is_running:
            return {'FINISHED'}
        if not context.active_object or context.active_object.mode == 'OBJECT' or not updater.handle_uveditor():
            return {'PASS_THROUGH'}
        if event.type == 'MOUSEMOVE':
            current_time = time.time()
            if current_time - self.last_mouse_move_time > self.cooldown:
                self.last_mouse_move_time = current_time
                # 在这里处理鼠标移动事件
                # 更新视图或执行其他操作
                modal_settings.UV_MOUSE = None
                '''如果检测到鼠标移动事件，它将清空main.UV_MOUSE'''
                for area in context.screen.areas:
                    if area.type == "IMAGE_EDITOR":
                        for region in area.regions:
                            if region.type == "WINDOW":
                                width = region.width
                                height = region.height
                                region_x = region.x
                                region_y = region.y
                        mouse_region_x = event.mouse_x - region_x
                        mouse_region_y = event.mouse_y - region_y
                        '''定义region_to_view和UV_TO_VIEW变量来进行区域和视图之间的转换。'''

                        if (mouse_region_x > 0 and mouse_region_y > 0 and
                                mouse_region_x < region_x + width and
                                mouse_region_y < region_y + height):

                            # if updater.renderer_3DView.debug:
                            print('[draw uv]:模态：刷新一次uv顶点')
                            updater.update()
                            # try:
                            #     bpy.context.active_object.data.update()
                            # except:
                            #     print('[draw uv]非mesh物体不可更新')

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.last_mouse_move_time = time.time() - self.cooldown  # 设置初始值
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class Updater():
    '''处理更新，优化渲染'''

    def __init__(self):
        self.initial_refresh = False
        self.previous_mode = None
        self.renderer_3DView = Renderer_3DView()
        self.renderer_UV = Renderer_UV()
        # 设置绘制颜色
        self.subscribed = False

        self.last_update = 0
        self.scene_update = False

        self.uv_select_mode = None
        self.bm_instance = None

        # detect mesh changes
        self.vert_select_count = 0
        self.uv_select_count = 0
        # vbo
        self.selected_verts = []
        self.selected_edges = []
        self.selected_faces = []
        self.uv_lines = []

    def start(self):
        '''场景发生变化就执行deps handler'''

        try:
            # if updater.renderer_3DView.debug:
            print('[draw uv]:清除可能残余的handler')
            bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)
        except:
            pass
        # if updater.renderer_3DView.debug:
        print(f'[draw uv]:载入新的handler')
        updater.initial_refresh = True
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_handler)
        # self.renderer_3DView.

    def stop(self):
        if updater.renderer_3DView.debug:
            print(f'[draw uv]:关闭渲染器')
        self.renderer_3DView.disable()
        self.renderer_UV.disable()
        try:
            bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)
        except:
            pass

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

    def isEditingUVs(self):
        '''编辑模式为真'''
        context = bpy.context
        obj = context.active_object

        if obj == None or obj.mode != "EDIT":
            return False
        return True

    def update(self):

        if self.renderer_3DView.debug:
            print('[draw uv]update')
        if not self.handle_uveditor():
            # 没有uv界面不渲染 uv同步模式不渲染
            if self.renderer_3DView.debug:
                print('[draw uv]需要界面：uv')
            self.renderer_3DView.disable()
            self.renderer_UV.disable()
            tag_redraw_all_views()
            return

        if bpy.context.scene.tool_settings.use_uv_select_sync and self.isEditingUVs():
            if self.renderer_3DView.debug:
                print('[draw uv]需要禁用uv同步')
            self.renderer_3DView.disable()

            tag_redraw_all_views()
            return

        prefs = bpy.context.preferences.addons[__package__].preferences
        if not self.isEditingUVs():
            # 处理uv视图绘制
            if self.renderer_3DView.debug:
                print('[draw uv]需要模式：编辑模式')
                print(f'[draw uv]self.renderer_UV.uv_edited：{self.renderer_UV.uv_edited}')
                print(f'[draw uv]obj_changed：{self.renderer_UV.obj_changed}')
            # 如果当前不是在UV编辑模式下，它会重置某些变量并退出
            self.renderer_3DView.disable()
            tag_redraw_all_views()
            # 检测顶点数
            for o in bpy.context.selected_objects:
                if o.type == 'MESH':
                    if len(o.data.vertices) > prefs.max_verts:
                        return

            if self.renderer_UV.uv_edited or self.renderer_UV.obj_changed:
                print(
                    f'[draw uv]如果uv_edited,obj_changed,{self.renderer_UV.uv_edited}{self.renderer_UV.obj_changed}更新uv')
                self.collect_uv_elements()
            self.renderer_UV.enable()
            # if  bpy.context.active_object is not None and bpy.context.active_object.type=='MESH':
            #     bpy.context.active_object.data.update()
        else:
            self.renderer_UV.disable()
            tag_redraw_all_views()
            # 开始处理3d视图绘制

            prefs = bpy.context.preferences.addons[__package__].preferences

            obj = bpy.context.active_object
            self.bm_instance = bmesh.from_edit_mesh(obj.data)

            if self.renderer_3DView.debug:
                print('[draw uv]断点2')

            try:

                if len(self.bm_instance.verts) > prefs.max_verts:
                    if self.renderer_3DView.debug:
                        print('[draw uv]检测顶点数是否超标')
                    return
            except:
                pass

            uv_layer = self.bm_instance.loops.layers.uv.verify()
            if updater.renderer_3DView.debug:
                print('[draw uv]读取uv层')

            verts_selection_changed, uv_selection_changed = self.detect_mesh_changes(self.bm_instance, uv_layer)

            if uv_selection_changed or self.handle_uv_select_mode():  # 或者uv 选择变了
                # self.uv_select_mode定义在init.py post_load_handler
                if self.renderer_3DView.debug:
                    print('[draw uv]uv选择变了')
                self.reset_3dview()
                # 如果UV选择发生更改，它会收集所有选择的元素。
                # 记录这个过程花了多长时间（尽管实际的时间没有在这段代码中使用）
                self.collect_selected_elements(self.bm_instance, uv_layer)

            try:
                self.bm_instance.free()
            except:
                pass

            self.renderer_3DView.enable()
            return

    def handle_uv_select_mode(self):
        '''uv选择模式变了返回True'''
        if self.uv_select_mode != bpy.context.scene.tool_settings.uv_select_mode:
            self.uv_select_mode = bpy.context.scene.tool_settings.uv_select_mode
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
        # print('[draw uv]检测模型变化')
        verts_selected = sum([v.index for v in bm.verts if v.select])
        if verts_selected != self.vert_select_count:
            self.vert_select_count = verts_selected
            verts_selection_changed = True
            # print('[draw uv]verts_selection_changed', verts_selection_changed)
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
            # print('[draw uv]uv_selection_changed', uv_selection_changed)
        # 更新选择uv
        return (verts_selection_changed, uv_selection_changed)

    def collect_selected_elements(self, bm, uv_layer):
        '''这个函数的目标是从bmesh中提取关于选中元素的数据，
        并将这些数据存储在VAO中，以便后续的渲染或其他操作'''
        mode = bpy.context.scene.tool_settings.uv_select_mode
        if mode == 'VERTEX':
            # 选择的顶点越少 越快
            for v in bm.verts:
                if v.select:
                    for loop in v.link_loops:
                        if loop[uv_layer].select:
                            self.selected_verts.append(v.co.to_tuple())
        elif mode == 'EDGE':
            verts = bpy.context.active_object.data.vertices
            verts_num = len(verts)
            if verts_num > 5000:
                # 粗糙版开销小，精度低
                self.selected_edges = [
                    v.co.to_tuple()  # 获取UV坐标而不是顶点坐标
                    for e in bm.edges if e.select
                    if e.link_loops[0][uv_layer].select
                    for v in e.verts]
            else:
                # 精确版开销比较大
                # 顶点小于5000时用精确版
                selected_uv_edges = set()
                for face in bm.faces:
                    for loop in face.loops:
                        next_loop = loop.link_loop_next
                        if loop[uv_layer].select and next_loop[uv_layer].select:
                            edge_key = tuple(sorted([loop.vert.index, next_loop.vert.index]))
                            selected_uv_edges.add(edge_key)
                for edge_key in selected_uv_edges:
                    self.selected_edges.extend([verts[i].co for i in edge_key])

        else:
            for face in bm.faces:
                if face.select:
                    verts = [v.co for v in face.verts]
                    if all(loop[uv_layer].select for loop in face.loops):
                        if len(verts) == 3:
                            self.selected_faces.extend([verts[0].to_tuple(), verts[1].to_tuple(), verts[2].to_tuple()])
                        elif len(verts) == 4:
                            self.selected_faces.extend(
                                [face.verts[0].co.to_tuple(), face.verts[1].co.to_tuple(), face.verts[2].co.to_tuple(),
                                 face.verts[0].co.to_tuple(),
                                 face.verts[2].co.to_tuple(), face.verts[3].co.to_tuple()])
                        else:
                            new_verts = []
                            for i in range(1, len(verts) - 1):
                                new_verts.extend([face.verts[0].co.to_tuple(), face.verts[i].co.to_tuple(),
                                                  face.verts[i + 1].co.to_tuple()])
                            self.selected_faces.extend(new_verts)
        self.renderer_3DView.selected_verts = np.array(self.selected_verts, dtype=np.float32)
        self.renderer_3DView.selected_edges = np.array(self.selected_edges, dtype=np.float32)
        self.renderer_3DView.selected_faces = np.array(self.selected_faces, dtype=np.float32)

    def reset_3dview(self):
        self.selected_verts.clear()
        self.selected_edges.clear()
        self.selected_faces.clear()

    def start_mouse_op(self):
        # if not Update_Operator.is_start:
        #     bpy.ops.uv.uv_mouse_position('INVOKE_DEFAULT')
        #     print('启动模态鼠标')
        #     Update_Operator.is_start=True
        #     return
        print(f'[draw uv]:启动鼠标事件器中...', Update_Operator._is_running)
        if updater.renderer_3DView.debug:
            print(f'[draw uv]:读取初始化[模态初始化] {modal_settings.init}  [模态启动]{modal_settings.mouse_update}')
        if modal_settings.init:
            if updater.renderer_3DView.debug:
                print(f'[draw uv]:[模态初始化]{modal_settings.init},跳过')
            return
        else:
            modal_settings.init = True
            Update_Operator._is_running=True
            bpy.ops.uv.uv_mouse_position('INVOKE_DEFAULT')
            print('启动鼠标事件器')
        # if not modal_settings.mouse_update:
        #     area = next((a for a in bpy.context.screen.areas if a.type == 'IMAGE_EDITOR' or a.type=='VIEW_3D'), None)
        #     if area:
        #         with bpy.context.temp_override(area=area):
        #             bpy.ops.uv.uv_mouse_position('INVOKE_DEFAULT')
        #             if updater.renderer_3DView.debug:
        #                 print('[draw uv]:启动鼠标modal')
        #
        #                 print(f'[draw uv]:启动成功...')
        #     else:
        #         print('[draw uv]:请打开3d视图或者uv视图')
        #         print('[draw uv]:启动鼠标事件器失败...')
            # for window in bpy.context.window_manager.windows:
            #     for area in window.screen.areas:
            #         if area.type == 'VIEW_3D' or area.type == 'IMAGE_EDITOR':
            #             # try:
            #             with bpy.context.temp_override(area=area):
            #
            #                 bpy.ops.uv.uv_mouse_position('INVOKE_DEFAULT')
            #                 if updater.renderer_3DView.debug:
            #                         print('[draw uv]:启动鼠标modal')
            #                 break
            #             # except:
            #             #     print('[draw uv]:请打开3d视图或者uv视图')
            #             #     return



    def collect_uv_elements(self):

        objs = bpy.context.selected_objects

        a = time.time()
        for obj in objs:
            if obj.type != 'MESH':
                continue

            uv_layers = obj.data.uv_layers
            if not uv_layers.active:
                continue

            uv_data_np = np.zeros(len(uv_layers.active.data) * 2)
            uv_layers.active.data.foreach_get("uv", uv_data_np)

            for poly in obj.data.polygons:
                loop_indices = poly.loop_indices
                loop_len = len(loop_indices)
                for i in range(loop_len):
                    start_index = loop_indices[i]
                    end_index = loop_indices[(i + 1) % loop_len]
                    start_uv = uv_data_np[2 * start_index:2 * start_index + 2]
                    end_uv = uv_data_np[2 * end_index:2 * end_index + 2]
                    self.uv_lines.extend([start_uv, end_uv])
        #
        #
        self.renderer_UV.obj_uv = np.array(self.uv_lines, dtype=np.float32)

        self.uv_lines.clear()
        # print('new', time.time() - a)
        self.renderer_UV.uv_edited = False


updater = Updater()


def switch_obj_callback(context):
    updater.renderer_UV.obj_changed = True
    # global previous_mode
    # 在每次活动对象更改时，重新设置模式的订阅
    bpy.msgbus.clear_by_owner("mode_callback_owner")
    if bpy.context.object:
        rna_path = bpy.context.object.path_resolve("mode", False)
        bpy.msgbus.subscribe_rna(
            key=rna_path,
            owner="mode_callback_owner",
            args=(),
            notify=toggle_mode_callback,
            options={"PERSISTENT"}
        )

        print('[draw uv]当前激活物体:', bpy.context.object.name)
        if bpy.context.object.type == 'MESH':
            print('[draw uv]切换物体，刷新uv:', )
            updater.update()
            updater.obj_changed = False
    else:
        print('[draw uv]当前没有激活物体')
    updater.previous_mode = bpy.context.object.mode if bpy.context.object else None


def switch_obj_msgbus():
    subscribe_to_switch_obj_msgbus = bpy.types.LayerObjects, "active"
    bpy.msgbus.subscribe_rna(
        key=subscribe_to_switch_obj_msgbus,
        owner='switch_obj_owner',
        args=(bpy.context,),
        notify=switch_obj_callback,
        options={"PERSISTENT"}
    )


def toggle_mode_callback():
    # print('切换模式')
    # global previous_mode
    current_mode = bpy.context.object.mode
    if current_mode != updater.previous_mode:
        print("[draw uv]:切换模式 {current_mode}")
        updater.previous_mode = current_mode
    if bpy.context.active_object.type == 'MESH':
        updater.update()

        updater.renderer_UV.uv_edited = True


@persistent
def depsgraph_handler(dummy):
    print('[draw uv]进入视图刷新句柄handler')
    if not updater.subscribed:
        # 设置渲染开关
        switch_obj_msgbus()
        updater.subscribed = True

    # updater.start_mouse_op()
    # print('[draw uv]‘，updater.initial_refresh)
    try:
        obj = bpy.context.active_object
        # 载入后刚开始需要 计算delta，所以首次要强制刷新下
        if updater.initial_refresh:

            if obj is not None and obj.type == 'MESH' and obj.mode == 'OBJECT':
                print(f'[draw uv]:首次更新')
                updater.update()
                # obj.data.update()
                updater.initial_refresh = False

        delta = (time.perf_counter() - updater.last_update)

        if delta > 3.1 / 10.0 and updater.scene_update:
            if updater.renderer_3DView.debug:
                print(f'[draw uv]:{delta} 更新一次数据处理')
            updater.scene_update = False

            updater.update()
            return

        depsgraph = bpy.context.evaluated_depsgraph_get()

        # if updater.renderer_3DView.debug:
        #     print('[draw uv]当前激活物体:',obj)
        if obj is not None:
            for update in depsgraph.updates:
                # if updater.renderer_3DView.debug:
                # print('[draw uv]update id:', update.id)
                if update.id.name == obj.name and update.is_updated_geometry:
                    updater.last_update = time.perf_counter()
                    # 场景被更新
                    updater.scene_update = True

            if updater.renderer_3DView.debug:
                print('[draw uv]:记录一次时间戳')
    except:
        pass
