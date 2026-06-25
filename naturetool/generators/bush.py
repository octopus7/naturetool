from dataclasses import dataclass
import math
import random

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


@dataclass(frozen=True)
class BushBuildSettings:
    count: int
    top_count: int
    top_density: float
    top_scale: float
    top_root_trim: float
    volume_size: float
    droop_curvature: float
    seed: int


INSTANCE_ROLE = "naturetool_bush_instance"
VOLUME_ROLE = "naturetool_bush_volume"
OWNED_VOLUME_KEY = "naturetool_owned_volume"
GENERATED_MESH_KEY = "naturetool_generated_mesh"
INSTANCE_LAYER_KEY = "naturetool_instance_layer"
BODY_LAYER = "body"
TOP_LAYER = "top"
MAX_TWIST_JITTER = math.radians(14.0)
SAMPLING_OVERSUBDIVISION = 2.5
DROOP_RADIANS_PER_UNIT = math.radians(70.0)


def is_bush_controller(obj):
    return bool(
        obj
        and hasattr(obj, "nature_bush")
        and obj.nature_bush.is_controller
    )


def create_bush(context, source_objects, settings: BushBuildSettings):
    collection = _create_collection(context, "Bush")
    controller = bpy.data.objects.new("Bush Controller", None)
    controller.empty_display_type = "SPHERE"
    controller.empty_display_size = max(settings.volume_size, 0.25) * 0.5
    controller.location = context.scene.cursor.location.copy()
    collection.objects.link(controller)

    bush = controller.nature_bush
    bush.is_controller = True
    bush.collection_name = collection.name
    bush.count = settings.count
    bush.top_count = settings.top_count
    bush.top_density = settings.top_density
    bush.top_scale = settings.top_scale
    bush.top_root_trim = settings.top_root_trim
    bush.volume_size = settings.volume_size
    bush.droop_curvature = settings.droop_curvature
    bush.seed = settings.seed
    bush.auto_update = False
    _set_sources(bush, source_objects)

    rebuild_bush(context, controller)
    return controller, collection


def rebuild_bush(context, controller):
    if not is_bush_controller(controller):
        raise ValueError("Object is not a Nature Tool bush controller")

    bush = controller.nature_bush
    source_objects = _source_objects(bush)
    if not source_objects:
        raise ValueError("Bush controller has no valid mesh sources")

    collection = _collection_for_controller(context, controller)
    _remove_generated_instances(controller)
    volume_object = _ensure_volume_object(context, collection, controller)
    controller.empty_display_size = max(bush.volume_size, 0.25) * 0.5

    rng = random.Random(bush.seed)
    sampler = _VolumeSampler(context, volume_object)
    positions = _sample_volume_positions(rng, sampler, volume_object, controller, bush.count)
    top_positions = _sample_top_cap_positions(
        rng,
        sampler,
        volume_object,
        controller,
        bush.top_count,
        bush.top_density,
    )
    _create_instances(collection, controller, source_objects, rng, positions, BODY_LAYER)
    _create_instances(collection, controller, source_objects, rng, top_positions, TOP_LAYER)

    return collection


def _create_instances(collection, controller, source_objects, rng, positions, layer):
    bush = controller.nature_bush

    for index, position in enumerate(positions):
        source = source_objects[index % len(source_objects)]
        rotation = _normal_aligned_rotation(rng, position)
        top_layer = layer == TOP_LAYER
        instance = source.copy()
        instance.data = _instance_mesh_data(
            source,
            rotation,
            bush.droop_curvature,
            bush.top_root_trim if top_layer else 0.0,
        )
        instance.name = f"{source.name}_bush_{layer}_{index + 1:03d}"
        instance.parent = controller
        instance.matrix_parent_inverse.identity()
        instance.location = position
        instance.rotation_euler = rotation
        layer_scale = bush.top_scale if top_layer else 1.0
        instance.scale = _scaled_vector(source.scale, _random_scale(rng) * layer_scale)
        instance["naturetool_role"] = INSTANCE_ROLE
        instance[INSTANCE_LAYER_KEY] = layer
        collection.objects.link(instance)


