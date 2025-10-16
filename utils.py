import bpy
import bmesh
import math
import numpy as np
import mathutils
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from bpy.app.handlers import persistent

# --- translate ---
def translate(text, *args, **kwargs):
    if bpy.context.preferences.view.use_translate_interface:
        translated_text = bpy.app.translations.pgettext(text)
        return translated_text.format(*args, **kwargs)
    return text.format(*args, **kwargs)

# --- format ---
def format_distance(context, distance_m):
    settings = context.scene.unit_settings
    if settings.system == 'METRIC':
        return f"{distance_m / 1000.0:.2f} km" if distance_m >= 1000 else f"{distance_m:.2f} m"
    elif settings.system == 'IMPERIAL':
        distance_ft = distance_m * 3.28084
        return f"{distance_ft / 5280.0:.2f} mi" if distance_ft >= 5280 else f"{distance_ft:.2f} ft"
    else:
        return f"{distance_m:.2f}"

def format_shutter_speed(speed):
    if speed <= 0: return "0s"
    if speed >= 0.5: return f"{speed:.3f}s"
    reciprocal = 1.0 / speed
    if abs(reciprocal - round(reciprocal)) < 0.01:
        return f"1/{round(reciprocal)}s"
    return f"{speed:.6g}s"
    
def create_empty_at_distance(context, distance, name="Distance_Empty"):
    cam = context.active_object
    if not cam or cam.type != 'CAMERA': return translate("Active object is not a camera.")
    if distance <= 0: return translate("Result has not been calculated yet.")
    cam_matrix = cam.matrix_world
    cam_location = cam_matrix.translation
    forward_vector = -cam_matrix.col[2].xyz.normalized()
    empty_location = cam_location + forward_vector * distance
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=empty_location)
    new_empty = context.active_object
    new_empty.name = name
    new_empty.empty_display_size = distance / 10 if distance > 0 else 1.0
    return translate("Created Empty at distance.")

# --- preset list ---
APERTURE_VALUES = [1.0, 1.2, 1.4, 1.8, 2.0, 2.8, 4.0, 5.6, 8.0, 11.0, 16.0, 22.0]
APERTURE_ITEMS = [('CUSTOM', "Custom", "")] + [(str(s), f"{s}", "") for s in APERTURE_VALUES]
SHUTTER_ITEMS = [('CUSTOM', "Custom", "")] + [(str(s), f"1/{round(1/s)}s", "") for s in [1, 1/2, 1/4, 1/8, 1/15, 1/30, 1/50, 1/60, 1/100, 1/125, 1/250, 1/500, 1/1000, 1/2000, 1/4000, 1/8000]]
ISO_ITEMS = [('CUSTOM', "Custom", "")] + [(str(i), f"ISO {i}", "") for i in [100, 200, 400, 800, 1600, 3200, 6400]]
ND_ITEMS = [('1', "None (0 Stop)", ""), ('CUSTOM', "Custom", "")] + [(str(2**i), f"ND{2**i} ({i} Stop)", "") for i in range(1, 11)]

