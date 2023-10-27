import bpy
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
import time
import numpy as np
import sys
obj_uv_edges={}
uv_data={}
uv_space = None
region = None
#版本判断
if bpy.app.version[0]==3:
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
elif bpy.app.version[0]>3:
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
# 获取UV编辑器的space_data和region_2d
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            uv_space = area.spaces.active
            for r in area.regions:
                if r.type == "WINDOW":
                    region = r
                    break
            if uv_space and region:
                break

def draw_normal():
    '''
    物体模式时，缓存uv坐标
    编辑模式时，订阅uv层数据是否被修改
    '''
    global uv_space, region, shader
    obj = bpy.context.active_object

    # 检查物体和UV数据的存在性
    if not obj or obj.type != 'MESH' or not obj.data.uv_layers:
        return
    normal1=time.time()
    # 获取UV坐标
    # if obj.mode == 'EDIT':
    #     bm = bmesh.from_edit_mesh(obj.data)
    #     uv_layer = bm.loops.layers.uv.active
    #     if uv_layer.name in uv_data and sys.getsizeof(uv_data[uv_layer.name]) ==sys.getsizeof(uv_layer):
    #         print('uv无变化')
    #     else:
    #         uv_data[uv_layer.name]=uv_layer
    #         print('uv变化')
    #     # if not uv_layer:
    #     #     return
    #     # uv_coords = [(loop[uv_layer].uv.x, loop[uv_layer].uv.y) for face in bm.faces for loop in face.loops]
    #     # print('edit uvcoord',uv_coords)
    #     uv_lines = []
    #     for face in bm.faces:
    #         for loop in face.loops:
    #             start_uv = loop[uv_layer].uv
    #             end_uv = loop.link_loop_next[uv_layer].uv
    #             uv_lines.append((start_uv, end_uv))
    #     # print('edit lines',uv_lines)
    #
    #     bm.free()
    #     obj_uv_edges.clear()
    if obj.mode == 'OBJECT':
        uv_layer = obj.data.uv_layers.active.data
        # uv_coords = [coord.uv for poly in obj.data.polygons for loop_index in poly.loop_indices for coord in
        #              [uv_layer[loop_index]]]
        # print('obj uvcoord',uv_coords)
        uv_lines = []
        if obj.name in obj_uv_edges:
            uv_lines=obj_uv_edges[obj.name]
        else:
            for poly in obj.data.polygons:
                for i in range(len(poly.loop_indices)):
                    start_loop_index = poly.loop_indices[i]
                    end_loop_index = poly.loop_indices[(i + 1) % len(poly.loop_indices)]
                    uv_lines.append((uv_layer[start_loop_index].uv,uv_layer[end_loop_index].uv))
        obj_uv_edges[obj.name]=uv_lines
        # print('obj lines',uv_lines)
    # 根据UV编辑器的缩放和偏移调整UV坐标
    zoom = Vector((uv_space.zoom[0], uv_space.zoom[1]))
    offset = Vector((region.view2d.view_to_region(0, 0, clip=False)))

    if uv_space.image:

        image_width, image_height = uv_space.image.size

        # adjusted_coords = [((Vector(coord) * Vector((image_width,image_height))) * zoom + offset).to_tuple() for coord in uv_coords]
        adjusted_line_coords = [((Vector(vert) * Vector((image_width,image_height))) * zoom + offset).to_tuple() for line in uv_lines for vert in line]

        # print('final coords image',adjusted_coords)
        # print('final lines image',adjusted_line_coords)

    else:
        # adjusted_coords = [((Vector(coord) * 256 ) * zoom + offset).to_tuple() for coord in uv_coords]
        adjusted_line_coords = [((Vector(vert) * 256 ) * zoom + offset).to_tuple() for line in uv_lines for vert in line]

        # print('final coords ',adjusted_coords)
        # print('final lines ',adjusted_line_coords)
    normal2=time.time()
    print('normal',normal2-normal1)

    batch = batch_for_shader(shader, 'LINES', {"pos": adjusted_line_coords})
    # batch = batch_for_shader(shader, 'LINES', {"pos": adjusted_coords})
    shader.bind()
    shader.uniform_float("color", (0.1, 0.5, 0.1, 1.0))
    batch.draw(shader)



