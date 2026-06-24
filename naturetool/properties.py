import bpy


def _refresh_bush_on_update(self, context):
    if not self.is_controller or not self.auto_update:
        return

    controller = self.id_data
    if not controller:
        return

    from .generators.bush import rebuild_bush

    rebuild_bush(context, controller)


class NatureToolSourceObject(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(
        name="Source Object",
        type=bpy.types.Object,
    )


class NatureToolBushSettings(bpy.types.PropertyGroup):
    is_controller: bpy.props.BoolProperty(
        name="Is Bush Controller",
        default=False,
        options={"HIDDEN"},
    )
    collection_name: bpy.props.StringProperty(
        name="Collection",
        options={"HIDDEN"},
    )
    count: bpy.props.IntProperty(
        name="Instances",
        description="Number of mesh instances in this bush",
        default=24,
        min=1,
        max=500,
        update=_refresh_bush_on_update,
    )
    radius: bpy.props.FloatProperty(
        name="Radius",
        description="Approximate placement radius for this bush",
        default=1.4,
        min=0.05,
        max=20.0,
        unit="LENGTH",
        update=_refresh_bush_on_update,
    )
    height: bpy.props.FloatProperty(
        name="Height",
        description="Approximate maximum vertical spread for this bush",
        default=1.0,
        min=0.05,
        max=20.0,
        unit="LENGTH",
        update=_refresh_bush_on_update,
    )
    seed: bpy.props.IntProperty(
        name="Seed",
        description="Random seed used for repeatable generation",
        default=1,
        min=0,
        max=999999,
        update=_refresh_bush_on_update,
    )
    auto_update: bpy.props.BoolProperty(
        name="Live Update",
        description="Rebuild the bush immediately when settings change",
        default=False,
    )
    sources: bpy.props.CollectionProperty(type=NatureToolSourceObject)


class NatureToolSettings(bpy.types.PropertyGroup):
    bush_count: bpy.props.IntProperty(
        name="Instances",
        description="Number of mesh instances to place in the generated bush",
        default=24,
        min=1,
        max=500,
    )
    bush_radius: bpy.props.FloatProperty(
        name="Radius",
        description="Approximate placement radius for the generated bush",
        default=1.4,
        min=0.05,
        max=20.0,
        unit="LENGTH",
    )
    bush_height: bpy.props.FloatProperty(
        name="Height",
        description="Approximate maximum vertical spread for the generated bush",
        default=1.0,
        min=0.05,
        max=20.0,
        unit="LENGTH",
    )
    random_seed: bpy.props.IntProperty(
        name="Seed",
        description="Random seed used for repeatable generation",
        default=1,
        min=0,
        max=999999,
    )


classes = (
    NatureToolSourceObject,
    NatureToolBushSettings,
    NatureToolSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.nature_tool = bpy.props.PointerProperty(type=NatureToolSettings)
    bpy.types.Object.nature_bush = bpy.props.PointerProperty(type=NatureToolBushSettings)


def unregister():
    del bpy.types.Object.nature_bush
    del bpy.types.Scene.nature_tool

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
