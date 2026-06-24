import bpy


class NATURETOOL_PT_main_panel(bpy.types.Panel):
    bl_label = "Nature Tool"
    bl_idname = "NATURETOOL_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Nature"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.nature_tool

        layout.prop(settings, "bush_count")
        layout.prop(settings, "bush_radius")
        layout.prop(settings, "bush_height")
        layout.prop(settings, "random_seed")
        layout.operator("naturetool.create_bush", icon="OUTLINER_OB_META")


classes = (
    NATURETOOL_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
