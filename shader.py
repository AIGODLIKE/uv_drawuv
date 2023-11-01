import gpu


view3d_vertex_shader = '''
    uniform mat4 viewProjectionMatrix;
    uniform mat4 wolrdMatrix;
    uniform vec4 color;
    in vec3 pos;
    out vec4 final_col;
    void main()
    {
        vec4 p =viewProjectionMatrix *  wolrdMatrix*vec4(pos, 1.0);
        p.w+=0.00003;
        gl_Position=p;
        final_col=color;
    }
 '''


view3d_fragment_shader = '''
    in vec4 final_col;
    out vec4 fragColor;

    void main()
    {
        fragColor = final_col;  
    }
'''
def view3d_gpu_shader():
    return  gpu.types.GPUShader(view3d_vertex_shader,view3d_fragment_shader)
uv_vertex_shader = '''
in vec2 pos;
uniform mat4 ModelViewProjectionMatrix;

void main()
{
    gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
}
'''

uv_fragment_shader = '''
uniform vec4 color;
out vec4 FragColor;

void main()
{
    FragColor = color;
}
'''
def uv_gpu_shader():
    return gpu.types.GPUShader(uv_vertex_shader, uv_fragment_shader)