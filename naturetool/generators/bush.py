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


def create_bush(context, source_objects, settings: BushBuildSettings):
    rng = random.Random(settings.seed)
    collection = _create_collection(context, "Bush")
    origin = context.scene.cursor.location.copy()

    for index in range(settings.count):
        source = source_objects[index % len(source_objects)]
        instance = source.copy()
        instance.data = source.data
        instance.name = f"{source.name}_bush_{index + 1:03d}"
        instance.parent = None
        instance.location = origin + _random_position(rng, settings.radius, settings.height)
        instance.rotation_euler = _random_rotation(rng)
        instance.scale = _scaled_vector(source.scale, _random_scale(rng))
        collection.objects.link(instance)

    return collection


def _create_collection(context, base_name):
    collection = bpy.data.collections.new(base_name)
    parent = context.collection or context.scene.collection
    parent.children.link(collection)
    return collection


def _random_position(rng, radius, height):
    angle = rng.uniform(0.0, math.tau)
    distance = radius * math.sqrt(rng.random())
    z = rng.uniform(0.0, height)
    return Vector((
        math.cos(angle) * distance,
        math.sin(angle) * distance,
        z,
    ))


def _random_rotation(rng):
    return Euler((
        rng.uniform(math.radians(-12.0), math.radians(12.0)),
        rng.uniform(math.radians(-12.0), math.radians(12.0)),
        rng.uniform(0.0, math.tau),
    ))


def _random_scale(rng):
    return rng.uniform(0.75, 1.25)


def _scaled_vector(vector, scale):
    return (
        vector.x * scale,
        vector.y * scale,
        vector.z * scale,
    )