def perform_lux_measurement(context, sensor_obj):
    if not sensor_obj:
        print("Sensor object not provided to measurement function.")
        return None
    original_scene = context.scene
    original_window_scene = context.window.scene
    original_engine = original_scene.render.engine
    temp_scene = bpy.data.scenes.new(name="SA_Toolkit_Temp_Scene")
    for obj in original_scene.objects:
        temp_scene.collection.objects.link(obj)
    temp_scene.world = original_scene.world
    context.window.scene = temp_scene
    
    temp_plane, temp_camera, temp_mat, temp_comp_tree = None, None, None, None
    final_lux = None
    try:
        sensor_matrix = sensor_obj.matrix_world
        sensor_location = sensor_matrix.translation
        plane_normal = sensor_matrix.to_3x3() @ mathutils.Vector((0.0, 0.0, 1.0)); plane_normal.normalize()
        bpy.ops.mesh.primitive_plane_add(size=0.01, enter_editmode=False, align='WORLD', location=sensor_location)
        temp_plane = context.active_object; temp_plane.name = "Temp_luxmeter_Plane"; temp_plane.rotation_euler = sensor_obj.rotation_euler
        temp_mat = bpy.data.materials.new(name="Temp_White_Material"); temp_mat.use_nodes = True
        nodes = temp_mat.node_tree.nodes; nodes.clear()
        node_diffuse = nodes.new(type='ShaderNodeBsdfDiffuse'); node_diffuse.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1)
        node_output = nodes.new(type='ShaderNodeOutputMaterial')
        temp_mat.node_tree.links.new(node_diffuse.outputs['BSDF'], node_output.inputs['Surface'])
        temp_plane.data.materials.append(temp_mat)
        camera_location = sensor_location + plane_normal * 0.01
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_location)
        temp_camera = context.active_object; temp_camera.name = "Temp_luxmeter_Camera"
        temp_camera.data.type = 'ORTHO'; temp_camera.data.ortho_scale = 0.01; temp_camera.data.clip_start = 0.001
        constraint = temp_camera.constraints.new(type='TRACK_TO'); constraint.target = temp_plane; constraint.track_axis = 'TRACK_NEGATIVE_Z'; constraint.up_axis = 'UP_Y'
        temp_scene.camera = temp_camera
        temp_scene.render.engine = 'CYCLES'
        temp_scene.render.resolution_x = 16
        temp_scene.render.resolution_y = 16
        temp_scene.cycles.samples = 256
        temp_scene.cycles.use_denoising = False
        temp_scene.render.film_transparent = True
        
        tree = None
        if bpy.app.version >= (5, 0, 0):
            # Blender 5.0 later: 
            # 1. Temporarily created as an independent node group
            comp_name = "SA_Toolkit_Temp_Compositor"
            temp_comp_tree = bpy.data.node_groups.new(comp_name, 'CompositorNodeTree')
            
            # 2. Link node groups to the scene using the correct attribute 'compositing_node_group'
            temp_scene.compositing_node_group = temp_comp_tree
            
            tree = temp_comp_tree
        else:
            # Blender 4.x earlier:
            temp_scene.use_nodes = True
            tree = temp_scene.node_tree
        
        if not tree:
            print("Analysis Toolkit Error: Could not get or create a compositor node tree for the temporary scene.")
            return None
            
        tree.nodes.clear()
        render_layers_node = tree.nodes.new(type='CompositorNodeRLayers')
        viewer_node = tree.nodes.new(type='CompositorNodeViewer')
        tree.links.new(render_layers_node.outputs[0], viewer_node.inputs[0])
        bpy.ops.render.render(scene=temp_scene.name, write_still=False)
        viewer_image = bpy.data.images.get('Viewer Node')
        if viewer_image is None or not viewer_image.has_data: return None
        temp_image = bpy.data.images.new("SA_Toolkit_Temp_Result", width=16, height=16, alpha=True, float_buffer=True)
        temp_image.pixels[:] = viewer_image.pixels[:]
        pixels = np.array(temp_image.pixels[:])
        bpy.data.images.remove(temp_image)
        if pixels.size == 0: return None
        pixels = pixels.reshape((16, 16, 4)); rgb_pixels = pixels[:, :, :3]
        luminance_values = 0.2126 * rgb_pixels[:, :, 0] + 0.7152 * rgb_pixels[:, :, 1] + 0.0722 * rgb_pixels[:, :, 2]
        average_luminance = np.mean(luminance_values)
        measured_lux = average_luminance * math.pi
        
        final_lux = measured_lux * 1.03
        
    finally:
        original_scene.render.engine = original_engine
        if original_window_scene:
            context.window.scene = original_window_scene
        if temp_plane: bpy.data.objects.remove(temp_plane, do_unlink=True)
        if temp_camera: bpy.data.objects.remove(temp_camera, do_unlink=True)
        if temp_mat: bpy.data.materials.remove(temp_mat)
        
        if temp_comp_tree:
            bpy.data.node_groups.remove(temp_comp_tree, do_unlink=True)

        if temp_scene: bpy.data.scenes.remove(temp_scene)
    return final_lux

