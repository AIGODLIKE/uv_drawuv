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
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "ImageEditor > Tool Shelf",
    "description": "在物体模式下显示uv，在编辑模式下绘制选择的uv顶点",
    "warning": "",
    "doc_url": "",
}
#
@persistent
def pre_load_handler(dummy):
    #载入新文件之前，结束渲染
    print('---------------------------------')
    print('[draw uv]:载入新blend文件,结束渲染')
    update.updater.stop()

@persistent
def post_load_handler(dummy):

    #载入新blend文件，初始化渲染设置

    update.updater.subscribed=False
    update.modal_settings.init = False
    print('---------------------------------')
    print('[draw uv]:载入新blend文件,初始化渲染设置')
    update.updater.uv_select_mode = bpy.context.scene.tool_settings.uv_select_mode
    print(f'[draw uv]:更新器.start()')
    update.updater.start()
    # bpy.ops.uv.mouse_listen_operator('INVOKE_DEFAULT')
#

@persistent
def load_check_uv_changes(dummy):
    bpy.app.timers.register(deps_refresh_view)
def is_modal_running(operator_idname):
    for op in bpy.context.window_manager.operators:
        if op.name == operator_idname:
            return True
    return False
def deps_refresh_view():
    # print('update deps_refresh_view')
    '''隔0.3s刷新deps'''
    # tag_redraw_all_views()
    # if  update.updater.handle_uveditor():
    # if not bpy.context.scene.tool_settings.use_uv_select_sync:
    obj=bpy.context.active_object

    # if obj is not None and obj.type=='MESH' and obj.mode=='EDIT':
    if obj is not None and obj.type=='MESH' :
        if not update.updater.handle_uveditor():
            update.updater.renderer_3DView.disable()
            tag_redraw_all_views()
            # obj.data.update()
        if obj.mode=='OBJECT':
            update.updater.renderer_3DView.disable()
            tag_redraw_all_views()
            # obj.data.update()
        else:
            update.updater.renderer_3DView.enable()
            tag_redraw_all_views()

    update.updater.start_mouse_op()


    return 0.3




classes = [
    # props.UVHighlightSettings,
    # operators.UV_OT_Timer,
    prefs.DrawUV_Color_Preferences,
    props.DrawUV_Switch_Settings,
    ui.PT_UV_Panel,
    update.Update_Operator,
    # main.Updater,
]
def register():

    print('[draw uv]：注册插件')
    # global previous_mode
    update.previous_mode=None
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.uv_drawuv_switch=bpy.props.PointerProperty(type=props.DrawUV_Switch_Settings)
    if not hasattr(update, "updater"):
        update.updater=update.Updater()
    if not hasattr(update, "modal_settings"):
        update.modal_settings = update.Modal_settings()
    bpy.app.handlers.load_pre.append(pre_load_handler)
    bpy.app.handlers.load_post.append(post_load_handler)
    # update.updater.subscribed = False
    # update.modal_settings.init = False

    # update.updater.start_mouse_op()
    bpy.app.timers.register(deps_refresh_view)
    bpy.app.handlers.load_post.append(load_check_uv_changes)
    update.updater.start()
    print('[draw uv]register updater start')

def unregister():

    # bpy.utils.unregister_class(UVMouseListenOperator)
    print('[draw uv]：取消注册，关闭渲染器')
    update.updater.stop()
    update.Update_Operator.stop()
    del update.updater
    del update.modal_settings
    bpy.msgbus.clear_by_owner("switch_obj_owner")
    bpy.msgbus.clear_by_owner("mode_callback_owner")
    bpy.app.timers.unregister(deps_refresh_view)
    bpy.app.handlers.load_pre.remove(pre_load_handler)
    bpy.app.handlers.load_post.remove(post_load_handler)
    for c in classes:
        bpy.utils.unregister_class(c)
