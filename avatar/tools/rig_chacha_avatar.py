import json
import math
import os
from collections import defaultdict

import bpy
from mathutils import Euler, Matrix, Vector


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_FBX = os.path.join(ROOT, "01_Reference", "Chacha_Mixamo.fbx")
OUT_BLEND = os.path.join(ROOT, "08_Final", "Chacha_Rigged.blend")
OUT_FBX = os.path.join(ROOT, "08_Final", "Chacha_Rigged.fbx")
REPORT = os.path.join(ROOT, "08_Final", "Chacha_Rigged_Verification.json")


def clear_scene():
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.ops.object.mode_set.poll() else None
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def import_character():
    bpy.ops.import_scene.fbx(filepath=SRC_FBX, automatic_bone_orientation=False)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("No mesh objects were imported from the source FBX.")

    # The supplied FBX imports two near-identical overlapping meshes. Keep one to avoid z-fighting.
    chosen = bpy.data.objects.get("Chacha_Mixamo") or max(meshes, key=lambda o: len(o.data.vertices))
    chosen.name = "Chacha_Rigged_Mesh"
    chosen.data.name = "Chacha_Rigged_MeshData"
    for obj in list(meshes):
        if obj != chosen:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.objects.active = chosen
    chosen.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return chosen


def make_materials_unity_friendly(mesh_obj):
    for slot in mesh_obj.material_slots:
        mat = slot.material
        if not mat:
            continue
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            try:
                bsdf.inputs["Roughness"].default_value = 0.6
                bsdf.inputs["Specular"].default_value = 0.35
            except Exception:
                pass


def make_principled_material(name, color, roughness=0.58, specular=0.25):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Specular"].default_value = specular
    return mat


def assign_recovered_material_zones(mesh_obj, mn, mx):
    # The requested FBX carries UVs but no texture images or vertex colors. Assign material
    # zones from the existing Chacha mesh regions so Unity does not receive an all-gray avatar.
    height = mx.z - mn.z
    cx = (mn.x + mx.x) * 0.5
    cy = (mn.y + mx.y) * 0.5
    mats = {
        "skin": make_principled_material("Chacha_Skin", (0.78, 0.45, 0.34, 1.0), 0.62, 0.28),
        "turban": make_principled_material("Chacha_Turban_Red", (0.62, 0.025, 0.018, 1.0), 0.72, 0.22),
        "moustache": make_principled_material("Chacha_Moustache_White", (0.88, 0.86, 0.82, 1.0), 0.76, 0.18),
        "shirt": make_principled_material("Chacha_Shirt_White", (0.82, 0.84, 0.86, 1.0), 0.67, 0.18),
        "vest": make_principled_material("Chacha_Vest_Dark", (0.055, 0.055, 0.052, 1.0), 0.7, 0.2),
        "tie": make_principled_material("Chacha_Tie_Red", (0.72, 0.0, 0.0, 1.0), 0.55, 0.3),
        "pants": make_principled_material("Chacha_Pants_Navy", (0.06, 0.075, 0.13, 1.0), 0.68, 0.2),
        "shoe": make_principled_material("Chacha_Shoes_Black", (0.006, 0.006, 0.006, 1.0), 0.48, 0.38),
        "cane": make_principled_material("Chacha_Cane_Brown", (0.33, 0.13, 0.045, 1.0), 0.5, 0.34),
    }
    mesh_obj.data.materials.clear()
    material_index = {}
    for key, mat in mats.items():
        mesh_obj.data.materials.append(mat)
        material_index[key] = len(mesh_obj.data.materials) - 1

    def relz(z):
        return (z - mn.z) / height

    for poly in mesh_obj.data.polygons:
        center = mesh_obj.matrix_world @ poly.center
        rz = relz(center.z)
        rx = (center.x - cx) / height
        front = center.y < (cy - height * 0.018)
        cane_strip = center.x < (mn.x + height * 0.04) and rz < 0.52 and center.y < (cy + height * 0.08)

        key = "skin"
        if cane_strip:
            key = "cane"
        elif rz < 0.095:
            key = "shoe"
        elif rz < 0.43:
            key = "pants"
        elif rz < 0.69:
            if abs(rx) < 0.12:
                key = "vest"
                if front and abs(rx) < 0.025 and 0.52 < rz < 0.72:
                    key = "tie"
            else:
                key = "shirt"
        elif rz < 0.75:
            if abs(rx) < 0.115:
                key = "shirt"
            else:
                key = "shirt"
        elif rz < 0.71:
            key = "skin"
        elif rz < 0.785:
            key = "skin"
            if front and center.y < (cy - height * 0.085) and 0.025 < abs(rx) < 0.135:
                key = "moustache"
        elif rz < 0.835:
            key = "skin"
            if front and center.y < (cy - height * 0.09) and 0.045 < abs(rx) < 0.12 and rz < 0.805:
                key = "moustache"
        elif rz < 0.91:
            if front and center.y < (cy - height * 0.045) and abs(rx) < 0.115:
                key = "skin"
            else:
                key = "turban"
        else:
            key = "turban"

        if (rz > 0.77 and (center.x < cx - height * 0.065) and center.z < mx.z - height * 0.12):
            # Turban tail/scarf on the cane side.
            key = "turban"
        if rz > 0.91:
            key = "turban"

        poly.material_index = material_index[key]


