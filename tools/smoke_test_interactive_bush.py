import bpy


def generated_children(controller):
    return [
        child
        for child in controller.children
        if child.get("naturetool_role") == "naturetool_bush_instance"
    ]


def main():
    bpy.ops.preferences.addon_enable(module="naturetool")

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
    source_a = bpy.context.object
    source_a.name = "BushSourceA"

    settings = bpy.context.scene.nature_tool
    settings.bush_count = 5
    settings.bush_radius = 2.0
    settings.bush_height = 1.25
    settings.random_seed = 42

    result = bpy.ops.naturetool.create_bush()
    assert result == {"FINISHED"}, result

    controller = bpy.context.active_object
    assert controller.nature_bush.is_controller
    assert len(generated_children(controller)) == 5

    controller.nature_bush.count = 8
    result = bpy.ops.naturetool.update_bush()
    assert result == {"FINISHED"}, result
    assert len(generated_children(controller)) == 8

    controller.nature_bush.auto_update = True
    controller.nature_bush.count = 3
    assert len(generated_children(controller)) == 3

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=8,
        ring_count=4,
        radius=0.5,
        location=(3.0, 0.0, 0.0),
    )
    source_b = bpy.context.object
    source_b.name = "BushSourceB"

    for obj in bpy.context.scene.objects:
        obj.select_set(False)

    source_b.select_set(True)
    controller.select_set(True)
    bpy.context.view_layer.objects.active = controller

    result = bpy.ops.naturetool.set_bush_sources()
    assert result == {"FINISHED"}, result
    assert len(controller.nature_bush.sources) == 1
    assert controller.nature_bush.sources[0].object == source_b

    print("naturetool interactive bush ok")


main()
