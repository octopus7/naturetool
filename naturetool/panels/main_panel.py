import bpy

from ..generators.bush import is_bush_controller


class NATURETOOL_PT_main_panel(bpy.types.Panel):
    bl_label = "Nature Tool"
    bl_idname = "NATURETOOL_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Nature"

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object

        if is_bush_controller(active_object):
            _draw_bush_editor(layout, active_object)
            return

        settings = context.scene.nature_tool

        layout.prop(settings, "bush_count")
        layout.prop(settings, "bush_top_count")
        layout.prop(settings, "bush_top_density")
        layout.prop(settings, "bush_volume_size")
        layout.prop(settings, "bush_droop_curvature")
        layout.prop(settings, "random_seed")
        layout.operator("naturetool.create_bush")


def _draw_bush_editor(layout, controller):
    bush = controller.nature_bush

    layout.prop(bush, "count")
    layout.prop(bush, "top_count")
    layout.prop(bush, "top_density")
    layout.prop(bush, "volume_object")
    layout.operator("naturetool.set_bush_volume")
    layout.prop(bush, "volume_size")
    layout.prop(bush, "droop_curvature")
    layout.prop(bush, "seed")
    layout.prop(bush, "auto_update")

    row = layout.row(align=True)
    row.operator("naturetool.update_bush")
    row.operator("naturetool.set_bush_sources")
    layout.operator("naturetool.delete_bush", icon="TRASH")

    valid_sources = [
        item.object
        for item in bush.sources
        if item.object and item.object.type == "MESH"
    ]

    box = layout.box()
    box.label(text=f"Sources: {len(valid_sources)}")
    for source in valid_sources[:6]:
        box.label(text=source.name, icon="MESH_DATA")

    if len(valid_sources) > 6:
        box.label(text=f"+ {len(valid_sources) - 6} more")


classes = (
    NATURETOOL_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
