import bpy
import math
from bpy.props import FloatProperty, IntProperty, EnumProperty, PointerProperty, BoolProperty, CollectionProperty, StringProperty
from . import utils

# --- PropertyGroup Definitions ---

class EVPropertyGroup(bpy.types.PropertyGroup):
    mode: EnumProperty(name="Mode", items=[('STILLS', "Stills", ""), ('MOVIE', "Movie", "")], default='STILLS', update=utils.update_ev_calculation)
    solve_target: EnumProperty(name="Solve Target", items=[('APERTURE', "Aperture", ""), ('SHUTTER', "Shutter", ""), ('ISO', "ISO", ""), ('EV', "EV", ""), ('ND', "ND Filter", "")], default='EV', update=utils.update_ev_calculation)
    aperture_preset: EnumProperty(name="Aperture Preset", items=utils.APERTURE_ITEMS, default='2.8', update=utils.update_ev_calculation)
    aperture: FloatProperty(name="Aperture", default=2.8, min=0.1, soft_max=64.0, update=utils.update_ev_calculation)
    shutter_speed_preset: EnumProperty(name="Shutter Speed Preset", items=utils.SHUTTER_ITEMS, default=str(1/50), update=utils.update_ev_calculation)
    shutter_speed: FloatProperty(name="Shutter Speed", default=1/50.0, min=0.000001, precision=6, subtype='TIME', unit='TIME', update=utils.update_ev_calculation)
    shutter_angle: FloatProperty(name="Shutter Angle", default=math.pi, min=0.00174533, max=6.28319, subtype='ANGLE', unit='ROTATION', update=utils.update_ev_calculation)
    fps: FloatProperty(name="FPS", default=24.0, min=1.0, update=utils.update_ev_calculation)
    iso_preset: EnumProperty(name="ISO Preset", items=utils.ISO_ITEMS, default='100', update=utils.update_ev_calculation)
    iso: FloatProperty(name="ISO", default=100.0, min=1.0, update=utils.update_ev_calculation)
    ev_value: FloatProperty(name="EV", default=15.0, update=utils.update_ev_calculation)
    nd_filter_preset: EnumProperty(name="ND Filter Preset", items=utils.ND_ITEMS, default='1', update=utils.update_ev_calculation)
    nd_filter_stops: FloatProperty(name="ND Filter Stops", default=0.0, min=0.0, soft_max=10.0, update=utils.update_ev_calculation)

class luxmeterResultItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    lux: bpy.props.FloatProperty()
    raw_lux: bpy.props.FloatProperty()

class TexelDensityPropertyGroup(bpy.types.PropertyGroup):
    target_object: PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        poll=lambda self, object: object.type == 'MESH',
        update=utils.on_texel_density_property_change
    )
    pixel_ratio_percentage: IntProperty(
        name="Target Pixel Ratio",
        description=bpy.app.translations.pgettext_tip("How many texture pixels to assign per 1 screen pixel. The slider goes up to 100%, but higher values can be entered manually"),
        default=100, min=10, max=400, soft_min=10, soft_max=100, subtype='PERCENTAGE',
        update=utils.on_texel_density_property_change
    )
    udim_resolution: EnumProperty(
        name="UDIM Base Resolution",
        items=[('1024', '1024x1024', ''), ('2048', '2048x2048', ''), ('4096', '4096x4096', ''), ('8192', '8192x8192', '')],
        default='2048',
        update=utils.on_texel_density_property_change
    )
    result_effective_resolution: StringProperty(name="Effective Resolution", default="N/A")
    result_resolution: StringProperty(name="Recommended Resolution", default="N/A")
    result_udim_tiles: IntProperty(name="UDIM Tiles", default=-1)
    result_coverage: StringProperty(name="Coverage", default="")

