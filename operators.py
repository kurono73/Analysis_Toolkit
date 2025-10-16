import bpy
import math
from bpy.props import FloatProperty, StringProperty
from . import utils
from mathutils import Vector

# --- luxmeter Operator ---
class luxmeter_OT_AddSensor(bpy.types.Operator):
    bl_idname = "scene_analysis.add_sensor"
    bl_label = "Add Sensor"
    bl_description = "Adds a new sensor to the 'LuxMeter Sensors' collection at the 3D cursor's position"

    
    def execute(self, context):
        collection_name = "LuxMeter Sensors"
        if collection_name in bpy.data.collections:
            sensor_collection = bpy.data.collections[collection_name]
        else:
            sensor_collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(sensor_collection)

        bpy.ops.object.empty_add(type='SINGLE_ARROW', align='WORLD', location=context.scene.cursor.location, scale=(0.25, 0.25, 0.25))
        new_sensor = context.active_object
        new_sensor.name = "LuxMeter_Sensor"

        for coll in new_sensor.users_collection:
            coll.objects.unlink(new_sensor)
        sensor_collection.objects.link(new_sensor)
        return {'FINISHED'}

class luxmeter_OT_MeasureAll(bpy.types.Operator):
    """Measure the illuminance of all sensors in the collection"""
    bl_idname = "scene_analysis.measure_all"
    bl_label = "Measure All Sensors"

    def execute(self, context):
        collection_name = "LuxMeter Sensors"
        if collection_name not in bpy.data.collections:
            self.report({'WARNING'}, f"Collection '{collection_name}' not found.")
            return {'CANCELLED'}

        sensor_collection = bpy.data.collections[collection_name]
        sensors = [obj for obj in sensor_collection.objects if obj.type == 'EMPTY']
        if not sensors:
            self.report({'WARNING'}, "No sensors found in the collection.")
            return {'CANCELLED'}

        context.scene.lux_meter_results.clear()
        lux_values = []
        

        scale = context.scene.speedometer_props.scale_factor
        if scale <= 0: scale = 1.0
        ev_comp = context.scene.lux_meter_ev_compensation
        
        wm = context.window_manager
        wm.progress_begin(0, len(sensors))

        for i, sensor in enumerate(sensors):
            self.report({'INFO'}, f"Measuring sensor '{sensor.name}'... ({i+1}/{len(sensors)})")
            # 1. Get raw measurements
            raw_cycles_lux = utils.perform_lux_measurement(context, sensor)
            
            if raw_cycles_lux is not None:
                new_result = context.scene.lux_meter_results.add()
                new_result.name = sensor.name
                
                # 2. Scale corrections applied and saved as "physical values" in raw_lux
                physical_lux = raw_cycles_lux / (scale**2)
                new_result.raw_lux = physical_lux
                
                # 3. Further EV correction is applied and saved in lux as "for display".
                display_lux = physical_lux * (2**ev_comp)
                new_result.lux = display_lux
                
                lux_values.append(display_lux)

            wm.progress_update(i + 1)

        wm.progress_end()

        if lux_values:
            context.scene.lux_meter_avg_lux = sum(lux_values) / len(lux_values)
            context.scene.lux_meter_min_lux = min(lux_values)
            context.scene.lux_meter_max_lux = max(lux_values)
            self.report({'INFO'}, "All sensor measurements are complete.")
        else:
            self.report({'WARNING'}, "No valid measurements were obtained.")
        return {'FINISHED'}

class luxmeter_OT_SaveResultsCSV(bpy.types.Operator):
    bl_idname = "scene_analysis.save_results_csv"
    bl_label = "Save Results as CSV"
    bl_description = "Saves the names and lux values of all measured sensors to a CSV file"

    
    filepath: StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        self.filepath = "lux_meter_results.csv"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        results = context.scene.lux_meter_results
        if not results:
            self.report({'WARNING'}, "No results to save.")
            return {'CANCELLED'}

        csv_content = "Sensor Name,Lux Value\n"
        for result in results:
            csv_content += f"{result.name},{result.lux:.2f}\n"
        
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            self.report({'INFO'}, f"Results saved to {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save file: {e}")
            return {'CANCELLED'}
            
        return {'FINISHED'}


