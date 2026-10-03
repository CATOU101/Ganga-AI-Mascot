"""Integration and asset validation tests for Chacha New 3D Avatar."""

from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
AVATAR_NEW_DIR = ROOT_DIR / "avatar" / "Chacha_New"
MEMBER2_DIR = ROOT_DIR / "avatar" / "Member2_Chacha"

EXPECTED_28_ANIMATIONS = [
    "Acknowledging",
    "Agreeing",
    "Angry_Gesture",
    "Being_Strangled",
    "Catwalk_Twist_R_To_Walk_180",
    "Clapping",
    "Clapping_1",
    "Defeat_Idle",
    "Drinking",
    "Happy_Idle",
    "Happy_Walk",
    "Idle",
    "Laughing_1",
    "Looking",
    "Male_Standing_Pose",
    "Nervously_Look_Around",
    "Patting",
    "Pointing",
    "Pointing_Forward",
    "Praying",
    "Quick_Formal_Bow",
    "Sad_Walk",
    "Swagger_Walk",
    "Talking",
    "Unarmed_Idle",
    "Waving",
    "Waving_Gesture",
    "Yelling",
]


def test_chacha_new_glb_exists_and_readable():
    glb_path = AVATAR_NEW_DIR / "Chacha_New.glb"
    assert glb_path.exists(), f"Chacha_New.glb not found at {glb_path}"
    file_size_mb = glb_path.stat().st_size / (1024 * 1024)
    # Verify non-empty and within plausible bounds for web-optimized 3D asset (1 MB to 50 MB)
    assert file_size_mb > 1.0, f"Chacha_New.glb unexpectedly small or empty: {file_size_mb:.2f} MB"
    assert file_size_mb < 50.0, f"Chacha_New.glb unexpectedly large: {file_size_mb:.2f} MB"


def test_existing_member2_avatar_preserved():
    member2_glb = MEMBER2_DIR / "Chacha_Master.glb"
    assert member2_glb.exists(), f"Member2 Chacha_Master.glb missing at {member2_glb}"
    file_size_mb = member2_glb.stat().st_size / (1024 * 1024)
    assert file_size_mb > 100.0, f"Member2 Chacha_Master.glb file size altered: {file_size_mb:.2f} MB"


def test_chacha_new_glb_internal_structure():
    glb_path = AVATAR_NEW_DIR / "Chacha_New.glb"
    with open(glb_path, "rb") as f:
        magic, version, length = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", "File magic header is not glTF"
        assert version == 2, f"Expected glTF version 2, got {version}"
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        assert chunk_type == 0x4E4F534A, "First chunk is not JSON (JSON = 0x4E4F534A)"
        json_bytes = f.read(chunk_len)
        data = json.loads(json_bytes.decode("utf-8"))

    # Animations count and names
    anims = [a["name"] for a in data.get("animations", [])]
    assert len(anims) == 28, f"Expected 28 animation clips, got {len(anims)}"
    assert set(anims) == set(EXPECTED_28_ANIMATIONS), "Animation clip names mismatch"

    # Mesh and bones
    meshes = data.get("meshes", [])
    assert len(meshes) == 1, f"Expected 1 mesh, found {len(meshes)}"
    prim = meshes[0]["primitives"][0]
    # Verify no morph targets exist
    targets = prim.get("targets", [])
    assert len(targets) == 3, f"Expected 0 morph targets, found {len(targets)}"

    # Skins/armature
    skins = data.get("skins", [])
    assert len(skins) == 1, "Expected 1 skin armature"
    joints = skins[0].get("joints", [])
    assert len(joints) == 65, f"Expected 65 bones in Mixamo skeleton, got {len(joints)}"

    # Embedded textures
    images = data.get("images", [])
    assert len(images) >= 3, f"Expected at least 3 embedded PBR texture images, got {len(images)}"


def test_mascot_js_configuration():
    mascot_js = ROOT_DIR / "avatar" / "mascot.js"
    assert mascot_js.exists(), "mascot.js not found"
    content = mascot_js.read_text(encoding="utf-8")

    # Verify model path
    assert "Chacha_New/Chacha_New.glb" in content, "Model path to Chacha_New.glb missing"
    assert "playAction('Idle')" in content, "Default idle action missing"

    # Verify semantic gesture mappings
    expected_mappings = [
        "'idle': 'Idle'",
        "'nod': 'Acknowledging'",
        "'point': 'Pointing'",
        "'explaining': 'Pointing_Forward'",
        "'waving': 'Waving'",
        "'thankful': 'Praying'",
        "'laughing': 'Laughing_1'",
        "'thinking': 'Looking'",
        "'shaking_hands': 'Patting'",
    ]
    for mapping in expected_mappings:
        assert mapping in content, f"Expected gesture mapping {mapping} missing from mascot.js"

    # Verify safe fallback guard for morph targets
    assert "hasMorphTargets" in content, "hasMorphTargets safe guard missing from mascot.js"


def test_index_html_ui_identifiers():
    index_html = ROOT_DIR / "avatar" / "index.html"
    assert index_html.exists(), "index.html not found"
    content = index_html.read_text(encoding="utf-8")

    assert "Chacha New" in content, "UI identifier for Chacha New missing in index.html"
    assert "mascot.js" in content, "mascot.js script tag missing in index.html"
    assert "app.js" in content, "app.js script tag missing in index.html"


def test_zero_git_deletions():
    res = subprocess.run(
        ["git", "diff", "--name-status"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    lines = res.stdout.strip().splitlines()
    deleted = [l for l in lines if l.startswith("D\t")]
    assert len(deleted) == 0, f"Strict non-destructive rule violated! Deleted files: {deleted}"