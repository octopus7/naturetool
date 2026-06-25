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
    volume_object: bpy.props.PointerProperty(
        name="Volume Mesh",
        description="Closed mesh volume used to distribute bush instances",
        type=bpy.types.Object,
        update=_refresh_bush_on_update,
    )
    count: bpy.props.IntProperty(
        name="Instances",
        description="Number of body mesh instances in this bush",
        default=24,
        min=1,
        max=500,
        update=_refresh_bush_on_update,
    )
    top_count: bpy.props.IntProperty(
        name="Top Instances",
        description="Additional mesh instances placed in the top cap area",
        default=8,
        min=0,
        max=500,
        update=_refresh_bush_on_update,
    )
    top_density: bpy.props.FloatProperty(
        name="Top Density",
        description="How tightly top cap instances are concentrated near the volume top",
        default=2.0,
        min=0.25,
        max=8.0,
        update=_refresh_bush_on_update,
    )
    volume_size: bpy.props.FloatProperty(
        name="Volume Size",
        description="Default near-spherical rounded-cube volume size",
        default=2.5,
        min=0.1,
        max=20.0,
        unit="LENGTH",
        update=_refresh_bush_on_update,
    )
    droop_curvature: bpy.props.FloatProperty(
        name="Droop Curvature",
        description="Downward bend amount applied along each source mesh's local -Y growth direction",
        default=0.2,
        min=0.0,
        max=3.0,
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
        description="Number of body mesh instances to place in the generated bush",
        default=24,
        min=1,
        max=500,
    )
    bush_top_count: bpy.props.IntProperty(
        name="Top Instances",
        description="Additional mesh instances placed in the top cap area",
        default=8,
        min=0,
        max=500,
    )
    bush_top_density: bpy.props.FloatProperty(
        name="Top Density",
        description="How tightly top cap instances are concentrated near the volume top",
        default=2.0,
        min=0.25,
        max=8.0,
    )
    bush_volume_size: bpy.props.FloatProperty(
        name="Volume Size",
        description="Default near-spherical rounded-cube volume size",
        default=2.5,
        min=0.1,
        max=20.0,
        unit="LENGTH",
    )
    bush_droop_curvature: bpy.props.FloatProperty(
        name="Droop Curvature",
        description="Downward bend amount applied along each source mesh's local -Y growth direction",
        default=0.2,
        min=0.0,
        max=3.0,
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
