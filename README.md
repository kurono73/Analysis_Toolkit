# Analysis_Toolkit
The **Analysis Toolkit** is a set of measurement and calculation tools for Blender.

All tools are located in the 3D Viewport's sidebar (press `N` to open) under the **"Analysis Toolkit"** tab.
## 1. UV SS(Screen Space) Resolution

This tool calculates the required texture resolution for the selected object's screen based on the active camera, UV unwrapping data, and rendering resolution. 

Understanding the optimal texture resolution helps identify insufficient or excessive textures.It can also be used to calculate the resolution of camera projection and embedded images.

### Interface

- **Target Object:** The mesh object to analyze.
- **Target Pixel Ratio:** The desired ratio of texture pixels to screen pixels. A value of 100% aims for a 1:1 mapping where one texture pixel covers one screen pixel.
- **UDIM Base Resolution:** The standard resolution of a single UDIM tile (e.g., 2048x2048) used to calculate the suggested tile count.
- **Recalculate at Current Position:** Recalculation when camera/object is moved in viewport.
- **Calculation Results**
    - **Effective Resolution:** The calculated, non-power-of-two resolution required to meet the Target Pixel Ratio.
    - **Recommended Single Texture Resolution:** The nearest power-of-two texture resolution (e.g., 2048x2048, 4096x4096) that covers the effective resolution.
    - **Suggestion UDIM Tiles:** The number of UDIM tiles needed to achieve the effective resolution, based on the selected UDIM Base Resolution.

### Workflow

1. Select the **Target Object**.
2. Select the camera to use for analysis.
3. Adjust the **Target Pixel Ratio** to define the desired texture quality.
4. If using a UDIM workflow, select the appropriate **UDIM Base Resolution**.
5. When you change any parameter, the results will be updated automatically. If you move the camera or object in the viewport, click **Recalculate**.
6. Use the **Recommended Resolution** or **UDIM Suggestion** as a guide for creating or scaling your textures.

---

## 2. Illuminance Meter

This tool allows you to measure the illuminance (in Lux) at multiple points within your scene using the Cycles render engine, enabling physically-based lighting adjustments.

Sun correction compensates for clipped or underexposed HDRIs based on measured illuminance values at the time of capture.

It is especially useful for VFX look development or architectural lighting design.


>💡note:    
>It can also be used when using Eevee, but measurements are taken using the Cycles engine.  
>These are only reference values and are not guaranteed to match reality.



### Interface

- **1. Sensor Management:**
    - **Add Sensor:** Creates a new arrow-shaped Empty at the 3D cursor's location. All sensors are automatically placed in a dedicated collection named "LightMeter Sensors".
- **2. Correction Settings:**
    - **EV Compensation:**This setting is important when you want to match the calculated values to real-world light meter readings.In CG, lighting that appears visually correct is typically the result of a camera applying exposure compensation to achieve a proper-looking image.  
    EV Compensation converts visually adjusted exposure back to **0 EV physical luminance**, allowing illuminance to be calculated and displayed on an absolute physical scale.  
    The EV value can be derived from exposure data recorded during **HDRI creation,** or from metadata embedded in**VFX plates or source photography**.  
    If the original exposure reference is unknown, entering an estimated EV value for the environment will produce results that are closer to real-world illuminance levels.  
        - Reference EV value：`Lux EV Converter`>`EV / Lux Reference`
        - EV calculation from metadata ： `EV Calculator`)
    
- **3. Measurement & Results:**
    - **Illuminance measurement:** Triggers a series of quick renders to measure the illuminance at the location and orientation of every sensor in the "LightMeter Sensors" collection.
    - **Average Lux:** The mathematical average of all successful measurements.
    - **Min / Max:** The lowest and highest Lux values recorded among all sensors.
    - **Individual Results:** A list displaying the name and measured Lux value for each sensor.
    - **Save Results as CSV:**Saves the names and lux values of all measured sensors to a CSV file.
- **Sun Correction:**
    - **Sun Object:** A pointer to select the `Sun` light in your scene.
    - **Basis Sensor:**The sensor to use as a reference for adjusting the sun's strength.
    - **Target Lux:** The desired illuminance value you want to achieve.
    - **Adjust Sun Strength:** Automatically adjusts the selected `Sun` light's strength so that the **currently elected sensor** receives the specified `Target Lux`.The Sun light will be adjusted to the target illuminance, taking into account all other valid lighting, including the World light.

### Workflow

- **Illuminance measurement:**
1. Click **Add Sensor** and place the new sensor empties at the points of interest in your scene. Orient the arrows to point towards the direction you want to measure from (the arrow points away from the measurement surface).
2. Click **Measure All Sensors**. The addon will process each sensor and display the results.
3. Measurement results can be saved in CSV format if necessary.
- **Sun Correction**
1. To match a real-world lighting condition, select a specific sensor, select your `Sun` light, enter a `Target Lux`, and click **Adjust Sun Strength**.
2. Click **Measure All Sensors** again to check if the target illuminance is achieved.


>💡When correcting a clipped HDRI, measure the actual illuminance on-site and use the known **inverse EV correction** value of the created HDRI.  
>Sun correction results and dark scenes will have some errors in the results due to sampling accuracy issues.


---

## 3. EV Lux Converter

A simple, real-time utility to convert between illuminance (Lux) and Exposure Value (EV at ISO 100).

### Interface

- **Lux:** The illuminance value in Lux.
- **EV:** The Exposure Value at ISO 100.
- **EV / Lux Reference:** Reference Table for Actual EV and Illuminance Values

### Workflow

Enter a value in either the `Lux` or `EV` — the other updates instantly using the standard formula: (`EV100 = log2(Lux / 2.5)`).