def set_bush_sources(controller, source_objects):
    if not is_bush_controller(controller):
        raise ValueError("Object is not a Nature Tool bush controller")

    _set_sources(controller.nature_bush, source_objects)


def set_bush_volume(context, controller, volume_object):
    if not is_bush_controller(controller):
        raise ValueError("Object is not a Nature Tool bush controller")
    if not volume_object or volume_object.type != "MESH":
        raise ValueError("Select a mesh object to use as the bush volume")

    bush = controller.nature_bush
    old_volume = bush.volume_object
    if old_volume and old_volume != volume_object and _is_owned_volume(old_volume):
        bpy.data.objects.remove(old_volume, do_unlink=True)

    collection = _collection_for_controller(context, controller)
    _link_object(collection, volume_object)
    _parent_to_controller(volume_object, controller)
    volume_object["naturetool_role"] = VOLUME_ROLE
    volume_object[OWNED_VOLUME_KEY] = False
    bush.volume_object = volume_object


def delete_bush(context, controller):
    if not is_bush_controller(controller):
        raise ValueError("Object is not a Nature Tool bush controller")

    collection = bpy.data.collections.get(controller.nature_bush.collection_name)
    _remove_generated_instances(controller)
    _remove_or_detach_volume_objects(controller)
    bpy.data.objects.remove(controller, do_unlink=True)

    if collection and len(collection.objects) == 0 and len(collection.children) == 0:
        _unlink_collection(context, collection)
        bpy.data.collections.remove(collection)


def combine_bush(context, controller, include_volume=False):
    if not is_bush_controller(controller):
        raise ValueError("Object is not a Nature Tool bush controller")

    source_objects = _generated_instances(controller)
    volume_object = controller.nature_bush.volume_object
    if include_volume and volume_object and volume_object.type == "MESH":
        source_objects.append(volume_object)

    if not source_objects:
        raise ValueError("Bush controller has no generated mesh instances")

    collection = _collection_for_controller(context, controller)
    combined = _join_evaluated_meshes(
        context,
        collection,
        controller,
        source_objects,
        "Bush Combined",
    )
    combined["naturetool_role"] = "naturetool_combined_bush"
    combined["naturetool_source_controller"] = controller.name
    return combined


def _set_sources(bush, source_objects):
    bush.sources.clear()

    for source in source_objects:
        item = bush.sources.add()
        item.object = source


def _source_objects(bush):
    return [
        item.object
        for item in bush.sources
        if item.object and item.object.type == "MESH"
    ]


def _generated_instances(controller):
    return [
        child
        for child in controller.children
        if child.type == "MESH" and child.get("naturetool_role") == INSTANCE_ROLE
    ]


def _create_collection(context, base_name):
    collection = bpy.data.collections.new(base_name)
    parent = context.collection or context.scene.collection
    parent.children.link(collection)
    return collection


def _collection_for_controller(context, controller):
    bush = controller.nature_bush
    collection = bpy.data.collections.get(bush.collection_name)
    if not collection:
        collection = _create_collection(context, "Bush")
        bush.collection_name = collection.name

    if controller.name not in collection.objects:
        collection.objects.link(controller)

    return collection


def _ensure_volume_object(context, collection, controller):
    bush = controller.nature_bush
    volume_object = bush.volume_object

    if not volume_object or volume_object.type != "MESH":
        volume_object = _owned_volume_child(controller)

    if not volume_object or volume_object.type != "MESH":
        volume_object = _create_default_volume(collection, controller, bush)
        bush.volume_object = volume_object
        return volume_object

    _link_object(collection, volume_object)
    if _is_owned_volume(volume_object):
        _update_default_volume_mesh(volume_object, bush)

    return volume_object


