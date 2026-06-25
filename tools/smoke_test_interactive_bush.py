import bpy
from mathutils import Vector


def generated_children(controller):
    return [
        child
        for child in controller.children
        if child.get("naturetool_role") == "naturetool_bush_instance"
    ]


def layer_children(controller, layer):
    return [
        child
        for child in generated_children(controller)
        if child.get("naturetool_instance_layer") == layer
    ]


def assert_instance_counts(controller, body_count, top_count):
    assert len(layer_children(controller, "body")) == body_count
    assert len(layer_children(controller, "top")) == top_count
    assert len(generated_children(controller)) == body_count + top_count


def assert_volume_object(controller):
    volume = controller.nature_bush.volume_object
    assert volume
    assert volume.type == "MESH"
    assert volume.parent == controller
    assert volume.get("naturetool_role") == "naturetool_bush_volume"
    return volume


def assert_points_in_default_volume(controller):
    half_size = controller.nature_bush.volume_size * 0.5

    for child in generated_children(controller):
        assert abs(child.location.x) <= half_size
        assert abs(child.location.y) <= half_size
        assert abs(child.location.z) <= half_size


def assert_top_cap_children(controller):
    half_size = controller.nature_bush.volume_size * 0.5
    density = controller.nature_bush.top_density
    cap_ratio = 0.38 / (max(density, 0.25) ** 0.5)
    cap_ratio = max(0.08, min(cap_ratio, 0.6))
    min_z = half_size - controller.nature_bush.volume_size * cap_ratio

    for child in layer_children(controller, "top"):
        assert child.location.z >= min_z - 0.001, (child.name, child.location.z, min_z)


def assert_droop_meshes(controller):
    bent_children = [
        child
        for child in generated_children(controller)
        if child.data.get("naturetool_generated_mesh")
    ]
    assert bent_children
    assert any(
        vertex.co.z < -0.0001
        for child in bent_children
        for vertex in child.data.vertices
    )
    assert_growth_segment_lengths_preserved(bent_children[0])


def assert_growth_segment_lengths_preserved(child):
    center_indices = [1, 4, 7, 10, 13]
    expected_length = 0.25

    for start, end in zip(center_indices, center_indices[1:]):
        segment_length = (
            child.data.vertices[end].co - child.data.vertices[start].co
        ).length
        assert abs(segment_length - expected_length) < 0.003, (
            child.name,
            segment_length,
            expected_length,
        )


def assert_forward_points_outward(controller):
    for child in generated_children(controller):
        normal = child.location.copy()
        if normal.length_squared == 0.0:
            continue

        normal.normalize()
        forward = child.rotation_euler.to_matrix() @ Vector((0.0, -1.0, 0.0))
        forward.normalize()
        assert forward.dot(normal) > 0.98, (child.name, forward, normal)


def main():
    bpy.ops.preferences.addon_enable(module="naturetool")

    source_mesh = bpy.data.meshes.new("BushSourceA_Mesh")
    vertices = []
    for row in range(5):
        y = -0.25 * row
        vertices.extend((
            (-0.1, y, 0.0),
            (0.0, y, 0.0),
            (0.1, y, 0.0),
        ))

    faces = []
    for row in range(4):
        start = row * 3
        next_start = (row + 1) * 3
        faces.append((start, start + 1, next_start + 1, next_start))
        faces.append((start + 1, start + 2, next_start + 2, next_start + 1))

    source_mesh.from_pydata(
        vertices,
        (),
        faces,
    )
    source_mesh.update()
    source_a = bpy.data.objects.new("BushSourceA", source_mesh)
    bpy.context.scene.collection.objects.link(source_a)
    source_a.select_set(True)
    bpy.context.view_layer.objects.active = source_a
    source_a.name = "BushSourceA"

    settings = bpy.context.scene.nature_tool
    settings.bush_count = 5
    settings.bush_top_count = 4
    settings.bush_top_density = 2.5
    settings.bush_volume_size = 2.5
    settings.bush_droop_curvature = 0.35
    settings.random_seed = 42

    result = bpy.ops.naturetool.create_bush()
    assert result == {"FINISHED"}, result

    controller = bpy.context.active_object
    assert controller.nature_bush.is_controller
    default_volume = assert_volume_object(controller)
    assert default_volume.get("naturetool_owned_volume")
    assert_instance_counts(controller, 5, 4)
    assert_points_in_default_volume(controller)
    assert_top_cap_children(controller)
    assert_droop_meshes(controller)
    assert_forward_points_outward(controller)

    controller.nature_bush.count = 8
    result = bpy.ops.naturetool.update_bush()
    assert result == {"FINISHED"}, result
    assert_instance_counts(controller, 8, 4)
    assert_points_in_default_volume(controller)
    assert_top_cap_children(controller)
    assert_droop_meshes(controller)
    assert_forward_points_outward(controller)

    controller.nature_bush.auto_update = True
    controller.nature_bush.count = 3
    assert_instance_counts(controller, 3, 4)
    assert_points_in_default_volume(controller)
    assert_top_cap_children(controller)
    assert_droop_meshes(controller)
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

    default_volume_name = default_volume.name
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.5))
    custom_volume = bpy.context.object
    custom_volume.name = "CustomBushVolume"
    custom_volume.scale = (2.4, 1.4, 1.2)

    for obj in bpy.context.scene.objects:
        obj.select_set(False)

    custom_volume.select_set(True)
    controller.select_set(True)
    bpy.context.view_layer.objects.active = controller

    result = bpy.ops.naturetool.set_bush_volume()
    assert result == {"FINISHED"}, result
    assert controller.nature_bush.volume_object == custom_volume
    assert custom_volume.parent == controller
    assert not custom_volume.get("naturetool_owned_volume")
    assert default_volume_name not in bpy.data.objects
    assert_instance_counts(controller, 3, 4)
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
    assert custom_volume.name in bpy.data.objects
    assert custom_volume.parent is None

    print("naturetool interactive bush ok")


main()