def on_ev_compensation_change(self, context):
    scene = context.scene
    
    # 測定結果がなければ何もしない
    if not scene.lux_meter_results:
        return

    new_ev_comp = scene.lux_meter_ev_compensation
    lux_values = []

    for result in scene.lux_meter_results:

        compensated_lux = result.raw_lux * (2**new_ev_comp)
        result.lux = compensated_lux
        lux_values.append(compensated_lux)

    if lux_values:
        scene.lux_meter_avg_lux = sum(lux_values) / len(lux_values)
        scene.lux_meter_min_lux = min(lux_values)
        scene.lux_meter_max_lux = max(lux_values)



_speedo_cache = {}

def get_converted_speed(speed_ms, unit):
    if unit == 'MS':
        return speed_ms, "m/s"
    elif unit == 'KMH':
        return speed_ms * 3.6, "km/h"
    elif unit == 'MMIN':
        return speed_ms * 60, "m/min"
    elif unit == 'FTS':
        return speed_ms * 3.28084, "ft/s"
    elif unit == 'MPH':
        return speed_ms * 2.23694, "mph"
    elif unit == 'KNOT':
        return speed_ms * 1.94384, "kn"
    elif unit == 'MACH':
        return speed_ms / 343.0, "Mach"
    return 0.0, ""


def speedo_realtime_update(scene):
    global _speedo_cache
    
    s = scene.speedometer_props
    if not hasattr(scene, "speedometer_props") or s.mode != 'INSTANT' or not s.target_obj:
        _speedo_cache.clear()
        return

    target_obj = s.target_obj
    obj_id = target_obj.name_full

    if not list(_speedo_cache.keys()) or list(_speedo_cache.keys())[0] != obj_id:
        _speedo_cache.clear()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = target_obj.evaluated_get(depsgraph)
    pos_current = obj_eval.matrix_world.translation.copy()
    frame_current = scene.frame_current

    last_pos, last_frame = _speedo_cache.get(obj_id, (None, None))

    speed_ms = 0.0
    if last_pos is not None and (frame_current == last_frame + 1 or frame_current == last_frame - 1):
        distance = (pos_current - last_pos).length * s.scale_factor
        fps = scene.render.fps / scene.render.fps_base
        time_delta = 1.0 / fps if fps > 0 else 1.0
        speed_ms = distance / time_delta
    
    _speedo_cache[obj_id] = (pos_current, frame_current)

    s.speed_ms = speed_ms


_CONV_UPDATE_LOCK = False
def imperial_to_metric(self, context):
    global _CONV_UPDATE_LOCK
    if _CONV_UPDATE_LOCK: return
    try:
        _CONV_UPDATE_LOCK = True
        total_inches = 0
        if self.conv_imperial_unit == 'FT': total_inches = self.conv_feet * 12
        elif self.conv_imperial_unit == 'FT_IN': total_inches = (self.conv_feet * 12) + self.conv_inches
        elif self.conv_imperial_unit == 'IN': total_inches = self.conv_inches
        cm = total_inches * 2.54
        if self.conv_metric_unit == 'MM': self.conv_metric_val = cm * 10
        elif self.conv_metric_unit == 'CM': self.conv_metric_val = cm
        elif self.conv_metric_unit == 'M': self.conv_metric_val = cm / 100
    finally: _CONV_UPDATE_LOCK = False

def metric_to_imperial(self, context):
    global _CONV_UPDATE_LOCK
    if _CONV_UPDATE_LOCK: return
    try:
        _CONV_UPDATE_LOCK = True
        cm = 0
        if self.conv_metric_unit == 'MM': cm = self.conv_metric_val / 10
        elif self.conv_metric_unit == 'CM': cm = self.conv_metric_val
        elif self.conv_metric_unit == 'M': cm = self.conv_metric_val * 100
        total_inches = cm / 2.54
        if self.conv_imperial_unit == 'FT': self.conv_feet = total_inches / 12
        elif self.conv_imperial_unit == 'FT_IN':
            self.conv_feet = math.floor(total_inches / 12)
            self.conv_inches = total_inches % 12
        elif self.conv_imperial_unit == 'IN': self.conv_inches = total_inches
    finally: _CONV_UPDATE_LOCK = False

# --- EV Calculation Update Function ---
_EV_UPDATE_LOCK = False

