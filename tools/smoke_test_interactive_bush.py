import bpy
from mathutils import Vector


def generated_children(controller):
    return [
        child
        for child in controller.children
        if child.get("naturetool_role") == "naturetool_bush_instance"
    ]


def assert_forward_points_outward(controller):
    for child in generated_children(controller):
        radial = Vector((child.location.x, child.location.y, 0.0))
        if radial.length_squared == 0.0:
            continue

        radial.normalize()
        forward = child.rotation_euler.to_matrix() @ Vector((0.0, -1.0, 0.0))
        forward.z = 0.0
        forward.normalize()
        assert forward.dot(radial) > 0.9, (child.name, forward, radial)


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
    assert_forward_points_outward(controller)

    controller.nature_bush.count = 8
    result = bpy.ops.naturetool.update_bush()
    assert result == {"FINISHED"}, result
    assert len(generated_children(controller)) == 8
    assert_forward_points_outward(controller)

    controller.nature_bush.auto_update = True
    controller.nature_bush.count = 3
    assert len(generated_children(controller)) == 3
    assert_forward_points_outward(controller)

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
    assert_forward_points_outward(controller)

    controller_name = controller.name
    generated_names = [child.name for child in generated_children(controller)]
    result = bpy.ops.naturetool.delete_bush()
    assert result == {"FINISHED"}, result
    assert controller_name not in bpy.data.objects
    for name in generated_names:
        assert name not in bpy.data.objects
    assert source_a.name in bpy.data.objects
    assert source_b.name in bpy.data.objects

    print("naturetool interactive bush ok")


main()