def draw_uv_callback():
    global uv_space, region, shader
    obj = bpy.context.active_object

    # 检查物体和UV数据的存在性
    if not obj or obj.type != 'MESH' or not obj.data.uv_layers:
        return

    normal1 = time.time()

    uv_lines = []

    # 获取 UV 坐标
    # if obj.mode == 'EDIT':
    #     bm = bmesh.from_edit_mesh(obj.data)
    #     uv_layer = bm.loops.layers.uv.active
    #
    #     if uv_layer:
    #         uv_data_np = np.zeros(len(bm.loops) * 2)
    #         uv_layer.data.foreach_get("uv", uv_data_np)
    #
    #         for face in bm.faces:
    #             for loop in face.loops:
    #                 start_index = loop.index
    #                 end_index = loop.link_loop_next.index
    #                 start_uv = uv_data_np[2*start_index:2*start_index+2]
    #                 end_uv = uv_data_np[2*end_index:2*end_index+2]
    #                 uv_lines.append((start_uv, end_uv))
    #         bm.free()
    #     else:
    #         return
    #
    if obj.mode == 'OBJECT':
        if obj.name in obj_uv_edges:
            uv_lines = obj_uv_edges[obj.name]
        else:
            uv_data_np = np.zeros(len(obj.data.uv_layers.active.data) * 2)
            obj.data.uv_layers.active.data.foreach_get("uv", uv_data_np)

            for poly in obj.data.polygons:
                for i in range(len(poly.loop_indices)):
                    start_index = poly.loop_indices[i]
                    end_index = poly.loop_indices[(i + 1) % len(poly.loop_indices)]
                    start_uv = uv_data_np[2*start_index:2*start_index+2]
                    end_uv = uv_data_np[2*end_index:2*end_index+2]
                    uv_lines.append((start_uv, end_uv))
            obj_uv_edges[obj.name] = uv_lines

    # 根据 UV 编辑器的缩放和偏移调整 UV 坐标
    zoom = Vector((uv_space.zoom[0], uv_space.zoom[1]))
    offset = Vector((region.view2d.view_to_region(0, 0, clip=False)))

    if uv_space.image:
        image_width, image_height = uv_space.image.size
        adjusted_line_coords = [((Vector(vert) * Vector((image_width, image_height))) * zoom + offset).to_tuple() for line in uv_lines for vert in line]
    else:
        adjusted_line_coords = [((Vector(vert) * 256) * zoom + offset).to_tuple() for line in uv_lines for vert in line]

    batch = batch_for_shader(shader, 'LINES', {"pos": adjusted_line_coords})
    shader.bind()
    shader.uniform_float("color", (0.1, 0.5, 0.1, 1.0))
    batch.draw(shader)

    normal2 = time.time()
    print('normal22', normal2 - normal1)



handle = bpy.types.SpaceImageEditor.draw_handler_add(draw_uv_callback, (), 'WINDOW', 'POST_PIXEL')
handle = bpy.types.SpaceImageEditor.draw_handler_add(draw_normal, (), 'WINDOW', 'POST_PIXEL')


# 定义回调函数
def notify_test(context):
    if context.object:
        print("Active object changed to:", context.object.name)
        if context.object.type == 'MESH':
            bpy.context.object.data.update()
    else:
        print("No active object")


# 设置msgbus订阅
subscribe_to = bpy.types.LayerObjects, "active"
bpy.msgbus.subscribe_rna(
    key=subscribe_to,
    owner=bpy.context.window,
    args=(bpy.context,),
    notify=notify_test,
    options={"PERSISTENT"}
)