class luxmeter_OT_CorrectSun(bpy.types.Operator):
    """Adjust the sun intensity based on the sensor selected in the dropdown"""
    bl_idname = "scene_analysis.correct_sun_active"
    bl_label = "Adjust Sun Strength"

    def execute(self, context):
        scene = context.scene
        sun_obj = scene.lux_meter_sun_object
        target_lux = scene.lux_meter_target_lux
        
        sensor_name = scene.lux_meter_correction_sensor
        basis_sensor = scene.objects.get(sensor_name)

        if not sun_obj:
            self.report({'WARNING'}, utils.translate("Sun Light to correct is not selected."))
            return {'CANCELLED'}
        if not basis_sensor:
            self.report({'WARNING'}, "Please select a valid sensor from the list.")
            return {'CANCELLED'}


        scale = scene.speedometer_props.scale_factor
        if scale <= 0: scale = 1.0
        ev_comp = scene.lux_meter_ev_compensation
        
        try:
            physical_target_lux = target_lux / (2**ev_comp)
        except ZeroDivisionError:
            self.report({'ERROR'}, "EV compensation resulted in a division by zero.")
            return {'CANCELLED'}


        original_strength = sun_obj.data.energy
        
        self.report({'INFO'}, utils.translate("Step 1/2: Measuring ambient light..."))
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        sun_obj.data.energy = 0.0
        
        raw_cycles_lux = utils.perform_lux_measurement(context, basis_sensor)
        
        if raw_cycles_lux is None:
            sun_obj.data.energy = original_strength
            self.report({'WARNING'}, utils.translate("Failed to measure ambient light."))
            return {'CANCELLED'}
            
        lux_ambient_physical = raw_cycles_lux / (scale**2)
        
        if lux_ambient_physical >= physical_target_lux:
            sun_obj.data.energy = 0
            display_ambient_lux = lux_ambient_physical * (2**ev_comp)
            self.report({'INFO'}, utils.translate("Ambient light ({lux:.0f} lx) exceeds target. Set Sun strength to 0.", lux=display_ambient_lux))
            return {'FINISHED'}
            
        self.report({'INFO'}, utils.translate("Step 2/2: Calibrating sun contribution..."))
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        CALIBRATION_STRENGTH = 1000.0
        sun_obj.data.energy = CALIBRATION_STRENGTH
        
        lux_total_at_calibration_raw = utils.perform_lux_measurement(context, basis_sensor)
        sun_obj.data.energy = original_strength

        if lux_total_at_calibration_raw is None:
            self.report({'WARNING'}, utils.translate("Failed to measure total light with sun."))
            return {'CANCELLED'}
            
        lux_total_at_calibration_physical = lux_total_at_calibration_raw / (scale**2)
            
        lux_from_sun_at_calibration = lux_total_at_calibration_physical - lux_ambient_physical

        if lux_from_sun_at_calibration <= 0:
            self.report({'WARNING'}, utils.translate("Sun does not appear to be contributing light to the sensor."))
            return {'CANCELLED'}

        lux_needed_from_sun = physical_target_lux - lux_ambient_physical
        
        strength_per_lux = CALIBRATION_STRENGTH / lux_from_sun_at_calibration
        new_strength = lux_needed_from_sun * strength_per_lux
        if new_strength < 0: new_strength = 0
        
        sun_obj.data.energy = new_strength
        self.report({'INFO'}, utils.translate("Updated Sun Light '{name}' strength to {strength:.2f} W/m².", name=sun_obj.name, strength=new_strength))
        return {'FINISHED'}

# --- TEXEL DENSITY Operator ---
class TEXELDENSITY_OT_Calculate(bpy.types.Operator):
    bl_idname = "scene_analysis.calculate_texel_density"
    bl_label = "Calculate Screen-Space Texel Density"
    bl_description = "Calculate the optimal texture size based on the active camera view"

    @classmethod
    def poll(cls, context):
        props = context.scene.texel_density_calculator
        return props and props.target_object and props.target_object.data.uv_layers and context.scene.camera

    def execute(self, context):
        result = utils.calculate_texel_density(context)
        if result == 'SUCCESS':
            self.report({'INFO'}, "Texel density calculated successfully.")
        else:
            self.report({'WARNING'}, result)
        return {'FINISHED'}

