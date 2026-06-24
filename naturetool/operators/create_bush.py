import bpy

from ..generators.bush import BushBuildSettings, create_bush


class NATURETOOL_OT_create_bush(bpy.types.Operator):
    bl_idname = "naturetool.create_bush"
    bl_label = "Create Bush"
    bl_description = "Create a bush by arranging the selected mesh objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return any(obj.type == "MESH" for obj in context.selected_objects)

    def execute(self, context):
        source_objects = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not source_objects:
            self.report({"ERROR"}, "Select at least one mesh object to use as bush source geometry")
            return {"CANCELLED"}

        settings = context.scene.nature_tool
        build_settings = BushBuildSettings(
            count=settings.bush_count,
            radius=settings.bush_radius,
            height=settings.bush_height,
            seed=settings.random_seed,
        )

        collection = create_bush(context, source_objects, build_settings)
        context.view_layer.active_layer_collection = _find_layer_collection(
            context.view_layer.layer_collection,
            collection,
        ) or context.view_layer.active_layer_collection

        self.report({"INFO"}, f"Created bush with {build_settings.count} instances")
        return {"FINISHED"}


def _find_layer_collection(layer_collection, collection):
    if layer_collection.collection == collection:
        return layer_collection

    for child in layer_collection.children:
        result = _find_layer_collection(child, collection)
        if result:
            return result

    return None


classes = (
    NATURETOOL_OT_create_bush,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