def update_ev_calculation(self, context):
    global _EV_UPDATE_LOCK
    if _EV_UPDATE_LOCK: return
    try:
        _EV_UPDATE_LOCK = True
        
        if self.solve_target != 'APERTURE' and self.aperture_preset != 'CUSTOM':
            self.aperture = float(self.aperture_preset)
        
        if self.solve_target != 'SHUTTER' and self.shutter_speed_preset != 'CUSTOM':
            self.shutter_speed = float(self.shutter_speed_preset)

        if self.solve_target != 'ISO' and self.iso_preset != 'CUSTOM':
            self.iso = float(self.iso_preset)

        if self.solve_target != 'ND' and self.nd_filter_preset != 'CUSTOM':
            self.nd_filter_stops = math.log2(float(self.nd_filter_preset)) if float(self.nd_filter_preset) > 0 else 0
        
        t = self.shutter_speed if self.mode == 'STILLS' else \
            (self.shutter_angle / (2 * math.pi)) / self.fps if self.fps > 0 else 0
        N, iso, ev100, nd = self.aperture, self.iso, self.ev_value, self.nd_filter_stops
        
        if self.solve_target == 'APERTURE':
            if t > 0 and iso > 0: self.aperture = math.sqrt(t * (2**(ev100 - nd)) * (iso / 100.0))
        elif self.solve_target == 'SHUTTER':
            denominator = (2**(ev100 - nd)) * (iso / 100.0)
            if denominator > 0:
                t_new = (N**2) / denominator
                if self.mode == 'STILLS': self.shutter_speed = t_new
                else: self.shutter_angle = t_new * self.fps * (2 * math.pi) if self.fps > 0 else 0
        elif self.solve_target == 'ISO':
            denominator = t * (2**(ev100 - nd))
            if denominator > 0: self.iso = (100.0 * (N**2)) / denominator
        elif self.solve_target == 'EV':
            if t > 0 and iso > 0: self.ev_value = math.log2((N**2) / t) - math.log2(iso / 100.0) + nd
        elif self.solve_target == 'ND':
            if t > 0 and iso > 0:
                ev_cam = math.log2((N**2) / t) - math.log2(iso / 100.0)
                self.nd_filter_stops = ev100 - ev_cam

        self.aperture_preset = next((k for k,v in APERTURE_ITEMS if k!='CUSTOM' and math.isclose(self.aperture, float(k))), 'CUSTOM')
        self.shutter_speed_preset = next((k for k,v in SHUTTER_ITEMS if k!='CUSTOM' and math.isclose(self.shutter_speed, float(k))), 'CUSTOM')
        self.iso_preset = next((k for k,v in ISO_ITEMS if k!='CUSTOM' and math.isclose(self.iso, float(k))), 'CUSTOM')
        if math.isclose(self.nd_filter_stops, 0):
            self.nd_filter_preset = '1'
        else:
            nd_val = 2**self.nd_filter_stops
            self.nd_filter_preset = next((k for k,v in ND_ITEMS if k!='CUSTOM' and k!='1' and math.isclose(nd_val, float(k))), 'CUSTOM')

    except (ValueError, ZeroDivisionError, AttributeError):
        pass
    finally:
        _EV_UPDATE_LOCK = False
        if context and context.area:
            context.area.tag_redraw()


# --- Texel Density ---
def get_2d_polygon_area(points):
    if len(points) < 3: return 0.0
    n = len(points); area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1] - points[j][0] * points[i][1]
    return abs(area) / 2.0