---

## 4. EV Calculator

A real-time exposure calculator to determine camera settings, similar to a photographer's light meter app. All calculations update instantly as you change values.

### Interface

- **Mode:**
    - **Stills:** For still photography. Aperture is treated as **F-Stop** and Shutter is **Shutter Speed (seconds)**.
    - **Movie:** For cinematography. Aperture is **T-Stop;** Shutter is **Shutter Angle (degrees)**. A **Frame Rate (FPS)** field becomes available.
- **Solve for:** Choose which parameter to calculate (Aperture, Shutter, ISO, EV, or ND Filter). The selected field becomes read-only and displays the computed result.
- **Parameter Inputs:**
    - **Aperture / T-Stop:** Lens aperture value with preset options.
    - **Shutter:** Either **Speed (s)** with fractional display (e.g., `(1/125s)`) or **Angle (°)**.
    - **ISO:** Sensor sensitivity, with common presets.
    - **ND Filter:** Neutral Density filter value; select a preset (e.g., `ND8 (3 Stop)`) or enter a custom number of stops.
    - **Exposure Value:** Desired EV, with buttons for `±1` stop and `±⅓` bstop adjustments.

### Workflow

1. Set the **Mode** to `Stills` or `Movie`.
2. Use the **Solve for** to choose which parameter to calculate.
3. Adjust the remaining parameters — results update in real time.

---

## 5. Horizon Distance Calculation

Calculates the geometric distance to the horizon based on the active camera's height, assuming a perfectly spherical Earth.

### Interface

- **Ground Z Offset:** Sets the Z-coordinate for "ground level". If your terrain is on a plane at Z=50, enter 50 here.
- **Calculate Horizon Distance:** Computes the distance based on the active camera’s Z position and ground offset.
- **Create Empty at Distance:** After calculating, this button creates an Empty in the camera's forward direction at the calculated horizon distance, positioned on the ground plane (at the Z Offset height).

### Workflow

1. Select your camera and position it at the desired height.
2. Enter the `Ground Z Offset` if necessary.
3. Click **Calculate Horizon Distance**.

---

## 6. Parallax Distance Calculation

Determine the distance at which background elements will appear static (i.e., have less than a specified parallax shift).  
Useful for calculating distances that can be replaced with matte painting.

### Interface

- **Current Settings:** Displays the active camera's relevant properties (Resolution, Sensor Size, Focal Length).
- **Reference Frames (A, B):** The start and end frames of the camera motion to be analyzed. Use the buttons to set them from the current frame on the timeline.
- **Auto-Detect Max Range:** Scans the entire scene's frame range to automatically find the two frames where the camera moved the farthest apart and sets them as A and B.
- **Allowed Pixel Shift:** The threshold for the parallax calculation. A value of `1.0` means you are calculating the distance at which an object will move by only one pixel on the final render.
- **Calculate Parallax Distance:** Performs the calculation.
- **Create Empty at Distance:** Creates an Empty in front of the camera at the calculated distance, which can be used as a guide for placing matte paintings or background geometry.

### Workflow

1. Select the animated camera.
2. Set or auto-detect the Reference Frames A and B.
3. Define the **Allowed Pixel Shift**.
4. Click **Calculate Parallax Distance**.

---

## 7. Shooting Distance

Calculates the straight-line distance from the active camera to a specified target in the scene.  
Useful for pre-visualization, focus distance setup, or depth-of-field planning.

### Interface

- **Target Mode:** Choose the target point.
    - **3D Cursor:** Measures the distance to the 3D cursor.
    - **Active Object:** Measures distance to the selected active object.
- **Result:** Displays the distance in Blender Units (typically meters).

### Workflow

1. Ensure you have an **Active Camera**.
2. Select your desired **Target Mode**.
3. If using **3D Cursor**, position it where you want to measure.
4. If using **Active Object** , select the target object.
5. Click **Calculate Shooting Distance**.
6. The tool displays the exact distance between the camera and the target.

---

## 8. Unit Converter

A real-time calculator for converting between Imperial and Metric units.

### Interface

- **Top Section (Imperial):** Choose the input format (`Feet (ft)`, `ft' in"`, `Inches (in)`) aand enter the value.
- **Bottom Section (Metric):** Choose the target unit (`mm`, `cm`, `m`) and enter the value.

### Workflow

Type a value in any field — all others update instantly.

---

## 9. Speedometer

Analyzes the speed of animated objects move.

### Interface

- **Scene Scale Factor:** Correction factor for speed calculation. E.g., if 1 Blender Unit = 1 cm, set to 0.01 to get results in meters/sec
- **Target:** Select the animated object to analyze.
- **Mode:**
    - **Instantaneous:** Displays the object’s speed at the current frame (updates in real time).Calculates speed by advancing the timeline frame by frame.
    - **Range Analysis:** Measures speed over a specified frame range.
- **Reference Frames (A, B) (Range Analysis only):** Start and end frames for analysis.
- **Calculate Speed over Range (Range Analysis only):** Executes the range analysis.
- **Unit**:Select units for `m/s`,`m/min`,`km/h`,`ft/s`,`mph`,`kn`,`Mach`.
- **Results:** Displays the speed in select units. In Range mode,shows Average, Max, and Min speeds.

### Workflow

1. Select the **Target Object**.
2. Choose `Instantaneous` or `Range Analysis` mode.
3. Set the Scene Scale Factor if your scene units differ from meters.
4. In `Instantaneous` mode, calculates speed by advancing the timeline frame by frame— the speed updates dynamically.
5. In `Range Analysis` mode, specify **Start** and **End Frames,**then run **Calculate Speed over Range**.
6. View results in your preferred units.