class SpeedometerPropertyGroup(bpy.types.PropertyGroup):
    scale_factor: FloatProperty(
        name="Scene Scale Factor",
        description=bpy.app.translations.pgettext_tip("Correction factor for speed calculation. E.g., if 1 Blender Unit = 1 cm, set to 0.01 to get results in meters/sec"),
        default=1.0,
        min=0.0001
    )
    target_obj: PointerProperty(
        name="Target Object",
        description=bpy.app.translations.pgettext_tip("The object whose speed you want to measure"),
        type=bpy.types.Object
    )
    mode: EnumProperty(
        name="Speedo Mode",
        items=[
            ('INSTANT', "Instantaneous", bpy.app.translations.pgettext_tip("Calculates speed by advancing the timeline frame by frame")),
            ('RANGE', "Range Analysis", bpy.app.translations.pgettext_tip("Analyzes speed over a specified frame range using Point A and Point B"))
        ],
        default='INSTANT'
    )
    unit: EnumProperty(
        name="Unit",
        description=bpy.app.translations.pgettext_tip("Select the unit for speed measurement"),
        items=[('KMH', "km/h", "Kilometers per hour"), ('MS', "m/s", "Meters per second"), ('MMIN', "m/min", "Meters per minute"), ('MPH', "mph", "Miles per hour"), ('FTS', "ft/s", "Feet per second"), ('KNOT', "kn", "Knots"), ('MACH', "Mach", "Mach number")],
        default='KMH'
    )
    start_frame: IntProperty(name="Speed Start Frame", default=1)
    end_frame: IntProperty(name="Speed End Frame", default=100)
    speed_ms: FloatProperty(name="Speed (m/s)", default=0.0)
    avg_speed_ms: FloatProperty(name="Average Speed (m/s)", default=-1.0)
    max_speed_ms: FloatProperty(name="Max Speed (m/s)", default=-1.0)
    min_speed_ms: FloatProperty(name="Min Speed (m/s)", default=-1.0)

def get_sensor_items(self, context):
    items = []
    collection_name = "LuxMeter Sensors"
    if collection_name in bpy.data.collections:
        sensor_collection = bpy.data.collections[collection_name]
        sensors = [obj for obj in sensor_collection.objects if obj.type == 'EMPTY']
        for sensor in sensors:
            items.append((sensor.name, sensor.name, ""))
    if not items:
        items.append(("NONE", "No Sensors Found", ""))
    return items

