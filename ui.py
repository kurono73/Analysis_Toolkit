import bpy
import math
from . import utils

# --- Panel Draw Functions ---

def draw_luxmeter_panel(layout, scene, context, _):
    """Draws the Illuminance Meter panel"""
    props = scene.analysis_toolkit_props
    box = layout.box()
    box.label(text=_("1. Sensor Management"))
    box.operator("scene_analysis.add_sensor", text=_("Add Sensor"))

    box = layout.box()
    box.label(text=_("2. Correction Settings"))
    row = box.row(align=True)
    row.label(text=_("EV Compensation"))
    row.prop(props, "lux_meter_ev_compensation", text="")

    box = layout.box()
    box.label(text=_("3. Measurement & Results"))
    box.operator("scene_analysis.measure_all", text=_("Illuminance measurement"), icon='PLAY')
    
    col = box.column(align=True)
    row = col.row(align=True)
    row.label(text=_("Average Lux") + ":")
    row.label(text=f"{props.lux_meter_avg_lux:.2f} lx")
    
    op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False)
    op.value_to_copy = f"{props.lux_meter_avg_lux:.2f}"
    
    row = col.row(align=True)
    row.label(text=_("Min / Max") + ":")
    sub_row = row.row(align=True)
    sub_row.label(text=f"{props.lux_meter_min_lux:.2f} lx")
    sub_row.label(text=f"/ {props.lux_meter_max_lux:.2f} lx")
    
    if props.lux_meter_results:
        box.label(text=_("Individual Results") + ":")
        res_box = box.box()
        for result in props.lux_meter_results:
            row = res_box.row()
            row.label(text=f"{result.name}:")
            row.label(text=f"{result.lux:.2f} lx")
            
            op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False)
            op.value_to_copy = f"{result.lux:.2f}"

        box.separator()
        box.operator("scene_analysis.save_results_csv", text=_("Save Results as CSV"), icon='FILE_TICK')

    sun_box = layout.box()
    row = sun_box.row()
    row.prop(props, "lux_meter_sun_panel_expanded", icon="TRIA_DOWN" if props.lux_meter_sun_panel_expanded else "TRIA_RIGHT", icon_only=True, emboss=False)
    row.label(text=_("Sun Correction"), icon='LIGHT_SUN')
    if props.lux_meter_sun_panel_expanded:
        sun_box.prop(props, "lux_meter_sun_object", text=_("Sun Object"))
        sun_box.prop(props, "lux_meter_correction_sensor", text=_("Basis Sensor"))
        row = sun_box.row(align=True)
        row.label(text=_("Target Lux")); row.prop(props, "lux_meter_target_lux", text="")
        sun_box.operator("scene_analysis.correct_sun_active", text=_("Adjust Sun Strength"), icon='PLAY')

