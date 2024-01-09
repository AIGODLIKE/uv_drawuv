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

        self.init = None


modal_settings = Modal_settings()


class Update_Operator(bpy.types.Operator):
    """ Mouse capture, update selected UV vertices while in UV view.
    """
    bl_idname = "uv.uv_mouse_position"
    bl_label = "UV Mouse location"
    bl_options = {"REGISTER", "INTERNAL"}
    last_mouse_move_time = 0.0
    cooldown = 0.2
    _is_running = True
    is_start = False


    @classmethod
    def stop(cls):
        cls._is_running = False

    def modal(self, context, event):

        if not self._is_running:
            return {'FINISHED'}
        if not context.active_object or context.active_object.mode == 'OBJECT' or not updater.handle_uveditor():
            return {'PASS_THROUGH'}
        if event.type == 'MOUSEMOVE':
            current_time = time.time()
            if current_time - self.last_mouse_move_time > self.cooldown:
                self.last_mouse_move_time = current_time

                modal_settings.UV_MOUSE = None

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


                        if (mouse_region_x > 0 and mouse_region_y > 0 and
                                mouse_region_x < region_x + width and
                                mouse_region_y < region_y + height):


                            updater.update()


        return {'PASS_THROUGH'}

    def execute(self, context):
        self.last_mouse_move_time = time.time() - self.cooldown  #
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class Updater():


    def __init__(self):
        self.objs_bm = {}
        self.mul_objs = []
        self.initial_refresh = False
        self.previous_mode = None
        self.renderer_3DView = Renderer_3DView()
        self.renderer_UV = Renderer_UV()

        self.subscribed = False
        self.selected_objs=None
        self.last_update = 0
        self.scene_update = False

        self.uv_select_mode = None

        self.uv_select_count = 0

        self.selected_verts = []
        self.selected_edges = []
        self.selected_faces = []
        self.uv_lines = []

    def start(self):
        '''场景发生变化就执行deps handler'''

        try:

            bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)
        except:
            pass

        updater.initial_refresh = True
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_handler)


    def stop(self):

        self.renderer_3DView.disable()
        self.renderer_UV.disable()
        try:
            bpy.app.handlers.depsgraph_update_post.remove(depsgraph_handler)
        except:
            pass

    def handle_uveditor(self):

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "IMAGE_EDITOR" and area.ui_type == "UV":

                    return True

        return False

    def isEditingUVs(self):

        context = bpy.context
        obj = context.active_object

        if obj == None or obj.mode != "EDIT":
            return False
        return True

    def update(self):
        settings = bpy.context.scene.uv_drawuv_switch

        if not self.handle_uveditor():


            self.renderer_3DView.disable()
            self.renderer_UV.disable()
            tag_redraw_all_views()
            return
        if bpy.context.scene.tool_settings.use_uv_select_sync and self.isEditingUVs():

            self.renderer_3DView.disable()
            tag_redraw_all_views()
            return

        prefs = bpy.context.preferences.addons[__package__].preferences
        if not self.isEditingUVs():

            self.renderer_3DView.disable()
            tag_redraw_all_views()
            if not settings.draw_uv_in_objmode:
                return

            for o in bpy.context.selected_objects:
                if o.type == 'MESH':
                    if len(o.data.vertices) > prefs.max_verts:
                        return

            if self.renderer_UV.uv_edited or self.renderer_UV.obj_changed:

                self.collect_uv_elements()
            self.renderer_UV.enable()

        else:
            self.renderer_UV.disable()
            tag_redraw_all_views()

            if not settings.draw_selected_in_3dview:
                return
            prefs = bpy.context.preferences.addons[__package__].preferences



            self.mul_objs.clear()
            for o in bpy.context.selected_objects:
                if o.type=='MESH':
                    self.mul_objs.append(o.name)

            if self.handle_uv_select_mode():
                for o in self.mul_objs:
                    self.objs_bm[o] = bmesh.from_edit_mesh(bpy.data.objects[o].data)
                    if len(self.objs_bm[o].verts) > prefs.max_verts:

                        return

                    self.reset_3dview()

                    uv_layer = self.objs_bm[o].loops.layers.uv.verify()

                    self.collect_selected_elements(o, self.objs_bm[o], uv_layer)
                    self.objs_bm[o].free()

                return
            uv_selection_changed=None
            for o in self.mul_objs:
                self.objs_bm[o]=bmesh.from_edit_mesh(bpy.data.objects[o].data)

                if len(self.objs_bm[o].verts) > prefs.max_verts:

                    return
                uv_layer = self.objs_bm[o].loops.layers.uv.verify()
                uv_selection_changed = self.detect_mesh_changes(self.objs_bm[o], uv_layer)
                self.objs_bm[o].free()

                if uv_selection_changed:
                    break
            if uv_selection_changed:
                for o in self.mul_objs:
                    self.objs_bm[o] = bmesh.from_edit_mesh(bpy.data.objects[o].data)
                    # print(self.objs_bm[o])
                    if uv_selection_changed or self.handle_uv_select_mode():  # 或者uv 选择变了
                        # self.uv_select_mode defined in init.py post_load_handler

                        self.reset_3dview()

                        uv_layer = self.objs_bm[o].loops.layers.uv.verify()

                        self.collect_selected_elements(o, self.objs_bm[o], uv_layer)

                        self.objs_bm[o].free()

            self.renderer_3DView.enable()
            return

    def handle_uv_select_mode(self):

        if self.uv_select_mode != bpy.context.scene.tool_settings.uv_select_mode:
            self.uv_select_mode = bpy.context.scene.tool_settings.uv_select_mode
            return True
        return False

    def detect_mesh_changes(self, bm, uv_layer):


        uv_selection_changed = 0

        uv_count = 0
        for f in bm.faces:
            if f.select:
                for l in f.loops:
                    if l[uv_layer].select:
                        uv_count += l.index

        if self.uv_select_count != uv_count:
            self.uv_select_count = uv_count
            uv_selection_changed = True
            # print('[draw uv]uv_selection_changed', uv_selection_changed)

        # return (verts_selection_changed, uv_selection_changed)
        return  uv_selection_changed

    def collect_selected_elements(self, name,bm, uv_layer):

        mode = bpy.context.scene.tool_settings.uv_select_mode
        if mode == 'VERTEX':

            for v in bm.verts:
                if v.select:
                    for loop in v.link_loops:
                        if loop[uv_layer].select:
                            self.selected_verts.append(v.co)
        elif mode == 'EDGE':
            verts = bpy.data.objects[name].data.vertices
            verts_num = len(verts)
            if verts_num > 5000:
                # Rough version has low cost, low precision
                self.selected_edges = [
                    v.co.to_tuple()
                    for e in bm.edges if e.select
                    if e.link_loops[0][uv_layer].select
                    for v in e.verts]
            else:
                # The precise version has a higher cost.
                # when the number of vertices is less than 5000
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
                            self.selected_faces.extend([verts[0], verts[1], verts[2]])
                        elif len(verts) == 4:
                            self.selected_faces.extend(
                                [face.verts[0].co, face.verts[1].co, face.verts[2].co,
                                 face.verts[0].co,
                                 face.verts[2].co, face.verts[3].co])
                        else:
                            new_verts = []
                            for i in range(1, len(verts) - 1):
                                new_verts.extend([face.verts[0].co, face.verts[i].co,
                                                  face.verts[i + 1].co])
                            self.selected_faces.extend(new_verts)
        self.renderer_3DView.selected_verts[name] = np.array(self.selected_verts, dtype=np.float32)
        self.renderer_3DView.selected_edges[name] = np.array(self.selected_edges, dtype=np.float32)
        self.renderer_3DView.selected_faces[name] = np.array(self.selected_faces, dtype=np.float32)

    def reset_3dview(self):
        self.selected_verts.clear()
        self.selected_edges.clear()
        self.selected_faces.clear()

    def start_mouse_op(self):

        # print(f'[draw uv]:启动鼠标事件器中...', Update_Operator._is_running)

        if modal_settings.init:

            return
        else:
            modal_settings.init = True
            Update_Operator._is_running=True
            bpy.ops.uv.uv_mouse_position('INVOKE_DEFAULT')




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

        self.renderer_UV.uv_edited = False


updater = Updater()


def switch_obj_callback(context):
    updater.renderer_UV.obj_changed = True
    # global previous_mode

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


        if bpy.context.object.type == 'MESH':

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

    current_mode = bpy.context.object.mode
    if current_mode != updater.previous_mode:

        updater.previous_mode = current_mode
    if bpy.context.active_object.type == 'MESH':
        updater.update()

        updater.renderer_UV.uv_edited = True


@persistent
def depsgraph_handler(dummy):

    if not updater.subscribed:

        switch_obj_msgbus()
        updater.subscribed = True

    try:
        obj = bpy.context.active_object

        if updater.initial_refresh:

            if obj is not None and obj.type == 'MESH' and obj.mode == 'OBJECT':

                updater.update()

                updater.initial_refresh = False

        delta = (time.perf_counter() - updater.last_update)

        if delta > 0.31 and updater.scene_update:

            updater.scene_update = False

            updater.update()
            return

        depsgraph = bpy.context.evaluated_depsgraph_get()


        if obj is not None:
            for update in depsgraph.updates:

                if update.id.name == obj.name and update.is_updated_geometry:
                    updater.last_update = time.perf_counter()

                    updater.scene_update = True


    except:
        pass