def bounds(mesh_obj):
    pts = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def create_facial_shape_keys(mesh_obj, mn, mx):
    """Create lightweight Unity blendshapes from the existing facial mesh region."""
    mesh_obj.shape_key_add(name="Basis", from_mix=False)
    height = mx.z - mn.z
    cx = (mn.x + mx.x) * 0.5
    cy = (mn.y + mx.y) * 0.5

    def local_regions(co):
        rx = co.x - cx
        rz = (co.z - mn.z) / height
        front = co.y < cy - height * 0.045
        face = front and 0.765 < rz < 0.89 and abs(rx) < height * 0.16
        mouth = front and 0.765 < rz < 0.815 and abs(rx) < height * 0.075
        cheek = front and 0.79 < rz < 0.845 and height * 0.018 < abs(rx) < height * 0.14
        brow = front and 0.835 < rz < 0.875 and abs(rx) < height * 0.12
        return rx, rz, face, mouth, cheek, brow

    def add_key(name, transform):
        key = mesh_obj.shape_key_add(name=name, from_mix=False)
        key.slider_min = 0.0
        key.slider_max = 1.0
        for index, point in enumerate(key.data):
            base = mesh_obj.data.vertices[index].co
            rx, rz, face, mouth, cheek, brow = local_regions(base)
            point.co = base + transform(base, rx, rz, face, mouth, cheek, brow)
        return key

    # The model's large moustache hides fine lip detail. These deliberately use readable,
    # gentle face and moustache movement rather than attempting a detailed FACS reconstruction.
    add_key(
        "Face_Happy",
        lambda co, rx, rz, face, mouth, cheek, brow: Vector((
            (0.010 if rx > 0 else -0.010) if cheek else 0.0,
            -0.004 if face else 0.0,
            0.014 if cheek or (mouth and abs(rx) > height * 0.032) else 0.0,
        )),
    )
    add_key(
        "Face_Thinking",
        lambda co, rx, rz, face, mouth, cheek, brow: Vector((
            0.0,
            -0.003 if face else 0.0,
            0.012 if brow and rx > 0 else (-0.007 if mouth and rx < 0 else 0.0),
        )),
    )
    add_key(
        "Face_Surprised",
        lambda co, rx, rz, face, mouth, cheek, brow: Vector((
            0.0,
            -0.010 if mouth else (-0.003 if face else 0.0),
            (rz - 0.79) * 0.20 if mouth else (0.010 if brow else 0.0),
        )),
    )
    add_key(
        "Face_SadConfused",
        lambda co, rx, rz, face, mouth, cheek, brow: Vector((
            0.0,
            -0.003 if face else 0.0,
            (-0.014 if mouth and abs(rx) > height * 0.03 else (0.010 if brow and rx < 0 else 0.0)),
        )),
    )
    add_key(
        "Mouth_Open",
        lambda co, rx, rz, face, mouth, cheek, brow: Vector((
            0.0,
            -0.014 if mouth else 0.0,
            (0.79 - rz) * 0.36 if mouth else 0.0,
        )),
    )