def draw_texeldensity_panel(layout, scene, context, _):
    """Draws the Texel Density panel"""
    props = scene.analysis_toolkit_props.texel_density_calculator
    obj = props.target_object
    
    box = layout.box()
    box.label(text=_("Target"), icon='OBJECT_DATA')
    split = box.split(factor=0.4)
    split.label(text=_("Target Object:"))
    split.prop(props, "target_object", text="")

    box = layout.box()
    box.label(text=_("Settings"), icon='SETTINGS')
    split = box.split(factor=0.4)
    split.label(text=_("Target Pixel Ratio:"))
    split.prop(props, "pixel_ratio_percentage", text="")
    split = box.split(factor=0.4)
    split.label(text=_("UDIM Base Resolution:"))
    split.prop(props, "udim_resolution", text="")

    warning_box = layout.box()
    is_ready = True
    active_cam = scene.camera
    if not obj:
        warning_box.label(text=_("Select an object"), icon='ERROR')
        is_ready = False
    elif not obj.data.uv_layers:
        warning_box.alert = True
        warning_box.label(text=_("Object has no UV map!"), icon='ERROR')
        is_ready = False
    elif not active_cam:
        warning_box.alert = True
        warning_box.label(text=_("No active camera in scene"), icon='ERROR')
        is_ready = False
    else:
        warning_box.label(text=_("Ready"), icon='CHECKMARK')

    row = layout.row()
    row.scale_y = 1.5
    row.enabled = is_ready
    row.operator("scene_analysis.calculate_texel_density", text=_("Recalculate at Current Position"), icon='FILE_REFRESH')
    
    info_box = layout.box()
    info_box.label(text=_("Info"), icon='INFO')
    render = scene.render
    cam_name = active_cam.name if active_cam else _("None")
    info_box.label(text=_( "Active Camera: {cam}", cam=cam_name))
    info_box.label(text=_( "Render Resolution: {x} x {y} px", x=render.resolution_x, y=render.resolution_y))
    if obj and obj.data.uv_layers and obj.data.uv_layers.active:
        info_box.label(text=_( "Active UV: {uv}", uv=obj.data.uv_layers.active.name))
        
    result_box = layout.box()
    result_box.label(text=_("Calculation Results"), icon='TEXTURE')
    col = result_box.column(align=True)
    col.label(text=_("Effective Resolution (Calculated):"))
    row = col.row()
    row.alignment = 'CENTER'
    row.scale_y = 1.2
    row.label(text=props.result_effective_resolution)
    
    col.label(text=_("Recommended Single Texture Resolution:"))
    row = col.row()
    row.alignment = 'CENTER'
    row.scale_y = 1.2
    row.label(text=props.result_resolution)
    if props.result_coverage:
        row.label(text=_( "({coverage:.1f}% Coverage)", coverage=float(props.result_coverage)))

    col.separator()
    enum_items_dict = {item.identifier: item.name for item in props.bl_rna.properties['udim_resolution'].enum_items}
    udim_res_text = enum_items_dict.get(props.udim_resolution, "")
    col.label(text=_( "Suggested UDIM Tiles (Based on {res}):", res=udim_res_text))
    row = col.row()
    row.alignment = 'CENTER'
    row.scale_y = 1.2
    if props.result_udim_tiles >= 0:
        udim_text = _("{num} tiles required", num=props.result_udim_tiles)
        row.label(text=udim_text)
    else:
        row.label(text="N/A")

def draw_luxev_panel(layout, scene, context, _):
    """Draws the Lux <> EV Converter panel with a reference table"""
    props = scene.analysis_toolkit_props
    col = layout.column(align=True)
    col.prop(props, "lux_meter_conv_ev", text="EV")
    row = col.row(align=True)
    row.alignment = 'CENTER'
    row.label(icon='SORT_DESC')
    row.label(icon='SORT_ASC')
    col.prop(props, "lux_meter_conv_lux", text="Lux")
    
    layout.separator()

    box = layout.box()
    row = box.row()
    row.prop(props, "lux_meter_ref_panel_expanded", 
             icon="TRIA_DOWN" if props.lux_meter_ref_panel_expanded else "TRIA_RIGHT", 
             icon_only=True, emboss=False)
    row.label(text=_("EV / Lux Reference"), icon='BOOKMARKS')

    if props.lux_meter_ref_panel_expanded:
        sub_box = box.box()
        grid = sub_box.column(align=True)
        header = grid.row(align=True)
        split = header.split(factor=0.15); split.label(text="EV")
        split = split.split(factor=0.35); split.label(text="Lux (Approx.)")
        split.label(text=_("Condition"))
        grid.separator()
        ref_data = [
            ("16", "~164,000 lx", _("Snow on a sunny day")), ("15", "~82,000 lx", _("Full sunlight")),
            ("14", "~41,000 lx", _("Hazy, some clouds, sunny day")), ("13", "~20,000 lx", _("Cloudy")),
            ("12", "~10,000 lx", _("Overcast, shady areas, sunrise/sunset")), ("9-11", "1,300-5,100 lx", _("Blue hour")),
            ("8", "640 lx", _("Bright street/indoor light")), ("5-7", "80-320 lx", _("Indoor / Bright window light")),
            ("2-4", "10-40 lx", _("Dim window light")), ("-1-1", "1-5 lx", _("Dark morning/evening")),
            ("-2-3", "0.3-0.6 lx", _("Full moonlight")),
        ]
        for ev, lux, desc in ref_data:
            row = grid.row(align=True)
            split = row.split(factor=0.15); split.label(text=ev)
            split = split.split(factor=0.35); split.label(text=lux)
            split.label(text=desc)