# --- SPEEDO Operator ---
class SPEEDO_OT_CalculateRangeSpeed(bpy.types.Operator):
    bl_idname = "scene_analysis.calculate_range_speed"; bl_label = "Calculate Speed over Range"; bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Calculates the average, maximum, and minimum speed of the target object between the start and end frames"
    def execute(self, context):
        scene = context.scene
        s = scene.speedometer_props # 新しいプロパティグループを参照
        target_obj = s.target_obj; start_frame = s.start_frame; end_frame = s.end_frame
        if not target_obj: self.report({'WARNING'}, utils.translate("Please select a target object.")); return {'CANCELLED'}
        if not target_obj.animation_data: self.report({'WARNING'}, utils.translate("Camera has no animation data.")); return {'CANCELLED'}
        if end_frame - start_frame < 1: self.report({'WARNING'}, utils.translate("Frame range is too short (min 2 frames).")); return {'CANCELLED'}
        
        original_frame = scene.frame_current
        fps = scene.render.fps / scene.render.fps_base
        time_delta = 1.0 / fps if fps > 0 else 1.0
        scale = s.scale_factor
        
        total_distance = 0.0; max_speed = -1.0; min_speed = float('inf')
        for f in range(start_frame, end_frame + 1):
            scene.frame_set(f - 1); pos_prev = target_obj.matrix_world.translation.copy()
            scene.frame_set(f); pos_current = target_obj.matrix_world.translation.copy()
            distance_per_frame = (pos_current - pos_prev).length * scale
            speed_ms = distance_per_frame / time_delta
            total_distance += distance_per_frame
            if speed_ms > max_speed: max_speed = speed_ms
            if speed_ms < min_speed: min_speed = speed_ms
        scene.frame_set(original_frame)
        duration_frames = end_frame - start_frame
        total_time = duration_frames * time_delta
        avg_speed = total_distance / total_time if total_time > 0 else 0
        s.avg_speed_ms = avg_speed; s.max_speed_ms = max_speed; s.min_speed_ms = min_speed
        self.report({'INFO'}, utils.translate("Calculation complete.")); return {'FINISHED'}

class SPEEDO_OT_SetFrameA(bpy.types.Operator):
    bl_idname = "scene_analysis.speedo_set_frame_a"; bl_label = "Set Point A for Speedo"; bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Set the current frame as the start point for range analysis"
    def execute(self, context): 
        context.scene.speedometer_props.start_frame = context.scene.frame_current
        return {'FINISHED'}

class SPEEDO_OT_SetFrameB(bpy.types.Operator):
    bl_idname = "scene_analysis.speedo_set_frame_b"; bl_label = "Set Point B for Speedo"; bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Set the current frame as the end point for range analysis"
    def execute(self, context): 
        context.scene.speedometer_props.end_frame = context.scene.frame_current
        return {'FINISHED'}

# --- DISTANCE Operator ---
class DISTANCE_OT_CalculateToTarget(bpy.types.Operator):
    bl_idname = "scene_analysis.distance_to_target"; bl_label = "Calculate Shooting Distance"
    bl_description = "Calculates the distance from the scene's active camera to the target (3D Cursor or Active Object)"
    def execute(self, context):
        scene = context.scene; cam = scene.camera
        if not cam: self.report({'WARNING'}, utils.translate("Please set a camera as the scene's active camera.")); return {'CANCELLED'}
        cam_loc = cam.matrix_world.translation; target_loc = None
        if scene.distance_target_mode == 'CURSOR': target_loc = scene.cursor.location
        else:
            target_obj = context.active_object
            if not target_obj: self.report({'WARNING'}, utils.translate("Please select an active object as the target.")); return {'CANCELLED'}
            if target_obj == cam: self.report({'WARNING'}, utils.translate("Target cannot be the camera itself.")); return {'CANCELLED'}
            target_loc = target_obj.matrix_world.translation
        distance = (cam_loc - target_loc).length
        scene.distance_to_target_m = distance
        scene.distance_camera_name = cam.name
        self.report({'INFO'}, utils.translate("Calculation complete.")); return {'FINISHED'}