def create_armature(mn, mx):
    height = mx.z - mn.z
    cx = (mn.x + mx.x) * 0.5
    cy = (mn.y + mx.y) * 0.5
    z = lambda f: mn.z + height * f

    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = bpy.context.object
    arm.name = "Chacha_Humanoid_Armature"
    arm.data.name = "Chacha_Humanoid_Skeleton"
    arm.show_in_front = True
    arm.data.display_type = "STICK"
    arm.data.pose_position = "POSE"

    eb = arm.data.edit_bones
    eb.remove(eb[0])

    def bone(name, head, tail, parent=None, connected=False):
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        b.roll = 0.0
        if parent:
            b.parent = eb[parent]
            b.use_connect = connected
        return b

    # Central chain, fitted to the current non-neutral pose.
    bone("Root", (cx, cy, z(0.03)), (cx, cy, z(0.48)))
    bone("Hips", (cx, cy, z(0.45)), (cx, cy, z(0.54)), "Root")
    bone("Spine", (cx, cy, z(0.54)), (cx, cy, z(0.64)), "Hips", True)
    bone("Chest", (cx, cy, z(0.64)), (cx, cy, z(0.73)), "Spine", True)
    bone("UpperChest", (cx, cy, z(0.73)), (cx, cy, z(0.78)), "Chest", True)
    bone("Neck", (cx, cy, z(0.78)), (cx + height * 0.015, cy, z(0.81)), "UpperChest", True)
    bone("Head", (cx + height * 0.015, cy, z(0.81)), (cx + height * 0.045, cy + height * 0.015, z(0.94)), "Neck", True)

    # Legs.
    hip_x = height * 0.055
    knee_x = height * 0.075
    ankle_x = height * 0.08
    toe_y = cy - height * 0.11
    foot_y = cy - height * 0.045
    for side, sgn in (("Left", 1), ("Right", -1)):
        bone(f"{side}UpperLeg", (cx + sgn * hip_x, cy, z(0.45)), (cx + sgn * knee_x, cy, z(0.25)), "Hips")
        bone(f"{side}LowerLeg", (cx + sgn * knee_x, cy, z(0.25)), (cx + sgn * ankle_x, cy, z(0.07)), f"{side}UpperLeg", True)
        bone(f"{side}Foot", (cx + sgn * ankle_x, cy, z(0.07)), (cx + sgn * ankle_x, foot_y, z(0.025)), f"{side}LowerLeg", True)
        bone(f"{side}Toes", (cx + sgn * ankle_x, foot_y, z(0.025)), (cx + sgn * ankle_x, toe_y, z(0.018)), f"{side}Foot", True)

    # Arms are placed in the existing acting pose, not a forced T-pose.
    arm_data = {
        "Left": {
            "shoulder": (cx + height * 0.055, cy, z(0.745)),
            "upper": (cx + height * 0.17, cy, z(0.67)),
            "lower": (cx + height * 0.165, cy - height * 0.025, z(0.48)),
            "hand": (cx + height * 0.135, cy - height * 0.045, z(0.40)),
        },
        "Right": {
            "shoulder": (cx - height * 0.055, cy, z(0.745)),
            "upper": (cx - height * 0.16, cy, z(0.62)),
            "lower": (cx - height * 0.18, cy - height * 0.03, z(0.39)),
            "hand": (cx - height * 0.17, cy - height * 0.04, z(0.33)),
        },
    }
    for side, pts in arm_data.items():
        bone(f"{side}Shoulder", (cx, cy, z(0.755)), pts["shoulder"], "UpperChest")
        bone(f"{side}UpperArm", pts["shoulder"], pts["upper"], f"{side}Shoulder", True)
        bone(f"{side}LowerArm", pts["upper"], pts["lower"], f"{side}UpperArm", True)
        bone(f"{side}Hand", pts["lower"], pts["hand"], f"{side}LowerArm", True)

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def point_segment_distance(p, a, b):
    ab = b - a
    denom = ab.length_squared
    if denom == 0:
        return (p - a).length
    t = max(0.0, min(1.0, (p - a).dot(ab) / denom))
    return (p - (a + ab * t)).length


