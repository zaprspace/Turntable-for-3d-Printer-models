import bpy
import os
import math
import sys
import traceback

# ------------------------------------------------------------
# ---- PARSE ARGUMENTS FROM GUI ----
# Expected order:
# blender -b -P <script> "<input_folder>" "<output_folder>" <r> <g> <b> <camera_height_pct>
# ------------------------------------------------------------

try:
    # Only take arguments after the script filename
    args = sys.argv[sys.argv.index(__file__) + 1:]

    if len(args) < 6:
        print("\nERROR: Not enough arguments passed to script!")
        print("Expected: input_folder output_folder r g b camera_height_pct")
        sys.exit(1)

    INPUT_FOLDER    = args[0]
    OUTPUT_FOLDER   = args[1]
    MAT_R           = float(args[2])
    MAT_G           = float(args[3])
    MAT_B           = float(args[4])
    CAM_HEIGHT_PCT  = float(args[5])

except Exception as e:
    print("Failed to parse arguments:", e)
    sys.exit(1)

# ------------------------------------------------------------
# ---- SETTINGS ----
# ------------------------------------------------------------
FRAMES = 180
FPS = 30
RES_X = 1080
RES_Y = 1080

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ------------------------------------------------------------
# ---- RESET SCENE ----
# ------------------------------------------------------------
def reset_camera_and_lights():
    """Remove all cameras, lights, and empties."""
    for obj in list(bpy.data.objects):
        if obj.type in {'CAMERA', 'LIGHT', 'EMPTY'}:
            bpy.data.objects.remove(obj, do_unlink=True)

def clean_scene():
    """Delete all objects and reset scene."""
    reset_camera_and_lights()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

# ------------------------------------------------------------
# ---- BACKGROUND ----
# ------------------------------------------------------------
def setup_background(r=0.01, g=0.01, b=0.01):
    world = bpy.data.worlds.get("World")
    if world is None:
        world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world

    world.use_nodes = True
    tree = world.node_tree
    nodes = tree.nodes
    links = tree.links

    nodes.clear()

    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (r, g, b, 1)
    bg.inputs["Strength"].default_value = 1.0

    out = nodes.new("ShaderNodeOutputWorld")
    links.new(bg.outputs["Background"], out.inputs["Surface"])

# ------------------------------------------------------------
# ---- IMPORT STL ----
# ------------------------------------------------------------
def import_stl(path):
    result = bpy.ops.wm.stl_import(filepath=path)
    if "FINISHED" not in result:
        raise RuntimeError(f"Failed to import STL: {path}")
    return [o for o in bpy.context.scene.objects if o.type == 'MESH']

# ------------------------------------------------------------
# ---- SCALE & CENTER ----
# ------------------------------------------------------------
def auto_scale_center(meshes):
    if not meshes:
        raise RuntimeError("No meshes found after import")

    # Join multiple meshes
    if len(meshes) > 1:
        bpy.context.view_layer.objects.active = meshes[0]
        for o in meshes:
            o.select_set(True)
        bpy.ops.object.join()
        obj = bpy.context.active_object
    else:
        obj = meshes[0]
        bpy.context.view_layer.objects.active = obj

    obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    obj.location = (0, 0, 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Scale largest dimension to 1 Blender unit
    max_dim = max(obj.dimensions)
    if max_dim > 0:
        obj.scale = (1/max_dim,) * 3
        bpy.context.view_layer.update()
        bpy.ops.object.transform_apply(scale=True)

    bpy.ops.object.shade_smooth()
    return obj

# ------------------------------------------------------------
# ---- MATERIAL ----
# ------------------------------------------------------------
def set_material(obj, r, g, b):
    """Simple glossy material with GUI-selected RGB."""
    mat = bpy.data.materials.new("ModelMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1)
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.location = (0, 0)

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (200, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    obj.data.materials.clear()
    obj.data.materials.append(mat)

# ------------------------------------------------------------
# ---- CAMERA ----
# ------------------------------------------------------------
def setup_camera(obj, height_pct=0.6):
    """Camera height relative to model height."""
    height = obj.dimensions.z
    cam_z = height * height_pct

    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    dist = max(obj.dimensions) * 1.1
    cam.location = (dist, -dist, cam_z)

    target = bpy.data.objects.new("Target", None)
    bpy.context.scene.collection.objects.link(target)
    target.location = (0, 0, 0)

    con = cam.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'

    return cam

# ------------------------------------------------------------
# ---- LIGHTS ----
# ------------------------------------------------------------
def setup_lights_follow_camera(cam):
    # Key light
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 0))
    key = bpy.context.active_object
    key.data.energy = 250
    key.data.size = 4
    key.parent = cam
    key.location = (2, -3, 1.5)

    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 0))
    fill = bpy.context.active_object
    fill.data.energy = 90
    fill.data.size = 5
    fill.parent = cam
    fill.location = (-2, -4, 1)

    # Rim light
    bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
    rim = bpy.context.active_object
    rim.data.energy = 120
    rim.parent = cam
    rim.location = (0, 4, 2.5)

# ------------------------------------------------------------
# ---- ANIMATION ----
# ------------------------------------------------------------
def animate_turntable(cam):
    rotor = bpy.data.objects.new("Rotor", None)
    bpy.context.scene.collection.objects.link(rotor)

    rotor.rotation_euler = (0, 0, 0)
    rotor.keyframe_insert("rotation_euler", frame=1)
    rotor.rotation_euler = (0, 0, math.radians(360))
    rotor.keyframe_insert("rotation_euler", frame=FRAMES)

    cam.parent = rotor
    bpy.context.scene.frame_end = FRAMES

# ------------------------------------------------------------
# ---- RENDER SETTINGS ----
# ------------------------------------------------------------
def setup_render(out_path):
    scene = bpy.context.scene
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.fps = FPS
    scene.render.filepath = out_path
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'

# ------------------------------------------------------------
# ---- PROCESS SINGLE STL ----
# ------------------------------------------------------------
def process_stl(stl_path):
    name = os.path.splitext(os.path.basename(stl_path))[0]
    out_path = os.path.join(OUTPUT_FOLDER, name)

    print(f"\nProcessing {name}...")

    clean_scene()
    setup_background()
    meshes = import_stl(stl_path)
    obj = auto_scale_center(meshes)
    set_material(obj, MAT_R, MAT_G, MAT_B)

    cam = setup_camera(obj, CAM_HEIGHT_PCT)
    setup_lights_follow_camera(cam)
    animate_turntable(cam)
    setup_render(out_path)

    bpy.ops.render.render(animation=True)
    print("Saved:", out_path + ".mp4")

# ------------------------------------------------------------
# ---- BATCH LOOP ----
# ------------------------------------------------------------
def main():
    if not os.path.exists(INPUT_FOLDER):
        print(f"ERROR: Input folder not found: {INPUT_FOLDER}")
        return

    for f in os.listdir(INPUT_FOLDER):
        if f.lower().endswith(".stl"):
            stl_path = os.path.join(INPUT_FOLDER, f)
            try:
                process_stl(stl_path)
            except Exception:
                print("\nFAILED:", f)
                print(traceback.format_exc())

    print("\nDONE — all models rendered.")

# Run
main()