# --- HORIZON Operator ---
class HORIZON_OT_CalculateDistance(bpy.types.Operator):
    bl_idname = "scene_analysis.horizon_distance"; bl_label = "Calculate Horizon Distance"
    bl_description = "Calculates the distance to the horizon from the active camera's height, considering atmospheric refraction"
    def execute(self, context):
        cam = context.active_object; scene = context.scene
        if not cam or cam.type != 'CAMERA': self.report({'WARNING'}, utils.translate("Please select a camera object.")); return {'CANCELLED'}
        # ground_offset = scene.horizon_ground_offset * scale 
        # effective_height = (cam.location.z * scale) - ground_offset
        ground_offset = scene.horizon_ground_offset
        effective_height = cam.location.z - ground_offset
        if effective_height <= 0:
            scene.horizon_distance_m = 0.0; self.report({'WARNING'}, utils.translate("Camera height must be greater than 0.")); return {'CANCELLED'}
        effective_earth_radius = 6371000.0 * (7.0 / 6.0)
        distance = math.sqrt(pow(effective_earth_radius + effective_height, 2) - pow(effective_earth_radius, 2))
        scene.horizon_distance_m = distance; scene.horizon_camera_height = effective_height
        scene.horizon_camera_name = cam.name
        self.report({'INFO'}, utils.translate("Calculation complete.")); return {'FINISHED'}
class HORIZON_OT_CreateEmpty(bpy.types.Operator):
    bl_idname = "scene_analysis.horizon_create_empty"; bl_label = "Create Empty for Horizon"
    bl_description = "Creates an Empty object at the calculated horizon distance in front of the camera"
    def execute(self, context):
        cam = context.active_object; scene = context.scene; distance = scene.horizon_distance_m; ground_offset = scene.horizon_ground_offset
        if not cam or cam.type != 'CAMERA': self.report({'WARNING'}, utils.translate("Active object is not a camera.")); return {'CANCELLED'}
        if distance <= 0: self.report({'WARNING'}, utils.translate("Result has not been calculated yet.")); return {'CANCELLED'}
        distance_unscaled = distance
        cam_matrix = cam.matrix_world; cam_location = cam.matrix_world.translation
        forward_vector = -cam_matrix.col[2].xyz.normalized()
        point_in_front = cam_location + forward_vector * distance_unscaled
        empty_location = Vector((point_in_front.x, point_in_front.y, ground_offset))
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=empty_location)
        new_empty = context.active_object; new_empty.name = "Horizon_Ground_Empty"
        new_empty.empty_display_size = distance_unscaled / 20 if distance_unscaled > 0 else 1.0
        self.report({'INFO'}, utils.translate("Created Empty at distance.")); return {'FINISHED'}

# --- PARALLAX Operator ---
class PARALLAX_OT_CalculateDistance(bpy.types.Operator):
    bl_idname = "scene_analysis.parallax_distance"; bl_label = "Calculate Parallax Distance"
    bl_description = "Calculates the distance at which an object would have a parallax shift equal to the 'Allowed Pixel Shift'"
    
    def execute(self, context):
        cam = context.active_object
        scene = context.scene
        
        if not cam or cam.type != 'CAMERA':
            self.report({'WARNING'}, utils.translate("Active object is not a camera."))
            return {'CANCELLED'}

        scene.parallax_camera_name = cam.name

        if utils.recalculate_parallax(scene):
            self.report({'INFO'}, utils.translate("Calculation complete."))
        else:
            self.report({'WARNING'}, utils.translate("Calculation failed. Check settings."))

        return {'FINISHED'}

class PARALLAX_OT_SetFrameA(bpy.types.Operator):
    bl_idname = "scene_analysis.parallax_set_frame_a"; bl_label = "Set Point A"; bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Set the current frame as reference point A for parallax calculation"
    def execute(self, context):
        context.scene.parallax_start_frame = context.scene.frame_current
        if context.scene.parallax_camera_name:
            utils.on_parallax_setting_change(self, context)
        return {'FINISHED'}

class PARALLAX_OT_SetFrameB(bpy.types.Operator):
    bl_idname = "scene_analysis.parallax_set_frame_b"; bl_label = "Set Point B"; bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Set the current frame as reference point B for parallax calculation"
    def execute(self, context):
        context.scene.parallax_end_frame = context.scene.frame_current
        if context.scene.parallax_camera_name:
            utils.on_parallax_setting_change(self, context)
        return {'FINISHED'}