def sutherland_hodgman_clipper_with_uvs(polygon_with_uvs, clip_rect):
    def clip_against_edge(vertices, edge_index, is_max_edge):
        clipped_vertices = []
        for i in range(len(vertices)):
            p1 = vertices[i]; p2 = vertices[(i + 1) % len(vertices)]
            p1_screen = (p1[0], p1[1]); p2_screen = (p2[0], p2[1])
            p1_inside = (p1_screen[edge_index] <= clip_rect[edge_index*2+1]) if is_max_edge else (p1_screen[edge_index] >= clip_rect[edge_index*2])
            p2_inside = (p2_screen[edge_index] <= clip_rect[edge_index*2+1]) if is_max_edge else (p2_screen[edge_index] >= clip_rect[edge_index*2])
            if p1_inside and p2_inside:
                clipped_vertices.append(p2)
            elif p1_inside and not p2_inside:
                if p2_screen[edge_index] - p1_screen[edge_index] != 0:
                    t = (clip_rect[edge_index*2 + (1 if is_max_edge else 0)] - p1_screen[edge_index]) / (p2_screen[edge_index] - p1_screen[edge_index])
                    ix, iy = p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])
                    iu, iv = p1[2] + t * (p2[2] - p1[2]), p1[3] + t * (p2[3] - p1[3])
                    clipped_vertices.append((ix, iy, iu, iv))
            elif not p1_inside and p2_inside:
                if p2_screen[edge_index] - p1_screen[edge_index] != 0:
                    t = (clip_rect[edge_index*2 + (1 if is_max_edge else 0)] - p1_screen[edge_index]) / (p2_screen[edge_index] - p1_screen[edge_index])
                    ix, iy = p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])
                    iu, iv = p1[2] + t * (p2[2] - p1[2]), p1[3] + t * (p2[3] - p1[3])
                    clipped_vertices.append((ix, iy, iu, iv))
                clipped_vertices.append(p2)
        return clipped_vertices
    clipped = polygon_with_uvs
    clipped = clip_against_edge(clipped, 0, False); clipped = clip_against_edge(clipped, 0, True)
    clipped = clip_against_edge(clipped, 1, False); clipped = clip_against_edge(clipped, 1, True)
    return clipped

def calculate_texel_density(context):
    props = context.scene.texel_density_calculator
    obj = props.target_object
    cam = context.scene.camera
    scene = context.scene
    render = scene.render

    if not all([obj, cam, obj.data.uv_layers]):
        return "Prerequisites not met."

    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    uv_layer = bm.loops.layers.uv.active
    
    if not uv_layer:
        eval_obj.to_mesh_clear()
        bm.free()
        return "Active UV layer not found."

    max_density_ratio = 0.0
    clip_rect = (0, render.resolution_x, 0, render.resolution_y)

    for face in bm.faces:
        cam_direction = cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        if face.normal.dot(cam_direction) > 0: continue
        
        world_coords = [eval_obj.matrix_world @ loop.vert.co for loop in face.loops]
        uv_coords = [loop[uv_layer].uv for loop in face.loops]
        screen_coords_3d = [world_to_camera_view(scene, cam, wc) for wc in world_coords]
        
        if all(p.z <= 0 for p in screen_coords_3d): continue
        
        poly_with_uvs = []
        for i in range(len(screen_coords_3d)):
            p = screen_coords_3d[i]
            uv = uv_coords[i]
            poly_with_uvs.append((p.x * render.resolution_x, p.y * render.resolution_y, uv.x, uv.y))
        
        clipped_poly_with_uvs = sutherland_hodgman_clipper_with_uvs(poly_with_uvs, clip_rect)
        if len(clipped_poly_with_uvs) < 3: continue
        
        clipped_screen_poly = [(p[0], p[1]) for p in clipped_poly_with_uvs]
        clipped_uv_poly = [(p[2], p[3]) for p in clipped_poly_with_uvs]
        
        screen_area_px = get_2d_polygon_area(clipped_screen_poly)
        uv_area = get_2d_polygon_area(clipped_uv_poly)
        
        if screen_area_px <= 1e-6 or uv_area <= 1e-9: continue
        
        current_density_ratio = screen_area_px / uv_area
        if current_density_ratio > max_density_ratio:
            max_density_ratio = current_density_ratio

    eval_obj.to_mesh_clear()
    bm.free()

    if max_density_ratio == 0:
        props.result_effective_resolution = "N/A"
        props.result_resolution = translate("Calculation failed (off-screen)")
        props.result_udim_tiles = -1 
        props.result_coverage = ""
        return 'SUCCESS'

    required_res_100 = math.sqrt(max_density_ratio)
    target_resolution = required_res_100 * (props.pixel_ratio_percentage / 100.0)
    props.result_effective_resolution = f"{target_resolution:.0f} x {target_resolution:.0f} px"
    
    final_resolution = 2**math.ceil(math.log2(target_resolution)) if target_resolution > 0 else 0
    props.result_resolution = f"{final_resolution} x {final_resolution} px"
    
    if target_resolution > 0:
        coverage = (final_resolution / target_resolution) * 100
        props.result_coverage = f"{coverage:.1f}" # Only store the number
    else:
        props.result_coverage = ""

    udim_res = int(props.udim_resolution)
    required_total_pixels = (target_resolution)**2
    tile_pixels = udim_res**2
    num_tiles = math.ceil(required_total_pixels / tile_pixels) if tile_pixels > 0 else 0
    props.result_udim_tiles = num_tiles
    return 'SUCCESS'

