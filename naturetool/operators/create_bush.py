import bpy

from ..generators.bush import (
    INSTANCE_ROLE,
    BushBuildSettings,
    create_bush,
    is_bush_controller,
    rebuild_bush,
    set_bush_sources,
)


class NATURETOOL_OT_create_bush(bpy.types.Operator):
    bl_idname = "naturetool.create_bush"
    bl_label = "Create Bush"
    bl_description = "Create a bush by arranging the selected mesh objects"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return any(_is_source_mesh(obj) for obj in context.selected_objects)

    def execute(self, context):
        source_objects = _source_objects_from_selection(context)
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

        controller, collection = create_bush(context, source_objects, build_settings)
        context.view_layer.active_layer_collection = _find_layer_collection(
            context.view_layer.layer_collection,
            collection,
        ) or context.view_layer.active_layer_collection
        _select_only(context, controller)

        self.report({"INFO"}, f"Created bush with {build_settings.count} instances")
        return {"FINISHED"}


class NATURETOOL_OT_update_bush(bpy.types.Operator):
    bl_idname = "naturetool.update_bush"
    bl_label = "Update Bush"
    bl_description = "Rebuild the selected bush controller using its current settings"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_bush_controller(context.active_object)

    def execute(self, context):
        controller = context.active_object
        try:
            rebuild_bush(context, controller)
        except ValueError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        self.report({"INFO"}, "Updated bush")
        return {"FINISHED"}


class NATURETOOL_OT_set_bush_sources(bpy.types.Operator):
    bl_idname = "naturetool.set_bush_sources"
    bl_label = "Set Sources From Selection"
    bl_description = "Use the selected mesh objects as sources for the active bush controller"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            is_bush_controller(context.active_object)
            and any(_is_source_mesh(obj) for obj in context.selected_objects)
        )

    def execute(self, context):
        controller = context.active_object
        source_objects = [
            obj
            for obj in _source_objects_from_selection(context)
            if obj != controller
        ]

        if not source_objects:
            self.report({"ERROR"}, "Select at least one mesh source along with the bush controller")
            return {"CANCELLED"}

        set_bush_sources(controller, source_objects)
        try:
            rebuild_bush(context, controller)
        except ValueError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Updated bush sources: {len(source_objects)}")
        return {"FINISHED"}


def _is_source_mesh(obj):
    return bool(
        obj
        and obj.type == "MESH"
        and obj.get("naturetool_role") != INSTANCE_ROLE
    )


def _source_objects_from_selection(context):
    return [
        obj
        for obj in context.selected_objects
        if _is_source_mesh(obj)
    ]


def _select_only(context, obj):
    for selected in context.selected_objects:
        selected.select_set(False)

    obj.select_set(True)
    context.view_layer.objects.active = obj


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
    NATURETOOL_OT_update_bush,
    NATURETOOL_OT_set_bush_sources,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