def _create_default_volume(collection, controller, bush):
    mesh = bpy.data.meshes.new("Bush Volume Mesh")
    volume_object = bpy.data.objects.new("Bush Volume", mesh)
    volume_object.parent = controller
    volume_object.matrix_parent_inverse.identity()
    volume_object.display_type = "WIRE"
    volume_object.show_wire = True
    volume_object.show_in_front = True
    volume_object.hide_render = True
    volume_object["naturetool_role"] = VOLUME_ROLE
    volume_object[OWNED_VOLUME_KEY] = True
    _update_default_volume_mesh(volume_object, bush)
    _link_object(collection, volume_object)
    return volume_object


def _update_default_volume_mesh(volume_object, bush):
    size = max(bush.volume_size, 0.1)
    half_size = size * 0.5

    vertices = (
        (-half_size, -half_size, -half_size),
        (half_size, -half_size, -half_size),
        (half_size, half_size, -half_size),
        (-half_size, half_size, -half_size),
        (-half_size, -half_size, half_size),
        (half_size, -half_size, half_size),
        (half_size, half_size, half_size),
        (-half_size, half_size, half_size),
    )
    faces = (
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    )

    mesh = volume_object.data
    mesh.clear_geometry()
    mesh.from_pydata(vertices, (), faces)
    mesh.update()

    bevel = volume_object.modifiers.get("Rounded Corners")
    if not bevel:
        bevel = volume_object.modifiers.new("Rounded Corners", "BEVEL")
    bevel.width = size * 0.49
    bevel.segments = 12
    bevel.profile = 0.5

    if not volume_object.modifiers.get("Weighted Normals"):
        volume_object.modifiers.new("Weighted Normals", "WEIGHTED_NORMAL")


def _owned_volume_child(controller):
    for child in controller.children:
        if _is_owned_volume(child):
            return child

    return None


def _is_owned_volume(obj):
    return bool(
        obj
        and obj.type == "MESH"
        and obj.get("naturetool_role") == VOLUME_ROLE
        and obj.get(OWNED_VOLUME_KEY)
    )


def _link_object(collection, obj):
    if all(existing != obj for existing in collection.objects):
        collection.objects.link(obj)


def _parent_to_controller(obj, controller):
    world_matrix = obj.matrix_world.copy()
    obj.parent = controller
    obj.matrix_world = world_matrix


def _join_evaluated_meshes(context, collection, controller, source_objects, name):
    depsgraph = context.evaluated_depsgraph_get()
    temp_objects = []
    base_mesh = bpy.data.meshes.new(f"{name} Mesh")
    base_object = bpy.data.objects.new(name, base_mesh)
    base_object.matrix_world = controller.matrix_world.copy()
    collection.objects.link(base_object)

    selected_objects = list(context.selected_objects)
    active_object = context.view_layer.objects.active

    try:
        for source in source_objects:
            evaluated = source.evaluated_get(depsgraph)
            mesh = bpy.data.meshes.new_from_object(
                evaluated,
                preserve_all_data_layers=True,
                depsgraph=depsgraph,
            )
            if len(mesh.materials) == 0:
                for slot in source.material_slots:
                    if slot.material:
                        mesh.materials.append(slot.material)

            temp = bpy.data.objects.new(f"{source.name}_combine_tmp", mesh)
            temp.matrix_world = source.matrix_world.copy()
            collection.objects.link(temp)
            temp_objects.append(temp)

        for obj in context.selected_objects:
            obj.select_set(False)

        base_object.select_set(True)
        for temp in temp_objects:
            temp.select_set(True)

        context.view_layer.objects.active = base_object
        result = bpy.ops.object.join()
        if result != {"FINISHED"}:
            raise ValueError("Could not join bush meshes")

        base_object.name = name
        base_object.data.name = f"{name} Mesh"
        return base_object
    except Exception:
        for temp in temp_objects:
            if temp.name in bpy.data.objects:
                mesh = temp.data
                bpy.data.objects.remove(temp, do_unlink=True)
                if mesh and mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
        if base_object.name in bpy.data.objects:
            bpy.data.objects.remove(base_object, do_unlink=True)
        raise
    finally:
        for obj in context.selected_objects:
            obj.select_set(False)

        for obj in selected_objects:
            if obj.name in bpy.data.objects:
                obj.select_set(True)

        if active_object and active_object.name in bpy.data.objects:
            context.view_layer.objects.active = active_object