def try_auto_weights(mesh_obj, arm):
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        return True, "Blender automatic weights completed."
    except Exception as exc:
        mesh_obj.parent = arm
        mod = mesh_obj.modifiers.new("Chacha_Armature", "ARMATURE")
        mod.object = arm
        return False, f"Automatic weights failed; deterministic spatial weights used. {exc}"


def ensure_armature_modifier(mesh_obj, arm):
    mod = next((m for m in mesh_obj.modifiers if m.type == "ARMATURE"), None)
    if not mod:
        mod = mesh_obj.modifiers.new("Chacha_Armature", "ARMATURE")
    mod.object = arm
    mesh_obj.parent = arm


def deterministic_weights(mesh_obj, arm, mn, mx):
    height = mx.z - mn.z
    cx = (mn.x + mx.x) * 0.5
    cy = (mn.y + mx.y) * 0.5
    for vg in list(mesh_obj.vertex_groups):
        mesh_obj.vertex_groups.remove(vg)
    groups = {b.name: mesh_obj.vertex_groups.new(name=b.name) for b in arm.data.bones}
    edit_like = {}
    for b in arm.data.bones:
        edit_like[b.name] = (arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local)

    weighted_counts = defaultdict(int)

    for v in mesh_obj.data.vertices:
        p = mesh_obj.matrix_world @ v.co
        relz = (p.z - mn.z) / height
        relx = (p.x - cx) / height
        weights = {}

        # Cane and cane-side fist: the cane is the extreme negative-X vertical strip.
        cane_strip = p.x < (mn.x + height * 0.035) and relz < 0.50 and p.y < (cy + height * 0.08)
        if cane_strip:
            weights["RightHand"] = 1.0
        elif relz > 0.78:
            weights["Head"] = 1.0
        elif relz > 0.735:
            weights["Head"] = (relz - 0.735) / 0.045
            weights["Neck"] = 1.0 - weights["Head"]
        elif relz > 0.66 and abs(relx) < 0.13:
            weights["UpperChest"] = (relz - 0.66) / 0.12
            weights["Chest"] = 1.0 - weights["UpperChest"]
        elif relz > 0.52 and abs(relx) < 0.16:
            weights["Chest"] = (relz - 0.52) / 0.14
            weights["Spine"] = 1.0 - weights["Chest"]
        elif relz > 0.38 and abs(relx) < 0.17:
            weights["Spine"] = max(0.0, min(1.0, (relz - 0.38) / 0.16))
            weights["Hips"] = 1.0 - weights["Spine"]
        elif relz <= 0.48 and abs(relx) < 0.18:
            side = "Left" if p.x >= cx else "Right"
            if relz < 0.08:
                weights[f"{side}Foot"] = 0.75
                weights[f"{side}LowerLeg"] = 0.25
            elif relz < 0.25:
                t = relz / 0.25
                weights[f"{side}LowerLeg"] = 0.75
                weights[f"{side}UpperLeg"] = 0.25 * t
                weights[f"{side}Foot"] = 0.25 * (1.0 - t)
            else:
                t = min(1.0, (relz - 0.25) / 0.23)
                weights[f"{side}UpperLeg"] = 0.85
                weights["Hips"] = 0.15 * t
        else:
            # Limb/body fallback: choose from the nearest plausible articulated bones.
            candidates = [
                "Hips", "Spine", "Chest", "UpperChest", "Neck", "Head",
                "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
                "RightUpperLeg", "RightLowerLeg", "RightFoot",
                "LeftUpperArm", "LeftLowerArm", "LeftHand",
                "RightUpperArm", "RightLowerArm", "RightHand",
            ]
            dists = []
            for name in candidates:
                a, b = edit_like[name]
                d = point_segment_distance(p, a, b)
                # Discourage cross-side limb stealing except near the torso.
                if "Left" in name and p.x < cx - height * 0.025:
                    d += height * 0.08
                if "Right" in name and p.x > cx + height * 0.025:
                    d += height * 0.08
                dists.append((d, name))
            dists.sort()
            selected = dists[:3]
            inv = [(1.0 / max(d, height * 0.018), name) for d, name in selected]
            total = sum(w for w, _ in inv)
            for w, name in inv:
                weights[name] = w / total

        total = sum(weights.values())
        if total <= 0:
            weights["Hips"] = 1.0
            total = 1.0
        for name, weight in weights.items():
            if weight > 0.001:
                groups[name].add([v.index], weight / total, "REPLACE")
                weighted_counts[name] += 1

    ensure_armature_modifier(mesh_obj, arm)
    return dict(weighted_counts)