class AnalysisToolkitPropertyGroup(bpy.types.PropertyGroup):
    # --- Pointers to other PropertyGroups ---
    speedometer_props: PointerProperty(type=SpeedometerPropertyGroup)
    ev_calculator: PointerProperty(type=EVPropertyGroup)
    texel_density_calculator: PointerProperty(type=TexelDensityPropertyGroup)

    # --- Lux Meter Properties ---
    lux_meter_results: CollectionProperty(type=luxmeterResultItem)
    lux_meter_avg_lux: FloatProperty(name="Average Lux", precision=2, default=-1.0)
    lux_meter_min_lux: FloatProperty(name="Min Lux", precision=2, default=-1.0)
    lux_meter_max_lux: FloatProperty(name="Max Lux", precision=2, default=-1.0)
    lux_meter_ev_compensation: FloatProperty(
        name="EV Compensation",
        description=bpy.app.translations.pgettext_tip("Converts exposure based on visual appearance back to 0 EV physical luminance and calculates illuminance on an absolute scale.If the original exposure reference is unknown, entering the estimated EV value of the environment will provide results closer to real-world illuminance."),
        default=0.0,
        precision=2,
        update=utils.on_ev_compensation_change
    )
    lux_meter_sun_object: PointerProperty(name="Sun Object", description=bpy.app.translations.pgettext_tip("Select the Sun Light object you want to adjust"), type=bpy.types.Object, poll=utils.poll_sun_lights)
    lux_meter_target_lux: FloatProperty(name="Target Lux", description=bpy.app.translations.pgettext_tip("The desired illuminance value that the Basis Sensor should receive from the Sun Light"), default=100000.0, min=0.0)
    lux_meter_correction_sensor: EnumProperty(name="Basis Sensor", description=bpy.app.translations.pgettext_tip("The sensor to use as a reference for adjusting the sun's strength"), items=get_sensor_items)
    lux_meter_sun_panel_expanded: BoolProperty(name="Expand Sun Correction", default=False)
    lux_meter_ref_panel_expanded: BoolProperty(name="Expand Reference Panel", default=False)

    # --- Lux/EV Converter Properties ---
    lux_meter_conv_ev: FloatProperty(name="EV", default=15.0, precision=2, update=utils.on_ev_update)
    lux_meter_conv_lux: FloatProperty(name="Lux", default=81920.0, min=0.0, update=utils.on_lux_update)

    # --- Shooting Distance Properties ---
    distance_to_target_m: FloatProperty(name="Distance to Target (m)", default=0.0)
    distance_target_mode: EnumProperty(name="Target Mode", description=bpy.app.translations.pgettext_tip("Choose the target for distance calculation: the 3D Cursor or the currently active object"), items=[('CURSOR', "3D Cursor", ""), ('ACTIVE_OBJECT', "Active Object", "")], default='CURSOR')
    distance_camera_name: StringProperty(name="Camera Name for Distance")

    # --- Horizon Distance Properties ---
    horizon_distance_m: FloatProperty(name="Horizon Distance (m)", default=0.0)
    horizon_camera_height: FloatProperty(name="Camera Height (m)", default=0.0)
    horizon_ground_offset: FloatProperty(name="Ground Z Offset", description=bpy.app.translations.pgettext_tip("Adjust the ground level (Z-axis) if it's not at 0"), default=0.0, unit='LENGTH')
    horizon_camera_name: StringProperty(name="Camera Name for Horizon")

    # --- Parallax Distance Properties ---
    parallax_start_frame: IntProperty(name="Reference Frame A", default=1, update=utils.on_parallax_setting_change)
    parallax_end_frame: IntProperty(name="Reference Frame B", default=100, update=utils.on_parallax_setting_change)
    parallax_distance_m: FloatProperty(name="Parallax Distance (m)", default=0.0)
    parallax_pixel_shift: FloatProperty(
        name="Pixel Shift",
        description=bpy.app.translations.pgettext_tip("The maximum number of pixels an object is allowed to shift between frames A and B to be considered 'in focus' or at a stable distance"),
        default=1.0, min=0.1, soft_max=20.0, step=10, precision=1, update=utils.on_parallax_setting_change
    )
    parallax_camera_name: StringProperty(name="Camera Name for Parallax")

    # --- Unit Converter Properties ---
    conv_imperial_unit: EnumProperty(name="Imperial Unit", items=[('FT', "Feet (ft)", ""), ('FT_IN', "ft' in\"", ""), ('IN', "Inches (in)", "")], default='FT_IN', update=utils.imperial_to_metric)
    conv_metric_unit: EnumProperty(name="Metric Unit", items=[('MM', "mm", ""), ('CM', "cm", ""), ('M', "m", "")], default='CM', update=utils.metric_to_imperial)
    conv_feet: FloatProperty(name="Feet", default=5.0, min=0.0, update=utils.imperial_to_metric)
    conv_inches: FloatProperty(name="Inches", default=10.0, min=0.0, max=11.999, update=utils.imperial_to_metric)
    conv_metric_val: FloatProperty(name="", default=177.8, min=0.0, update=utils.metric_to_imperial)

    # --- Internal Properties for Texel Density Handler ---
    td_last_res_x: IntProperty(options={'HIDDEN'})
    td_last_res_y: IntProperty(options={'HIDDEN'})


classes = (
    EVPropertyGroup,
    luxmeterResultItem,
    TexelDensityPropertyGroup,
    SpeedometerPropertyGroup,
    AnalysisToolkitPropertyGroup,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.analysis_toolkit_props = PointerProperty(type=AnalysisToolkitPropertyGroup)

def unregister():
    if hasattr(bpy.types.Scene, 'analysis_toolkit_props'):
        del bpy.types.Scene.analysis_toolkit_props
        
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)