def on_texel_density_property_change(self, context):
    if context.scene.texel_density_calculator.target_object:
        calculate_texel_density(context)

@persistent
def texel_density_depsgraph_handler(scene):
    if not hasattr(scene, "texel_density_calculator"): return
    props = scene.texel_density_calculator
    render = scene.render
    if not props.target_object or not scene.camera: return
    if scene.td_last_res_x == render.resolution_x and scene.td_last_res_y == render.resolution_y: return
    
    scene.td_last_res_x = render.resolution_x
    scene.td_last_res_y = render.resolution_y
    calculate_texel_density(bpy.context)

# --- (Lux/EV, Polling and handler registration/unregistration functions remain unchanged) ---
_LUXEV_UPDATE_LOCK = False
def on_lux_update(self, context):
    global _LUXEV_UPDATE_LOCK
    if _LUXEV_UPDATE_LOCK: return
    try:
        _LUXEV_UPDATE_LOCK = True
        if self.lux_meter_conv_lux > 0:
            self.lux_meter_conv_ev = math.log2(self.lux_meter_conv_lux / 2.5)
    finally: _LUXEV_UPDATE_LOCK = False

def on_ev_update(self, context):
    global _LUXEV_UPDATE_LOCK
    if _LUXEV_UPDATE_LOCK: return
    try:
        _LUXEV_UPDATE_LOCK = True
        self.lux_meter_conv_lux = 2.5 * (2**self.lux_meter_conv_ev)
    finally: _LUXEV_UPDATE_LOCK = False

def poll_sun_lights(self, object):
    return object.type == 'LIGHT' and object.data.type == 'SUN'

def initial_calculation():
    if bpy.context.scene:
        on_ev_mode_change(bpy.context.scene, bpy.context)
    return None

# --- parallax ---

def recalculate_parallax(scene):
    cam = scene.objects.get(scene.parallax_camera_name)
    if not cam or cam.type != 'CAMERA':
        return False

    if not cam.animation_data: return False
    
    start_frame = scene.parallax_start_frame
    end_frame = scene.parallax_end_frame
    pixel_shift = scene.parallax_pixel_shift

    if start_frame == end_frame: return False
    if pixel_shift <= 0: return False

    original_frame = scene.frame_current
    scene.frame_set(start_frame); pos1 = cam.matrix_world.translation.copy()
    scene.frame_set(end_frame); pos2 = cam.matrix_world.translation.copy()
    scene.frame_set(original_frame)
    
    baseline = (pos1 - pos2).length
    
    if baseline == 0:
        scene.parallax_distance_m = 0.0
        return False

    focal_length = cam.data.lens
    sensor_width = cam.data.sensor_width
    resolution_x = scene.render.resolution_x
    if sensor_width == 0 or pixel_shift == 0: return False
    
    distance = (focal_length * baseline * resolution_x) / (sensor_width * pixel_shift)
    scene.parallax_distance_m = distance
    return True

def on_parallax_setting_change(self, context):
    if context.scene.parallax_camera_name:
        recalculate_parallax(context.scene)


@persistent
def on_load_handler(dummy):
    bpy.app.timers.register(initial_calculation)

app_handlers = [
    (bpy.app.handlers.frame_change_post, speedo_realtime_update),
    (bpy.app.handlers.depsgraph_update_post, texel_density_depsgraph_handler),
    (bpy.app.handlers.load_post, on_load_handler)
]

def register():
    for handler_list, handler_func in app_handlers:
        if handler_func not in handler_list:
            handler_list.append(handler_func)
    bpy.app.timers.register(initial_calculation)

def unregister():
    for handler_list, handler_func in app_handlers:
        if handler_func in handler_list:
            handler_list.remove(handler_func)