def normalize_existing_weights(mesh_obj, arm, mn, mx):
    # Keep automatic weights where they exist, but lock the cane and high head/turban detail to stable bones.
    height = mx.z - mn.z
    cy = (mn.y + mx.y) * 0.5
    bone_names = {b.name for b in arm.data.bones}
    groups = {}
    for name in bone_names:
        groups[name] = mesh_obj.vertex_groups.get(name) or mesh_obj.vertex_groups.new(name=name)

    def clear_and_set(index, name):
        for vg in mesh_obj.vertex_groups:
            try:
                vg.remove([index])
            except RuntimeError:
                pass
        groups[name].add([index], 1.0, "REPLACE")

    for v in mesh_obj.data.vertices:
        p = mesh_obj.matrix_world @ v.co
        relz = (p.z - mn.z) / height
        cane_strip = p.x < (mn.x + height * 0.035) and relz < 0.50 and p.y < (cy + height * 0.08)
        if cane_strip:
            clear_and_set(v.index, "RightHand")
        elif relz > 0.80:
            clear_and_set(v.index, "Head")

    ensure_armature_modifier(mesh_obj, arm)


def create_action(arm, name, frame_range, keyframes):
    action = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = action
    start, end = frame_range
    bpy.context.scene.frame_start = min(bpy.context.scene.frame_start, start)
    bpy.context.scene.frame_end = max(bpy.context.scene.frame_end, end)

    # Every action starts from the same neutral pose so clips remain independent.
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0.0, 0.0, 0.0)

    for frame, poses in keyframes:
        bpy.context.scene.frame_set(frame)
        for bone_name, rot in poses.items():
            pb = arm.pose.bones.get(bone_name)
            if not pb:
                continue
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = Euler(tuple(math.radians(v) for v in rot), "XYZ")
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)
        for pb in arm.pose.bones:
            if pb.name not in poses:
                pb.rotation_mode = "XYZ"
                pb.keyframe_insert(data_path="rotation_euler", frame=frame)

    action.frame_start = start
    action.frame_end = end
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "SINE"
    return action


