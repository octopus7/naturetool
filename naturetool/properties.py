import bpy


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
    NatureToolSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.nature_tool = bpy.props.PointerProperty(type=NatureToolSettings)


def unregister():
    del bpy.types.Scene.nature_tool

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
