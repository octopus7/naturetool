from dataclasses import dataclass
import math
import random

import bpy
from mathutils import Euler, Vector


@dataclass(frozen=True)
class BushBuildSettings:
    count: int
    radius: float
    height: float
    seed: int


INSTANCE_ROLE = "naturetool_bush_instance"
MAX_YAW_JITTER = math.radians(14.0)
MAX_TILT = math.radians(8.0)


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
    controller.empty_display_size = max(settings.radius, 0.25)
    controller.location = context.scene.cursor.location.copy()
    collection.objects.link(controller)

    bush = controller.nature_bush
    bush.is_controller = True
    bush.collection_name = collection.name
    bush.count = settings.count
    bush.radius = settings.radius
    bush.height = settings.height
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
    controller.empty_display_size = max(bush.radius, 0.25)

    rng = random.Random(bush.seed)
    for index in range(bush.count):
        source = source_objects[index % len(source_objects)]
        position = _random_position(rng, bush.radius, bush.height)
        instance = source.copy()
        instance.data = source.data
        instance.name = f"{source.name}_bush_{index + 1:03d}"
        instance.parent = controller
        instance.matrix_parent_inverse.identity()
        instance.location = position
        instance.rotation_euler = _outward_rotation(rng, position)
        instance.scale = _scaled_vector(source.scale, _random_scale(rng))
        instance["naturetool_role"] = INSTANCE_ROLE
        collection.objects.link(instance)

    return collection


def set_bush_sources(controller, source_objects):
    if not is_bush_controller(controller):
        raise ValueError("Object is not a Nature Tool bush controller")

    _set_sources(controller.nature_bush, source_objects)


def delete_bush(context, controller):
    if not is_bush_controller(controller):
        raise ValueError("Object is not a Nature Tool bush controller")

    collection = bpy.data.collections.get(controller.nature_bush.collection_name)
    _remove_generated_instances(controller)
    bpy.data.objects.remove(controller, do_unlink=True)

    if collection and not collection.objects and not collection.children:
        _unlink_collection(context, collection)
        bpy.data.collections.remove(collection)


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


def _remove_generated_instances(controller):
    for child in list(controller.children):
        if child.get("naturetool_role") == INSTANCE_ROLE:
            bpy.data.objects.remove(child, do_unlink=True)


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


def _random_position(rng, radius, height):
    angle = rng.uniform(0.0, math.tau)
    distance = radius * math.sqrt(rng.random())
    z = rng.uniform(0.0, height)
    return Vector((
        math.cos(angle) * distance,
        math.sin(angle) * distance,
        z,
    ))


def _outward_rotation(rng, position):
    direction = Vector((position.x, position.y, 0.0))
    if direction.length_squared == 0.0:
        direction = Vector((1.0, 0.0, 0.0))

    direction.normalize()
    yaw = math.atan2(direction.y, direction.x) + math.pi / 2.0
    yaw += rng.uniform(-MAX_YAW_JITTER, MAX_YAW_JITTER)

    return Euler((
        rng.uniform(-MAX_TILT, MAX_TILT),
        rng.uniform(-MAX_TILT, MAX_TILT),
        yaw,
    ))


def _random_scale(rng):
    return rng.uniform(0.75, 1.25)


def _scaled_vector(vector, scale):
    return (
        vector.x * scale,
        vector.y * scale,
        vector.z * scale,
    )
