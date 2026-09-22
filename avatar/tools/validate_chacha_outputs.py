import json
import math
import os

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLEND = os.path.join(ROOT, "08_Final", "Chacha_Rigged.blend")
FBX = os.path.join(ROOT, "08_Final", "Chacha_Rigged.fbx")
OUT_JSON = os.path.join(ROOT, "08_Final", "Chacha_Output_Validation.json")
OUT_DIR = os.path.join(ROOT, "08_Final", "validation_renders")


def scene_bounds(meshes):
    pts = []
    for obj in meshes:
        for corner in obj.bound_box:
            pts.append(obj.matrix_world @ Vector(corner))
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def setup_render(meshes):
    os.makedirs(OUT_DIR, exist_ok=True)
    mn, mx = scene_bounds(meshes)
    center = (mn + mx) * 0.5
    height = mx.z - mn.z
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.eevee.taa_render_samples = 16
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 1200
    bpy.context.scene.world.color = (0.04, 0.04, 0.055)

    if not bpy.context.scene.camera:
        bpy.ops.object.camera_add()
        bpy.context.scene.camera = bpy.context.object
    cam = bpy.context.scene.camera
    cam.location = (center.x, center.y - height * 2.15, center.z + height * 0.08)
    direction = Vector((center.x, center.y, center.z + height * 0.08)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 55

    if not any(o.type == "LIGHT" for o in bpy.context.scene.objects):
        bpy.ops.object.light_add(type="AREA", location=(center.x, center.y - height, center.z + height))
        light = bpy.context.object
        light.data.energy = 450
        light.data.size = 5


def render_action(arm, action_name, frame):
    action = bpy.data.actions[action_name]
    arm.animation_data_create()
    arm.animation_data.action = action
    bpy.context.scene.frame_set(frame)
    path = os.path.join(OUT_DIR, f"{action_name}_frame_{frame}.png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def render_expression(mesh, expression_name):
    key_blocks = mesh.data.shape_keys.key_blocks
    for key in key_blocks:
        if key.name != "Basis":
            key.value = 0.0
    key_blocks[expression_name].value = 1.0
    bpy.context.scene.frame_set(1)
    path = os.path.join(OUT_DIR, f"{expression_name}.png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    key_blocks[expression_name].value = 0.0
    return path


def validate_blend():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    armatures = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    arm = armatures[0] if armatures else None
    setup_render(meshes)
    renders = []
    if arm:
        checkpoints = (
            ("Idle_Breathing", 30),
            ("Talking_UpperBody", 36),
            ("Head_Nod", 16),
            ("Head_Turn", 20),
            ("Simple_Hand_Gesture", 24),
            ("Happy_Reaction", 18),
            ("Thinking_Reaction", 18),
        )
        for action_name, frame in checkpoints:
            if action_name in bpy.data.actions:
                renders.append(render_action(arm, action_name, frame))
    expression_renders = []
    if meshes and meshes[0].data.shape_keys:
        for expression_name in ("Face_Happy", "Face_Thinking", "Face_Surprised", "Face_SadConfused", "Mouth_Open"):
            if expression_name in meshes[0].data.shape_keys.key_blocks:
                expression_renders.append(render_expression(meshes[0], expression_name))
    return {
        "blend_armature_count": len(armatures),
        "blend_mesh_count": len(meshes),
        "blend_bone_count": len(arm.data.bones) if arm else 0,
        "blend_actions": sorted(a.name for a in bpy.data.actions),
        "blend_mesh_modifiers": {
            obj.name: [{"name": m.name, "type": m.type, "target": getattr(m, "object", None).name if getattr(m, "object", None) else None} for m in obj.modifiers]
            for obj in meshes
        },
        "blend_materials": sorted(m.name for m in bpy.data.materials),
        "blend_shape_keys": [key.name for key in meshes[0].data.shape_keys.key_blocks] if meshes and meshes[0].data.shape_keys else [],
        "renders": renders,
        "expression_renders": expression_renders,
    }


def validate_fbx_reimport():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.ops.import_scene.fbx(filepath=FBX, automatic_bone_orientation=False)
    armatures = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    return {
        "fbx_reimport_armature_count": len(armatures),
        "fbx_reimport_mesh_count": len(meshes),
        "fbx_reimport_bone_count": len(armatures[0].data.bones) if armatures else 0,
        "fbx_reimport_actions": sorted(a.name for a in bpy.data.actions),
        "fbx_reimport_materials": sorted(m.name for m in bpy.data.materials),
        "fbx_reimport_shape_keys": [key.name for key in meshes[0].data.shape_keys.key_blocks] if meshes and meshes[0].data.shape_keys else [],
        "fbx_reimport_has_armature_modifier": any(
            m.type == "ARMATURE" for obj in meshes for m in obj.modifiers
        ),
    }


def main():
    result = validate_blend()
    result.update(validate_fbx_reimport())
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
