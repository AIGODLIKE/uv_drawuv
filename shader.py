import gpu


vertex_shader = '''
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


fragment_shader = '''
    in vec4 final_col;
    out vec4 fragColor;

    void main()
    {
        fragColor = final_col;  
    }
'''
def gpu_shader():
    return  gpu.types.GPUShader(vertex_shader,fragment_shader)