def create_animations(arm):
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 120

    actions = []
    actions.append(
        create_action(
            arm,
            "Idle_Breathing",
            (1, 60),
            [
                (1, {"Chest": (0, 0, 0), "UpperChest": (0, 0, 0), "Head": (0, 0, 0)}),
                (30, {"Chest": (-2.0, 0, 0.6), "UpperChest": (-2.5, 0, 0.8), "Head": (0.8, 0, -0.4)}),
                (60, {"Chest": (0, 0, 0), "UpperChest": (0, 0, 0), "Head": (0, 0, 0)}),
            ],
        )
    )
    actions.append(
        create_action(
            arm,
            "Talking_UpperBody",
            (1, 72),
            [
                (1, {"Chest": (0, 0, 0), "Head": (0, 0, 0), "LeftLowerArm": (0, 0, 0)}),
                (18, {"Chest": (-1.5, 0, -2.0), "Head": (1.5, 0, 2.0), "LeftLowerArm": (-4, 2, 4)}),
                (36, {"Chest": (1.0, 0, 1.5), "Head": (-1.0, 0, -1.5), "LeftLowerArm": (2, -2, -3)}),
                (54, {"Chest": (-1.0, 0, -1.0), "Head": (1.0, 0, 1.0), "LeftLowerArm": (-3, 1, 2)}),
                (72, {"Chest": (0, 0, 0), "Head": (0, 0, 0), "LeftLowerArm": (0, 0, 0)}),
            ],
        )
    )
    actions.append(
        create_action(
            arm,
            "Head_Nod",
            (1, 48),
            [
                (1, {"Neck": (0, 0, 0), "Head": (0, 0, 0)}),
                (16, {"Neck": (4, 0, 0), "Head": (10, 0, 0)}),
                (32, {"Neck": (-2, 0, 0), "Head": (-5, 0, 0)}),
                (48, {"Neck": (0, 0, 0), "Head": (0, 0, 0)}),
            ],
        )
    )
    actions.append(
        create_action(
            arm,
            "Head_Turn",
            (1, 60),
            [
                (1, {"Neck": (0, 0, 0), "Head": (0, 0, 0)}),
                (20, {"Neck": (0, 5, 0), "Head": (0, 10, 0)}),
                (36, {"Neck": (0, -2, 0), "Head": (0, -5, 0)}),
                (60, {"Neck": (0, 0, 0), "Head": (0, 0, 0)}),
            ],
        )
    )
    actions.append(
        create_action(
            arm,
            "Simple_Hand_Gesture",
            (1, 72),
            [
                (1, {"LeftUpperArm": (0, 0, 0), "LeftLowerArm": (0, 0, 0), "LeftHand": (0, 0, 0)}),
                (24, {"LeftUpperArm": (-8, -2, 4), "LeftLowerArm": (-18, 8, 4), "LeftHand": (0, 8, -10)}),
                (48, {"LeftUpperArm": (-4, 2, -5), "LeftLowerArm": (-9, -8, -2), "LeftHand": (0, -8, 8)}),
                (72, {"LeftUpperArm": (0, 0, 0), "LeftLowerArm": (0, 0, 0), "LeftHand": (0, 0, 0)}),
            ],
        )
    )
    actions.append(
        create_action(
            arm,
            "Happy_Reaction",
            (1, 60),
            [
                (1, {"Chest": (0, 0, 0), "UpperChest": (0, 0, 0), "Head": (0, 0, 0), "LeftUpperArm": (0, 0, 0), "LeftLowerArm": (0, 0, 0)}),
                (18, {"Chest": (-2, 0, -1), "UpperChest": (-2, 0, -1), "Head": (-4, 0, 2), "LeftUpperArm": (-7, -2, 3), "LeftLowerArm": (-14, 6, 3)}),
                (36, {"Chest": (-1, 0, 1), "UpperChest": (-1, 0, 1), "Head": (2, 0, -2), "LeftUpperArm": (-4, 2, -4), "LeftLowerArm": (-8, -5, -2)}),
                (60, {"Chest": (0, 0, 0), "UpperChest": (0, 0, 0), "Head": (0, 0, 0), "LeftUpperArm": (0, 0, 0), "LeftLowerArm": (0, 0, 0)}),
            ],
        )
    )
    actions.append(
        create_action(
            arm,
            "Thinking_Reaction",
            (1, 60),
            [
                (1, {"Chest": (0, 0, 0), "Neck": (0, 0, 0), "Head": (0, 0, 0), "LeftUpperArm": (0, 0, 0), "LeftLowerArm": (0, 0, 0), "LeftHand": (0, 0, 0)}),
                (18, {"Chest": (2, 0, 2), "Neck": (0, 0, -3), "Head": (5, 0, -6), "LeftUpperArm": (-8, 0, 3), "LeftLowerArm": (-20, 5, -2), "LeftHand": (0, 0, 8)}),
                (38, {"Chest": (1, 0, 1), "Neck": (0, 0, -2), "Head": (4, 0, -5), "LeftUpperArm": (-6, 1, 2), "LeftLowerArm": (-16, 4, -1), "LeftHand": (0, 0, 6)}),
                (60, {"Chest": (0, 0, 0), "Neck": (0, 0, 0), "Head": (0, 0, 0), "LeftUpperArm": (0, 0, 0), "LeftLowerArm": (0, 0, 0), "LeftHand": (0, 0, 0)}),
            ],
        )
    )

    # Store all actions as NLA strips so Blender and Unity FBX import can see separate clips.
    arm.animation_data.action = None
    for action in actions:
        track = arm.animation_data.nla_tracks.new()
        track.name = action.name
        strip = track.strips.new(action.name, int(action.frame_start), action)
        strip.frame_end = action.frame_end
        strip.use_auto_blend = False
        action.use_fake_user = True
    arm.animation_data.action = actions[0]
    return actions