def _remove_generated_instances(controller):
    for child in list(controller.children):
        if child.get("naturetool_role") == INSTANCE_ROLE:
            mesh = child.data if child.type == "MESH" else None
            bpy.data.objects.remove(child, do_unlink=True)
            if mesh and mesh.get(GENERATED_MESH_KEY) and mesh.users == 0:
                bpy.data.meshes.remove(mesh)


def _remove_or_detach_volume_objects(controller):
    for child in list(controller.children):
        if child.get("naturetool_role") != VOLUME_ROLE:
            continue

        if child.get(OWNED_VOLUME_KEY):
            bpy.data.objects.remove(child, do_unlink=True)
            continue

        world_matrix = child.matrix_world.copy()
        child.parent = None
        child.matrix_world = world_matrix


def _unlink_collection(context, collection):
    parents = [
        candidate
        for candidate in bpy.data.collections
        if collection.name in candidate.children
    ]

    for parent in parents:
        parent.children.unlink(collection)

    if collection.name in context.scene.collection.children:
        context.scene.collection.children.unlink(collection)


def _sample_volume_positions(rng, sampler, volume_object, controller, count):
    points = []
    candidates = _jittered_grid_candidates(
        rng,
        sampler.bounds_min,
        sampler.bounds_max,
        max(count, int(count * SAMPLING_OVERSUBDIVISION)),
    )

    for candidate in candidates:
        if sampler.contains(candidate):
            points.append(_volume_point_to_controller_space(volume_object, controller, candidate))
            if len(points) == count:
                return points

    max_attempts = max(1000, count * 250)
    for _ in range(max_attempts):
        candidate = _random_point_in_bounds(rng, sampler.bounds_min, sampler.bounds_max)
        if sampler.contains(candidate):
            points.append(_volume_point_to_controller_space(volume_object, controller, candidate))
            if len(points) == count:
                return points

    raise ValueError("Could not sample enough points from the volume mesh. Use a closed mesh volume.")


def _sample_top_cap_positions(rng, sampler, volume_object, controller, count, density):
    if count <= 0:
        return []

    points = []
    candidates = _jittered_grid_candidates(
        rng,
        sampler.bounds_min,
        sampler.bounds_max,
        max(count, int(count * SAMPLING_OVERSUBDIVISION * max(density, 1.0) * 4.0)),
    )

    for candidate in candidates:
        if sampler.contains(candidate) and rng.random() <= _top_cap_weight(sampler, candidate, density):
            points.append(_volume_point_to_controller_space(volume_object, controller, candidate))
            if len(points) == count:
                return points

    max_attempts = max(2000, count * 1000)
    for _ in range(max_attempts):
        candidate = _random_point_in_bounds(rng, sampler.bounds_min, sampler.bounds_max)
        if sampler.contains(candidate) and rng.random() <= _top_cap_weight(sampler, candidate, density):
            points.append(_volume_point_to_controller_space(volume_object, controller, candidate))
            if len(points) == count:
                return points

    raise ValueError("Could not sample enough top cap points from the volume mesh.")


def _top_cap_weight(sampler, point, density):
    density = max(density, 0.25)
    span = sampler.bounds_max - sampler.bounds_min
    z_norm = (point.z - sampler.bounds_min.z) / max(span.z, 0.001)
    z_norm = max(0.0, min(z_norm, 1.0))

    center_x = (sampler.bounds_min.x + sampler.bounds_max.x) * 0.5
    center_y = (sampler.bounds_min.y + sampler.bounds_max.y) * 0.5
    x_norm = (point.x - center_x) / max(span.x * 0.5, 0.001)
    y_norm = (point.y - center_y) / max(span.y * 0.5, 0.001)
    radial_norm = min(math.sqrt((x_norm * x_norm) + (y_norm * y_norm)), 1.0)

    vertical_weight = z_norm ** (1.0 + density * 0.9)
    center_weight = (1.0 - radial_norm * radial_norm) ** (0.75 + density * 0.35)
    return max(0.0, min(vertical_weight * center_weight, 1.0))