class PARALLAX_OT_FindExtremes(bpy.types.Operator):
    bl_idname = "scene_analysis.parallax_find_extremes"; bl_label = "Auto-Detect Max Range"; bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Finds the two frames within the scene's frame range where the camera has moved the farthest apart"
    def execute(self, context):
        cam = context.active_object; scene = context.scene
        if not cam or cam.type != 'CAMERA': self.report({'WARNING'}, utils.translate("Active object is not a camera.")); return {'CANCELLED'}
        if not cam.animation_data: self.report({'WARNING'}, utils.translate("Camera has no animation data.")); return {'CANCELLED'}
        original_frame = scene.frame_current; frame_start, frame_end = scene.frame_start, scene.frame_end
        positions = []
        for f in range(frame_start, frame_end + 1):
            scene.frame_set(f)
            positions.append((f, cam.matrix_world.translation.copy()))
        scene.frame_set(original_frame)
        if len(positions) < 2: self.report({'WARNING'}, utils.translate("Could not find two distinct animated frames in the scene range.")); return {'CANCELLED'}
        max_dist_sq = -1.0; best_a, best_b = -1, -1
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                frame1, pos1 = positions[i]; frame2, pos2 = positions[j]; dist_sq = (pos1 - pos2).length_squared
                if dist_sq > max_dist_sq: max_dist_sq = dist_sq; best_a, best_b = frame1, frame2
        if best_a != -1:
            if best_a > best_b: best_a, best_b = best_b, best_a
            scene.parallax_start_frame = best_a; scene.parallax_end_frame = best_b
            self.report({'INFO'}, utils.translate("Found max range between frame {a} and {b}.", a=best_a, b=best_b))
            if scene.parallax_camera_name:
                utils.on_parallax_setting_change(self, context)
        return {'FINISHED'}

class PARALLAX_OT_CreateEmpty(bpy.types.Operator):
    bl_idname = "scene_analysis.parallax_create_empty"; bl_label = "Create Empty for Parallax"
    bl_description = "Creates an Empty object at the calculated parallax distance in front of the camera"
    def execute(self, context):
        distance = context.scene.parallax_distance_m
        if distance <= 0:
            self.report({'WARNING'}, utils.translate("Result has not been calculated yet."))
            return {'CANCELLED'}
        distance_unscaled = distance
        report_msg = utils.create_empty_at_distance(context, distance_unscaled, "Parallax_Empty")
        self.report({'INFO'}, report_msg); return {'FINISHED'}

# --- EVcalculator Operator ---
class EV_OT_StepValue(bpy.types.Operator):
    bl_idname = "scene_analysis.ev_step_value"; bl_label = "Step EV Value"; bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Adjust the Exposure Value by a specific step"
    step: FloatProperty()
    def execute(self, context):
        context.scene.ev_calculator.ev_value += self.step
        return {'FINISHED'}

# --- ANALYSIS Operator ---
class ANALYSIS_OT_CopyValue(bpy.types.Operator):
    bl_idname = "scene_analysis.copy_value"; bl_label = "Copy Value"; bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Copy the specified value to the clipboard"
    value_to_copy: StringProperty()
    def execute(self, context):
        context.window_manager.clipboard = self.value_to_copy
        self.report({'INFO'}, f"Copied: {self.value_to_copy}"); return {'FINISHED'}

# --- Registration class list ---
classes = (
    luxmeter_OT_AddSensor,
    luxmeter_OT_MeasureAll,
    luxmeter_OT_SaveResultsCSV,
    luxmeter_OT_CorrectSun,
    TEXELDENSITY_OT_Calculate,
    SPEEDO_OT_CalculateRangeSpeed,
    SPEEDO_OT_SetFrameA,
    SPEEDO_OT_SetFrameB,
    DISTANCE_OT_CalculateToTarget,
    HORIZON_OT_CalculateDistance,
    HORIZON_OT_CreateEmpty,
    PARALLAX_OT_CalculateDistance,
    PARALLAX_OT_SetFrameA,
    PARALLAX_OT_SetFrameB,
    PARALLAX_OT_FindExtremes,
    PARALLAX_OT_CreateEmpty,
    EV_OT_StepValue,
    ANALYSIS_OT_CopyValue,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)