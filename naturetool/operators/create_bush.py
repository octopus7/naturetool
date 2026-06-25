import bpy

from ..generators.bush import (
    INSTANCE_ROLE,
    VOLUME_ROLE,
    BushBuildSettings,
    create_bush,
    delete_bush,
    is_bush_controller,
    rebuild_bush,
    set_bush_sources,
    set_bush_volume,
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
            top_count=settings.bush_top_count,
            top_density=settings.bush_top_density,
            volume_size=settings.bush_volume_size,
            droop_curvature=settings.bush_droop_curvature,
            seed=settings.random_seed,
        )

        controller, collection = create_bush(context, source_objects, build_settings)
        context.view_layer.active_layer_collection = _find_layer_collection(
            context.view_layer.layer_collection,
            collection,
        ) or context.view_layer.active_layer_collection
        _select_only(context, controller)

        total_count = build_settings.count + build_settings.top_count
        self.report(
            {"INFO"},
            f"Created bush with {total_count} instances ({build_settings.count} body, {build_settings.top_count} top)",
        )
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


class NATURETOOL_OT_set_bush_volume(bpy.types.Operator):
    bl_idname = "naturetool.set_bush_volume"
    bl_label = "Set Volume From Selection"
    bl_description = "Use the selected mesh object as the active bush volume"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            is_bush_controller(context.active_object)
            and _volume_object_from_selection(context) is not None
        )

    def execute(self, context):
        controller = context.active_object
        volume_object = _volume_object_from_selection(context)
        if not volume_object:
            self.report({"ERROR"}, "Select a mesh object along with the active bush controller")
            return {"CANCELLED"}

        try:
            set_bush_volume(context, controller, volume_object)
            rebuild_bush(context, controller)
        except ValueError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Updated bush volume: {volume_object.name}")
        return {"FINISHED"}


class NATURETOOL_OT_delete_bush(bpy.types.Operator):
    bl_idname = "naturetool.delete_bush"
    bl_label = "Delete Bush"
    bl_description = "Delete the selected bush controller and its generated instances"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_bush_controller(context.active_object)

    def execute(self, context):
        controller = context.active_object
        controller_name = controller.name

        try:
            delete_bush(context, controller)
        except ValueError as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}

        self.report({"INFO"}, f"Deleted bush: {controller_name}")
        return {"FINISHED"}


def _is_source_mesh(obj):
    return bool(
        obj
        and obj.type == "MESH"
        and obj.get("naturetool_role") not in {INSTANCE_ROLE, VOLUME_ROLE}
    )


def _volume_object_from_selection(context):
    for obj in context.selected_objects:
        if obj != context.active_object and obj.type == "MESH" and obj.get("naturetool_role") != INSTANCE_ROLE:
            return obj

    return None


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
    NATURETOOL_OT_set_bush_volume,
    NATURETOOL_OT_delete_bush,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