def draw_ev_panel(layout, scene, context, _):
    s = scene.analysis_toolkit_props.ev_calculator
    
    layout.prop(s, "mode", text=_("Mode"), expand=True)
    layout.prop(s, "solve_target", text=_("Solve for"))

    aperture_label = _("T-Stop") if s.mode == 'MOVIE' else _("F-Stop")
    prefix = "T" if s.mode == 'MOVIE' else "f"
    row = layout.row(align=True); row.label(text=aperture_label)
    if s.solve_target == 'APERTURE': row.label(text=f"{prefix}/{s.aperture:.1f}")
    else:
        row.prop(s, "aperture_preset", text="")
        if s.aperture_preset == 'CUSTOM':
            custom_row = layout.row(); split = custom_row.split(factor=0.3)
            split.label(text=""); split.prop(s, "aperture", text=f"{prefix}/")

    if s.mode == 'STILLS':
        row = layout.row(align=True); row.label(text=_("Speed (s)"))
        if s.solve_target == 'SHUTTER': row.label(text=utils.format_shutter_speed(s.shutter_speed))
        else:
            row.prop(s, "shutter_speed_preset", text="")
            if s.shutter_speed_preset == 'CUSTOM':
                custom_row = layout.row(); split = custom_row.split(factor=0.3)
                split.label(text=""); row = split.row(align=True)
                row.prop(s, "shutter_speed", text="")
                row.label(text=f"({utils.format_shutter_speed(s.shutter_speed)})")
    else: # MOVIE
        row = layout.row(align=True); row.label(text=_("Angle (°)"))
        if s.solve_target == 'SHUTTER': row.label(text=_( "{angle:.1f}°", angle=math.degrees(s.shutter_angle)))
        else: row.prop(s, "shutter_angle", text="")
        row = layout.row(align=True); row.label(text=_("Frame Rate")); row.prop(s, "fps", text="")
        
    row = layout.row(align=True); row.label(text="ISO")
    if s.solve_target == 'ISO': row.label(text=f"ISO {s.iso:.0f}")
    else:
        row.prop(s, "iso_preset", text="")
        if s.iso_preset == 'CUSTOM':
            custom_row = layout.row(); split = custom_row.split(factor=0.3)
            split.label(text=""); split.prop(s, "iso", text="")
            
    row = layout.row(align=True); row.label(text=_("ND Filter"))
    if s.solve_target == 'ND':
        if s.nd_filter_stops > 0.01: row.label(text=_( "{stops:.1f} Stops", stops=s.nd_filter_stops))
        else: row.label(text=_("Not Required"), icon='INFO')
    else:
        row.prop(s, "nd_filter_preset", text="")
        if s.nd_filter_preset == 'CUSTOM':
            custom_row = layout.row(); split = custom_row.split(factor=0.3)
            split.label(text=""); split.prop(s, "nd_filter_stops", text="")

    row = layout.row(align=True); row.label(text=_("Exposure Value (EV)"))
    if s.solve_target == 'EV': row.label(text=f"EV {s.ev_value:.1f}")
    else:
        sub = row.row(align=True); sub.prop(s, "ev_value", text="")
        step_row = sub.row(align=True); step_row.scale_x = 0.8
        op = step_row.operator("scene_analysis.ev_step_value", text="-1"); op.step = -1.0
        op = step_row.operator("scene_analysis.ev_step_value", text="+1"); op.step = 1.0
        step_row.separator()
        op = step_row.operator("scene_analysis.ev_step_value", text="-⅓"); op.step = -1/3
        op = step_row.operator("scene_analysis.ev_step_value", text="+⅓"); op.step = 1/3