def _volume_point_to_controller_space(volume_object, controller, point):
    world_point = volume_object.matrix_world @ point
    return controller.matrix_world.inverted() @ world_point


def _jittered_grid_candidates(rng, bounds_min, bounds_max, target_count):
    size = bounds_max - bounds_min
    divisions = _grid_divisions(size, target_count)
    cell = Vector((
        size.x / divisions[0],
        size.y / divisions[1],
        size.z / divisions[2],
    ))
    candidates = []

    for x_index in range(divisions[0]):
        for y_index in range(divisions[1]):
            for z_index in range(divisions[2]):
                candidates.append(Vector((
                    bounds_min.x + (x_index + rng.random()) * cell.x,
                    bounds_min.y + (y_index + rng.random()) * cell.y,
                    bounds_min.z + (z_index + rng.random()) * cell.z,
                )))

    rng.shuffle(candidates)
    return candidates


def _grid_divisions(size, target_count):
    safe_size = Vector((
        max(size.x, 0.001),
        max(size.y, 0.001),
        max(size.z, 0.001),
    ))
    volume = safe_size.x * safe_size.y * safe_size.z
    cell_size = (volume / max(target_count, 1)) ** (1.0 / 3.0)
    divisions = [
        max(1, math.ceil(safe_size.x / cell_size)),
        max(1, math.ceil(safe_size.y / cell_size)),
        max(1, math.ceil(safe_size.z / cell_size)),
    ]

    while divisions[0] * divisions[1] * divisions[2] < target_count:
        ratios = (
            safe_size.x / divisions[0],
            safe_size.y / divisions[1],
            safe_size.z / divisions[2],
        )
        axis = max(range(3), key=lambda index: ratios[index])
        divisions[axis] += 1

    return tuple(divisions)


def _random_point_in_bounds(rng, bounds_min, bounds_max):
    return Vector((
        rng.uniform(bounds_min.x, bounds_max.x),
        rng.uniform(bounds_min.y, bounds_max.y),
        rng.uniform(bounds_min.z, bounds_max.z),
    ))


class _VolumeSampler:
    def __init__(self, context, volume_object):
        depsgraph = context.evaluated_depsgraph_get()
        evaluated_object = volume_object.evaluated_get(depsgraph)
        mesh = evaluated_object.to_mesh()
        try:
            vertices = [vertex.co.copy() for vertex in mesh.vertices]
            polygons = [
                tuple(polygon.vertices)
                for polygon in mesh.polygons
                if len(polygon.vertices) >= 3
            ]
        finally:
            evaluated_object.to_mesh_clear()

        if not vertices or not polygons:
            raise ValueError("Volume mesh must have vertices and faces")

        self.tree = BVHTree.FromPolygons(vertices, polygons)
        self.bounds_min = Vector((
            min(vertex.x for vertex in vertices),
            min(vertex.y for vertex in vertices),
            min(vertex.z for vertex in vertices),
        ))
        self.bounds_max = Vector((
            max(vertex.x for vertex in vertices),
            max(vertex.y for vertex in vertices),
            max(vertex.z for vertex in vertices),
        ))
        self.ray_direction = Vector((1.0, 0.371, 0.113)).normalized()
        self.max_ray_distance = (self.bounds_max - self.bounds_min).length * 2.0
        self.epsilon = max(self.max_ray_distance * 0.00001, 0.000001)

    def contains(self, point):
        origin = point.copy()
        remaining_distance = self.max_ray_distance
        hit_count = 0

        for _ in range(128):
            location, _normal, _index, distance = self.tree.ray_cast(
                origin,
                self.ray_direction,
                remaining_distance,
            )
            if location is None:
                break

            if distance > self.epsilon:
                hit_count += 1

            step = max(distance, self.epsilon) + self.epsilon
            origin = location + self.ray_direction * self.epsilon
            remaining_distance -= step
            if remaining_distance <= 0.0:
                break

        return hit_count % 2 == 1


