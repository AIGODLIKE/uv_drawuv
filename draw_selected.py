import bpy
import gpu
from gpu_extras.batch import batch_for_shader
import bmesh

vertex_shader = '''
    uniform mat4 viewProjectionMatrix;
    uniform mat4 wolrdMatrix;
    uniform vec4 color;
    in vec3 pos;
    out vec4 final_col;
    void main()
    {
        vec4 p =viewProjectionMatrix *  wolrdMatrix*vec4(pos, 1.0);
        p.w+=0.00001;
        gl_Position=p;
        final_col=color;
    }
'''

fragment_shader = '''
    in vec4 final_col;
    out vec4 fragColor;

    void main()
    {
        fragColor = final_col;  
    }
'''


def draw_callback_px():
    context = bpy.context
    obj = context.active_object
    # uv_sync=context.scene.tool_settings.use_uv_select_sync

    if (not obj or obj.type != 'MESH' or obj.mode != 'EDIT' or not obj.data.uv_layers) or context.scene.tool_settings.use_uv_select_sync:
        # print('returned')
        return
    # print('not returned')
    try:
        bm = bmesh.from_edit_mesh(obj.data)
    except:
        return
    uv_layer = bm.loops.layers.uv.active
    mode = context.scene.tool_settings.uv_select_mode
    shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
    # shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    #    alpha = 0.6

    selected_verts = []
    if mode == 'VERTEX':

        for v in bm.verts:
            if v.select:
                for loop in v.link_loops:
                    if loop[uv_layer].select:
                        selected_verts.append(v.co)
        # selected_verts = [v.co for v in bm.verts if v.select]
        batch = batch_for_shader(shader, 'POINTS', {"pos": selected_verts})

        # gpu.state.depth_test_set('LESS_EQUAL')
        # shader.bind()
        # shader.uniform_float("color", (1, 0, 0, alpha))
        # batch.draw(shader)
        # gpu.state.depth_test_set('LESS')
    elif mode == 'EDGE':
        for e in bm.edges:
            if e.select:
                for loop in e.link_loops:
                    if loop[uv_layer].select:
                        selected_verts.extend([e.verts[0].co, e.verts[1].co])
        # selected_edges_coords = [coord for e in bm.edges if e.select for coord in (e.verts[0].co, e.verts[1].co)]
        print(selected_verts)
        batch = batch_for_shader(shader, 'LINES', {"pos": selected_verts})
        gpu.state.depth_test_set('LESS_EQUAL')
        #
        # shader.bind()
        # shader.uniform_float("color", (0, 1, 0, alpha))
        # batch.draw(shader)
        # gpu.state.depth_test_set('LESS')
    elif mode == 'FACE' or mode == 'ISLAND':
        # selected_faces = []

        for face in bm.faces:
            if face.select:
                # uv_coords = [loop[uv_layer].uv for loop in face.loops]
                verts = [v.co for v in face.verts]
                if len(face.verts) == 3:
                    if all(loop[uv_layer].select for loop in face.loops):
                        selected_verts.extend(verts)
                elif len(face.verts) == 4:
                    if all(loop[uv_layer].select for loop in face.loops):
                        # selected_faces.extend([uv_coords[0],uv_coords[1],uv_coords[2],uv_coords[0],uv_coords[2],uv_coords[3]])
                        selected_verts.extend(
                            [face.verts[0].co, face.verts[1].co, face.verts[2].co, face.verts[0].co, face.verts[2].co,
                             face.verts[3].co])
                    # print('=44:',selected_faces)
                elif len(face.verts) > 4:
                    # print('verts>4')
                    if all(loop[uv_layer].select for loop in face.loops):
                        # print('verts>4 selected')
                        verts.clear()
                        for i in range(1, len(face.verts) - 1):
                            verts.extend([face.verts[0].co, face.verts[i].co, face.verts[i + 1].co])
                        # print('>4:',verts)

                        selected_verts.extend(verts)

        batch = batch_for_shader(shader, 'TRIS', {"pos": selected_verts})
        gpu.state.blend_set('ALPHA')
    bm.free()

    gpu.state.depth_test_set('LESS_EQUAL')
    view_proj_matrix = bpy.context.region_data.perspective_matrix
    wolrdMatrix = obj.matrix_world
    shader.uniform_float("viewProjectionMatrix", view_proj_matrix)
    shader.uniform_float("wolrdMatrix", wolrdMatrix)
    shader.bind()
    shader.uniform_float("color", (0, 1, 0.3, 0.3))
    batch.draw(shader)
    gpu.state.depth_test_set('LESS')


handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (), 'WINDOW', 'POST_VIEW')
# bpy.types.SpaceView3D.draw_handler_remove(handle, 'WINDOW')
