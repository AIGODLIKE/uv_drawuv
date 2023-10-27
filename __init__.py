import time

import bpy
from .render import tag_redraw_all_views
from bpy.app.handlers import persistent
from . import (
    ui,
    props,
    prefs,
    update,
)
bl_info = {
    "name": "uv_drawuv",
    "category": "UV",
    "author": "幻之境_cupcko",
    "description": "Show uv selections in the scene viewm,show uv in object mode",
    "version": (1,0,0),
    "location": "ImageEditor > Tool Shelf",
    "blender": (3, 0, 0),
}
#
@persistent
def pre_load_handler(dummy):
    #载入新文件之前，结束渲染
    print('载入新blend文件,结束渲染')
    update.updater.stop()

@persistent
def post_load_handler(dummy):
    #载入新blend文件，初始化渲染设置
    print('载入新blend文件,初始化渲染设置')
    update.updater.uv_select_mode = bpy.context.scene.tool_settings.uv_select_mode
    update.updater.start()
#

@persistent
def load_check_uv_changes(dummy):
    bpy.app.timers.register(deps_refresh_view)
def deps_refresh_view():
    '''隔0.3s刷新deps'''
    # tag_redraw_all_views()
    # if  update.updater.handle_uveditor():
    # if not bpy.context.scene.tool_settings.use_uv_select_sync:
    obj=bpy.context.active_object
    # if obj is not None and obj.type=='MESH' and obj.mode=='EDIT':
    if obj is not None and obj.type=='MESH':
        # a=time.time()

        # obj.data['redraw_view']=1
        # bpy.ops.wm.properties_remove(data_path="object.data", property_name="redraw_view")
        # print('op',time.time()-a)
        # a=time.time()
        bpy.context.object.data.update()
        # print('updateop',time.time()-a)

        # print('shuaxin deps')
        # redraw_view = obj.vertex_groups.new(name="refresh_view")
        # bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)

    return 0.3
classes = [
    # props.UVHighlightSettings,
    # operators.UV_OT_Timer,
    prefs.DrawUV_Color_Preferences,
    props.DrawUV_Switch_Settings,
    ui.PT_UV_Panel,
    # main.Updater,
]
def register():
    print('register uv drawuv')
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.uv_drawuv_switch=bpy.props.PointerProperty(type=props.DrawUV_Switch_Settings)
    bpy.app.handlers.load_pre.append(pre_load_handler)
    bpy.app.handlers.load_post.append(post_load_handler)

    bpy.app.timers.register(deps_refresh_view)
    bpy.app.handlers.load_post.append(load_check_uv_changes)
    update.updater.start()
def unregister():
    print('unregister uv drawuv')
    update.updater.stop()
    bpy.app.timers.unregister(deps_refresh_view)
    bpy.app.handlers.load_pre.remove(pre_load_handler)
    bpy.app.handlers.load_post.remove(post_load_handler)
    for c in classes:
        bpy.utils.unregister_class(c)