def _normal_aligned_rotation(rng, position):
    normal = position.copy()
    if normal.length_squared == 0.0:
        normal = Vector((1.0, 0.0, 0.0))

    normal.normalize()
    up_hint = Vector((0.0, 0.0, 1.0))
    if abs(normal.dot(up_hint)) > 0.96:
        up_hint = Vector((1.0, 0.0, 0.0))

    right = up_hint.cross(normal).normalized()
    up = normal.cross(right).normalized()
    matrix = Matrix((
        (right.x, -normal.x, up.x),
        (right.y, -normal.y, up.y),
        (right.z, -normal.z, up.z),
    ))
    twist = Matrix.Rotation(rng.uniform(-MAX_TWIST_JITTER, MAX_TWIST_JITTER), 3, normal)
    return (twist @ matrix).to_euler()


def _instance_mesh_data(source, rotation, droop_curvature, root_trim=0.0):
    if droop_curvature <= 0.0 and root_trim <= 0.0:
        return source.data

    mesh = source.data.copy()
    mesh.name = f"{source.data.name}_generated"
    mesh[GENERATED_MESH_KEY] = True
    _collapse_growth_start(mesh, root_trim)
    if droop_curvature > 0.0:
        _bend_downward_preserving_length(mesh, rotation, droop_curvature)
    return mesh


def _collapse_growth_start(mesh, root_trim):
    root_trim = max(0.0, min(root_trim, 0.9))
    if root_trim <= 0.0 or not mesh.vertices:
        return

    min_y = min(vertex.co.y for vertex in mesh.vertices)
    max_y = max(vertex.co.y for vertex in mesh.vertices)
    growth_length = max_y - min_y
    if growth_length <= 0.000001:
        return

    trim_distance = growth_length * root_trim
    for vertex in mesh.vertices:
        distance = max_y - vertex.co.y
        vertex.co.y = max_y - max(0.0, distance - trim_distance)

    mesh.update()


def _bend_downward_preserving_length(mesh, rotation, droop_curvature):
    if not mesh.vertices:
        return

    min_y = min(vertex.co.y for vertex in mesh.vertices)
    max_y = max(vertex.co.y for vertex in mesh.vertices)
    growth_length = max_y - min_y
    if growth_length <= 0.000001:
        return

    gravity_local = rotation.to_matrix().inverted() @ Vector((0.0, 0.0, -1.0))
    if gravity_local.length_squared == 0.0:
        return

    forward = Vector((0.0, -1.0, 0.0))
    bend_direction = gravity_local - forward * gravity_local.dot(forward)
    if bend_direction.length_squared <= 0.000001:
        return

    bend_direction.normalize()
    side = forward.cross(bend_direction)
    if side.length_squared <= 0.000001:
        return

    side.normalize()
    root_origin = Vector((0.0, max_y, 0.0))
    curvature = (droop_curvature * DROOP_RADIANS_PER_UNIT) / growth_length
    if abs(curvature) <= 0.000001:
        return

    for vertex in mesh.vertices:
        relative = vertex.co - root_origin
        distance = max(0.0, min(relative.dot(forward), growth_length))
        side_offset = relative.dot(side)
        bend_offset = relative.dot(bend_direction)
        angle = curvature * distance

        sin_angle = math.sin(angle)
        cos_angle = math.cos(angle)
        centerline = (
            root_origin
            + forward * (sin_angle / curvature)
            + bend_direction * ((1.0 - cos_angle) / curvature)
        )
        rotated_bend_axis = (-forward * sin_angle) + (bend_direction * cos_angle)
        vertex.co = centerline + side * side_offset + rotated_bend_axis * bend_offset

    mesh.update()


def _random_scale(rng):
    return rng.uniform(0.75, 1.25)


def _scaled_vector(vector, scale):
    return (
        vector.x * scale,
        vector.y * scale,
        vector.z * scale,
    )