def draw_horizon_panel(layout, scene, context, _):
    """Draws the Horizon Distance panel"""
    props = scene.analysis_toolkit_props
    layout.prop(props, "horizon_ground_offset")
    layout.operator("scene_analysis.horizon_distance", text=_("Calculate Horizon Distance"), icon='PLAY')
    if props.horizon_distance_m > 0:
        res_box = layout.box()
        res_box.label(text=_("Result"))
        res_box.label(text=_( "From Camera: {cam}", cam=props.horizon_camera_name), icon='CAMERA_DATA')
        row = res_box.row(align=True); row.label(text=_("Height above offset") + ":"); row.label(text=utils.format_distance(context, props.horizon_camera_height))
        row = res_box.row(align=True); row.label(text=_("Distance") + ":"); row.label(text=utils.format_distance(context, props.horizon_distance_m))
        op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False)
        op.value_to_copy = f"{props.horizon_distance_m:.4f}"
        res_box.label(text=_("(Atmospheric refraction is considered)"), icon='INFO')
        res_box.operator("scene_analysis.horizon_create_empty", text=_("Create Empty at Distance"), icon='EMPTY_DATA')

def draw_parallax_panel(layout, scene, context, _):
    """Draws the Parallax Distance panel"""
    props = scene.analysis_toolkit_props
    info_box = layout.box(); cam = context.active_object
    if cam and cam.type == 'CAMERA':
        info_box.label(text=_("Current Settings") + ":")
        res_x=scene.render.resolution_x; res_y=scene.render.resolution_y; sensor_w=cam.data.sensor_width; focal_len=cam.data.lens
        row=info_box.row(align=True); row.label(text=_("Resolution")+":"); row.label(text=f"{res_x} x {res_y} px")
        row=info_box.row(align=True); row.label(text=_("Sensor")+":"); row.label(text=f"{sensor_w:.2f} mm")
        row=info_box.row(align=True); row.label(text=_("Focal Length")+":"); row.label(text=f"{focal_len:.1f} mm")
    else: info_box.label(text=_("Please select a camera"), icon='ERROR')
    layout.separator()
    layout.label(text=_("Reference Frames (A, B):"))
    row_frames = layout.row(align=True)
    row_frames.operator("scene_analysis.parallax_set_frame_a", text="A", icon='DECORATE_KEYFRAME'); row_frames.prop(props, "parallax_start_frame", text="")
    row_frames.separator(factor=1.0)
    row_frames.operator("scene_analysis.parallax_set_frame_b", text="B", icon='DECORATE_KEYFRAME'); row_frames.prop(props, "parallax_end_frame", text="")
    layout.operator("scene_analysis.parallax_find_extremes", text=_("Auto-Detect Max Range"), icon='AUTO')
    row_pixels = layout.row(align=True); row_pixels.prop(props, "parallax_pixel_shift", text=_("Allowed Pixel Shift"))
    layout.operator("scene_analysis.parallax_distance", text=_("Calculate Parallax Distance"), icon='PLAY')
    if props.parallax_distance_m > 0:
        res_box = layout.box(); pixel_shift_display = props.parallax_pixel_shift
        res_box.label(text=_( "From Camera: {cam}", cam=props.parallax_camera_name), icon='CAMERA_DATA')
        res_box.label(text=_( "{:.1f} Pixel Parallax Distance:", pixel_shift_display))
        row = res_box.row(align=True)
        row.label(text=utils.format_distance(context, props.parallax_distance_m))
        op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False); op.value_to_copy = f"{props.parallax_distance_m:.4f}"
        res_box.label(text=_( "(Objects farther than this will shift less than {:.1f}px)", pixel_shift_display), icon='INFO')
        res_box.operator("scene_analysis.parallax_create_empty", text=_("Create Empty at Distance"), icon='EMPTY_DATA')

