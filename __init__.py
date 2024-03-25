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
    "name": "draw_uv",
    "category": "UV",
    "author": "AIGODLIKE Community:cupcko",
    "version": (1, 4, 1),
    "blender": (3, 5, 0),
    "location": "ImageEditor > Tool Shelf",
    "description": "This plugin allows for selected UV vertices to be rendered in the 3D view,and enabling the display of object UVs in object mode.",
    "warning": "",
    "doc_url": "",
}


#
@persistent
def pre_load_handler(dummy):
    #
    print('---------------------------------')

    update.updater.stop()
    update.updater.renderer_3DView.coords_clear()


@persistent
def post_load_handler(dummy):
    #

    update.updater.subscribed = False
    update.modal_settings.init = False
    print('---------------------------------')

    update.updater.uv_select_mode = bpy.context.scene.tool_settings.uv_select_mode

    update.updater.start()



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
    '''0.3s refresh deps'''
    obj = bpy.context.active_object

    if not obj:
        return 0.3
    if obj is not None and obj.type == 'MESH':
        if not update.updater.handle_uveditor():
            #如果没有uv编辑器
            #停止渲染,关闭模态
            update.updater.renderer_3DView.disable()
            update.updater.renderer_UV.disable()
            update.Update_Operator.stop()
            tag_redraw_all_views()
            # print('暂停模态')
        if obj.mode == 'OBJECT':
            update.updater.renderer_3DView.disable()
            update.Update_Operator.stop()
            tag_redraw_all_views()
            # print('暂停模态')
        else:
            update.updater.renderer_3DView.enable()
            update.Update_Operator.start()
            # print('启动模态',update.Update_Operator._is_running)
            tag_redraw_all_views()

    update.updater.start_mouse_op()
    #需要检测running 和init
    # a = time.time()
    objs = []
    for o in bpy.context.selected_objects:
        if o.type == 'MESH':
            objs.append(o.name)
    if update.updater.selected_objs != objs:
        update.updater.selected_objs = objs[:]
        objs.clear()

        obj.data['temp_refresh_prop'] = 1
        bpy.ops.wm.properties_remove(data_path="object.data", property_name="temp_refresh_prop")
        # print('delta time',time.time()-a)
    return 0.3


class TranslationHelper():
    def __init__(self, name: str, data: dict, lang='zh_CN'):
        self.name = name
        self.translations_dict = dict()

        for src, src_trans in data.items():
            key = ("Operator", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans
            key = ("*", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans

    def register(self):
        try:
            bpy.app.translations.register(self.name, self.translations_dict)
        except(ValueError):
            pass

    def unregister(self):
        bpy.app.translations.unregister(self.name)


from . import zh_CN

DrawUV_zh_CN = TranslationHelper('DrawUV_zh_CN', zh_CN.data)
DrawUV_zh_HANS = TranslationHelper('DrawUV_zh_HANS', zh_CN.data, lang='zh_HANS')


classes = [

    prefs.DrawUV_Color_Preferences,
    props.DrawUV_Switch_Settings,
    ui.PT_UV_Panel,
    update.Update_Operator,

]


def register():

    if bpy.app.version < (4, 0, 0):
        DrawUV_zh_CN.register()
    else:
        DrawUV_zh_CN.register()
        DrawUV_zh_HANS.register()

    # global previous_mode
    update.previous_mode = None
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.uv_drawuv_switch = bpy.props.PointerProperty(type=props.DrawUV_Switch_Settings)
    if not hasattr(update, "updater"):
        update.updater = update.Updater()
    if not hasattr(update, "modal_settings"):
        update.modal_settings = update.Modal_settings()
    bpy.app.handlers.load_pre.append(pre_load_handler)
    bpy.app.handlers.load_post.append(post_load_handler)

    bpy.app.timers.register(deps_refresh_view, first_interval=0, persistent=True)
    bpy.app.handlers.load_post.append(load_check_uv_changes)
    update.updater.start()
    print('[draw uv]register updater start')


def unregister():

    if bpy.app.version < (4, 0, 0):
        DrawUV_zh_CN.unregister()
    else:
        DrawUV_zh_CN.unregister()
        DrawUV_zh_HANS.unregister()


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