def add_scene_helpers(mn, mx):
    bpy.ops.object.light_add(type="AREA", location=(0.0, -2.8, mx.z + 0.8))
    light = bpy.context.object
    light.name = "Rig_Check_Key_Light"
    light.data.energy = 500
    light.data.size = 4

    bpy.ops.object.camera_add(location=(0.0, -3.4, (mn.z + mx.z) * 0.52), rotation=(math.radians(76), 0, 0))
    bpy.context.scene.camera = bpy.context.object


def evaluated_bbox(mesh_obj, arm, action, frame):
    arm.animation_data.action = action
    bpy.context.scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = mesh_obj.evaluated_get(depsgraph)
    pts = [obj_eval.matrix_world @ Vector(corner) for corner in obj_eval.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def verify(mesh_obj, arm, actions, auto_weight_note):
    reports = {}
    reports["armature_exists"] = arm.type == "ARMATURE" and len(arm.data.bones) >= 20
    reports["mesh_parented_to_armature"] = mesh_obj.parent == arm
    reports["armature_modifier"] = any(m.type == "ARMATURE" and m.object == arm for m in mesh_obj.modifiers)
    reports["vertex_groups"] = len(mesh_obj.vertex_groups)
    reports["materials"] = [slot.material.name for slot in mesh_obj.material_slots if slot.material]
    reports["shape_keys"] = [key.name for key in mesh_obj.data.shape_keys.key_blocks] if mesh_obj.data.shape_keys else []
    reports["actions"] = {a.name: list(a.frame_range) for a in actions}
    reports["weighting_method"] = auto_weight_note

    for action_name in ("Idle_Breathing", "Talking_UpperBody", "Head_Nod", "Head_Turn", "Simple_Hand_Gesture", "Happy_Reaction", "Thinking_Reaction"):
        action = bpy.data.actions[action_name]
        start, end = [int(v) for v in action.frame_range]
        a0, b0 = evaluated_bbox(mesh_obj, arm, action, start)
        a1, b1 = evaluated_bbox(mesh_obj, arm, action, (start + end) // 2)
        reports[f"{action_name}_bbox_start"] = [list(a0), list(b0)]
        reports[f"{action_name}_bbox_mid"] = [list(a1), list(b1)]
        reports[f"{action_name}_deforms"] = max((a0 - a1).length, (b0 - b1).length) > 0.002

    reports["unity_export_settings"] = {
        "format": "FBX",
        "path_mode": "COPY",
        "embed_textures": True,
        "add_leaf_bones": False,
        "bake_anim": True,
        "primary_bone_axis": "Y",
        "secondary_bone_axis": "X",
    }

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)
    return reports


def export_unity_fbx(mesh_obj, arm):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(
        filepath=OUT_FBX,
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z",
        axis_up="Y",
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        use_armature_deform_only=True,
        bake_anim=True,
        bake_anim_use_all_actions=True,
        bake_anim_use_nla_strips=True,
        bake_anim_force_startend_keying=True,
        path_mode="COPY",
        embed_textures=True,
    )


def main():
    clear_scene()
    mesh_obj = import_character()
    make_materials_unity_friendly(mesh_obj)
    mn, mx = bounds(mesh_obj)
    assign_recovered_material_zones(mesh_obj, mn, mx)
    create_facial_shape_keys(mesh_obj, mn, mx)
    arm = create_armature(mn, mx)

    auto_ok, auto_note = try_auto_weights(mesh_obj, arm)
    if auto_ok and len(mesh_obj.vertex_groups) >= 10:
        normalize_existing_weights(mesh_obj, arm, mn, mx)
    else:
        counts = deterministic_weights(mesh_obj, arm, mn, mx)
        auto_note += f" Weighted groups: {counts}"

    actions = create_animations(arm)
    add_scene_helpers(mn, mx)
    report = verify(mesh_obj, arm, actions, auto_note)

    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    export_unity_fbx(mesh_obj, arm)
    print(json.dumps(report, indent=2))
    print(f"Saved {OUT_BLEND}")
    print(f"Exported {OUT_FBX}")


if __name__ == "__main__":
    main()