def draw_shooting_distance_panel(layout, scene, context, _):
    """Draws the Shooting Distance panel"""
    props = scene.analysis_toolkit_props
    row_mode = layout.row(align=True)
    row_mode.prop_enum(props, "distance_target_mode", 'CURSOR'); row_mode.prop_enum(props, "distance_target_mode", 'ACTIVE_OBJECT')
    layout.operator("scene_analysis.distance_to_target", text=_("Calculate Shooting Distance"), icon='PLAY')
    if props.distance_to_target_m > 0:
        res_box = layout.box()
        res_box.label(text=_("Result"))
        res_box.label(text=_( "From Camera: {cam}", cam=props.distance_camera_name), icon='CAMERA_DATA')
        row = res_box.row(align=True)
        row.label(text=_("Distance") + ":"); row.label(text=utils.format_distance(context, props.distance_to_target_m))
        op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False)
        op.value_to_copy = f"{props.distance_to_target_m:.4f}"

def draw_converter_panel(layout, scene, context, _):
    """Draws the Unit Converter panel"""
    props = scene.analysis_toolkit_props
    col_imperial = layout.column(align=True)
    col_imperial.prop(props, "conv_imperial_unit", text="")
    if props.conv_imperial_unit == 'FT': col_imperial.prop(props, "conv_feet", text="ft")
    elif props.conv_imperial_unit == 'FT_IN':
        row = col_imperial.row(align=True); row.prop(props, "conv_feet", text="ft"); row.prop(props, "conv_inches", text="in")
    elif props.conv_imperial_unit == 'IN': col_imperial.prop(props, "conv_inches", text="in")
    icon_row = layout.row(align=True); icon_row.alignment = 'CENTER'
    icon_row.label(icon='SORT_DESC'); icon_row.label(icon='SORT_ASC')
    col_metric = layout.column(align=True)
    col_metric.prop(props, "conv_metric_unit", text="")
    col_metric.prop(props, "conv_metric_val", text="")

def draw_speedometer_panel(layout, scene, context, _):
    """Draws the Speedometer panel"""
    s = scene.analysis_toolkit_props.speedometer_props
    layout.prop(s, "scale_factor")
    layout.prop(s, "target_obj", text=_("Target"))
    row_mode = layout.row(align=True)
    row_mode.prop_enum(s, "mode", 'INSTANT'); row_mode.prop_enum(s, "mode", 'RANGE')
    layout.prop(s, "unit", text=_("Unit"))

    if s.mode == 'INSTANT':
        if s.target_obj:
            res_box = layout.box(); res_box.label(text=_("Result"))
            speed_val, unit_label = utils.get_converted_speed(s.speed_ms, s.unit)
            row = res_box.row(align=True)
            row.label(text=_("Current Speed") + ":"); row.label(text=f"{speed_val:.2f} {unit_label}")
            op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False)
            op.value_to_copy = f"{speed_val:.4f}"
    else: # 'RANGE'
        row_frames = layout.row(align=True)
        row_frames.operator("scene_analysis.speedo_set_frame_a", text="A", icon='DECORATE_KEYFRAME'); row_frames.prop(s, "start_frame", text="")
        row_frames.separator(factor=1.0)
        row_frames.operator("scene_analysis.speedo_set_frame_b", text="B", icon='DECORATE_KEYFRAME'); row_frames.prop(s, "end_frame", text="")
        layout.operator("scene_analysis.calculate_range_speed", text=_("Calculate Speed over Range"), icon='PLAY')
        
        if s.max_speed_ms >= 0:
            res_box = layout.box(); res_box.label(text=_("Result"))
            avg_val, unit_label = utils.get_converted_speed(s.avg_speed_ms, s.unit)
            max_val, _unit = utils.get_converted_speed(s.max_speed_ms, s.unit)
            min_val, _unit = utils.get_converted_speed(s.min_speed_ms, s.unit)
            row = res_box.row(align=True)
            row.label(text=_("Average Speed") + ":"); row.label(text=f"{avg_val:.2f} {unit_label}")
            op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False); op.value_to_copy = f"{avg_val:.4f}"
            row = res_box.row(align=True)
            row.label(text=_("Max Speed") + ":"); row.label(text=f"{max_val:.2f} {unit_label}")
            op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False); op.value_to_copy = f"{max_val:.4f}"
            row = res_box.row(align=True)
            row.label(text=_("Min Speed") + ":"); row.label(text=f"{min_val:.2f} {unit_label}")
            op = row.operator("scene_analysis.copy_value", text="", icon='COPYDOWN', emboss=False); op.value_to_copy = f"{min_val:.4f}"

# --- Panel Class Definitions (Base Class) ---
class ANALYSIS_PT_Base(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AnalysisToolkit'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return hasattr(context.scene, 'analysis_toolkit_props')

# --- Static Panel Class Definitions (Inheriting from Base) ---
class ANALYSIS_PT_luxmeter(ANALYSIS_PT_Base):
    bl_label = "Illuminance Meter"; bl_idname = "ANALYSIS_PT_luxmeter"
    def draw(self, context): draw_luxmeter_panel(self.layout, context.scene, context, utils.translate)

class ANALYSIS_PT_texeldensity(ANALYSIS_PT_Base):
    bl_label = "UV SS Resolution"; bl_idname = "ANALYSIS_PT_texeldensity"
    def draw(self, context): draw_texeldensity_panel(self.layout, context.scene, context, utils.translate)

class ANALYSIS_PT_luxev(ANALYSIS_PT_Base):
    bl_label = "EV Lux Converter"; bl_idname = "ANALYSIS_PT_luxev"
    def draw(self, context): draw_luxev_panel(self.layout, context.scene, context, utils.translate)

class ANALYSIS_PT_ev(ANALYSIS_PT_Base):
    bl_label = "EV Calculator"; bl_idname = "ANALYSIS_PT_ev"
    def draw(self, context): draw_ev_panel(self.layout, context.scene, context, utils.translate)

class ANALYSIS_PT_horizon(ANALYSIS_PT_Base):
    bl_label = "Horizon Distance"; bl_idname = "ANALYSIS_PT_horizon"
    def draw(self, context): draw_horizon_panel(self.layout, context.scene, context, utils.translate)

class ANALYSIS_PT_parallax(ANALYSIS_PT_Base):
    bl_label = "Parallax Distance"; bl_idname = "ANALYSIS_PT_parallax"
    def draw(self, context): draw_parallax_panel(self.layout, context.scene, context, utils.translate)

class ANALYSIS_PT_shooting_distance(ANALYSIS_PT_Base):
    bl_label = "Shooting Distance"; bl_idname = "ANALYSIS_PT_shooting_distance"
    def draw(self, context): draw_shooting_distance_panel(self.layout, context.scene, context, utils.translate)
    
class ANALYSIS_PT_converter(ANALYSIS_PT_Base):
    bl_label = "Unit Converter"; bl_idname = "ANALYSIS_PT_converter"
    def draw(self, context): draw_converter_panel(self.layout, context.scene, context, utils.translate)

class ANALYSIS_PT_speedometer(ANALYSIS_PT_Base):
    bl_label = "Speedometer"; bl_idname = "ANALYSIS_PT_speedometer"
    def draw(self, context): draw_speedometer_panel(self.layout, context.scene, context, utils.translate)

# --- Registration List ---
classes = (
    ANALYSIS_PT_texeldensity, ANALYSIS_PT_luxmeter, ANALYSIS_PT_luxev,
    ANALYSIS_PT_ev, ANALYSIS_PT_horizon, ANALYSIS_PT_parallax,
    ANALYSIS_PT_shooting_distance, ANALYSIS_PT_converter, ANALYSIS_PT_speedometer,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)