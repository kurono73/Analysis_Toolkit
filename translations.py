import bpy

translation_dict = {
    "ja_JP": {
        # General
        ("*" , "AnalysisToolkit"): "解析ツールキット",
        ("*" , "Calculation complete."): "計算が完了しました。",
        ("*" , "Result"): "計算結果",
        ("*" , "Distance"): "距離",
        ("*" , "Copy the specified value to the clipboard"): "指定された値をクリップボードにコピーします",
        ("*" , "None"): "なし",


        # Illuminance Meter
        ("*" , "Illuminance Meter"): "照度計",
        ("*" , "1. Sensor Management"): "1. センサー管理",
        ("*" , "Add Sensor"): "センサーを追加",
        ("*" , "Adds a new sensor to the 'LuxMeter Sensors' collection at the 3D cursor's position"): "3Dカーソルの位置に、新しいセンサーを「LuxMeter Sensors」コレクションへ追加します",
        ("*" , "2. Correction Settings"): "2. 補正設定",
        ("*" , "EV Compensation"): "EV逆補正値",
        ("*" , "Converts exposure based on visual appearance back to 0 EV physical luminance and calculates illuminance on an absolute scale.If the original exposure reference is unknown, entering the estimated EV value of the environment will provide results closer to real-world illuminance."): "見た目基準の露出を0EV基準の物理的輝度に戻し、実照度ベースで計算します。想定環境のEV値を入れる事で現実の照度に近づきます。",
        ("*" , "3. Measurement & Results"): "3. 測定と結果",
        ("*" , "Illuminance measurement"): "照度測定",
        ("*" , "Measures the illuminance (lux) for all sensors in the collection. This may take time as it involves rendering"): "コレクション内の全センサーの照度(lux)を測定します。レンダリングを伴うため時間がかかる場合があります",
        ("*" , "Average Lux"): "平均照度",
        ("*" , "Min / Max"): "最小 / 最大",
        ("*" , "Individual Results"): "個別結果",
        ("*" , "Save Results as CSV"): "結果をCSVで保存",
        ("*" , "Saves the names and lux values of all measured sensors to a CSV file"): "測定された全センサーの名前と照度値をCSVファイルに保存します",
        ("*" , "Sun Correction"): "太陽補正",
        ("*" , "Sun Object"): "太陽オブジェクト",
        ("*" , "Select the Sun Light object you want to adjust"): "調整したい太陽ライトのオブジェクトを選択してください",
        ("*" , "Basis Sensor"): "基準センサー",
        ("*" , "The sensor to use as a reference for adjusting the sun's strength"): "太陽の強度を調整するための基準として使用するセンサー",
        ("*" , "Target Lux"): "目標照度",
        ("*" , "The desired illuminance value that the Basis Sensor should receive from the Sun Light"): "基準センサーが太陽から受けるべき目標の照度",
        ("*" , "Adjust Sun Strength"): "太陽の強度を調整",
        ("*" , "Adjusts the strength of the selected Sun Light so that the 'Basis Sensor' receives the 'Target Lux' value"): "選択された太陽ライトの強度を、「基準センサー」が「目標照度」の値になるように調整します",
 
        # UV SS Resolution
        ("*" , "UV SS Resolution"): "UV SS 解像度",
        ("*" , "Target"): "ターゲット",
        ("*" , "Target Object:"): "対象オブジェクト:",
        ("*" , "Settings"): "設定",
        ("*" , "Target Pixel Ratio:"): "目標ピクセル比率:",
        ("*" , "UDIM Base Resolution:"): "UDIM基準解像度:",
        ("*" , "Select an object"): "オブジェクトを選択",
        ("*" , "Object has no UV map!"): "オブジェクトにUVマップがありません！",
        ("*" , "No active camera in scene"): "シーンにアクティブカメラがありません",
        ("*" , "Ready"): "準備OK",
        ("*" , "Recalculate at Current Position"): "現在の位置で再計算",
        ("*" , "Info"): "情報",
        ("*" , "Active Camera: {cam}"): "アクティブカメラ: {cam}",
        ("*" , "Render Resolution: {x} x {y} px"): "レンダリング解像度: {x} x {y} px",
        ("*" , "Active UV: {uv}"): "アクティブUV: {uv}",
        ("*" , "Calculation Results"): "計算結果",
        ("*" , "Effective Resolution (Calculated):"): "実効解像度 (計算値):",
        ("*" , "Recommended Single Texture Resolution:"): "単一テクスチャの推奨解像度:",
        ("*" , "({coverage:.1f}% Coverage)"): "({coverage:.1f}% カバー)",
        ("*" , "Suggested UDIM Tiles (Based on {res}):"): "UDIM参考タイル数 ({res}基準):",
        ("*" , "Calculate the optimal texture size based on the active camera view"): "アクティブカメラ視点での最適なテクスチャサイズを計算します",
        ("*" , "Calculation failed (off-screen)"): "計算不可 (画面外)",
        ("*" , "{num} tiles required"): "{num} 枚のタイルが必要です",

        # Lux EV Converter
        ("*" , "EV Lux Converter"): "EV Lux 換算",
        ("*" , "EV / Lux Reference"): "EV / Lux 参考",
        ("*" , "Condition"): "状況",
        ("*" , "Snow on a sunny day"): "雪の晴れの日",
        ("*" , "Full sunlight"): "晴天",
        ("*" , "Hazy, some clouds, sunny day"): "うす曇り、晴れ",
        ("*" , "Cloudy"): "曇り",
        ("*" , "Overcast, shady areas, sunrise/sunset"): "曇り、晴れの日陰、日の出・日の入り",
        ("*" , "Blue hour"): "ブルーアワー",
        ("*" , "Bright street/indoor light"): "明るい街灯、明るい室内照明",
        ("*" , "Indoor / Bright window light"): "室内照明、明るい窓からの光",
        ("*" , "Dim window light"): "薄暗い窓の光",
        ("*" , "Dark morning/evening"): "日の出前の薄暗い朝、日没後の暗い夜",
        ("*" , "Full moonlight"): "満月からの月明かり",

        # Speedometer
        ("*" , "Speedometer"): "速度計",
        ("*" , "Scene Scale Factor"): "シーンスケール補正",
        ("*" , "Correction factor for speed calculation. E.g., if 1 Blender Unit = 1 cm, set to 0.01 to get results in meters/sec"): "速度計算のための補正係数。例: 1 Blender Unit = 1 cm の場合、0.01に設定すると結果が メートル/秒 になります",
        ("*" , "Please select a target object."): "ターゲットオブジェクトを選択してください。",
        ("*" , "Instantaneous"): "瞬間速度",
        ("*" , "Range Analysis"): "範囲分析",
        ("*" , "Calculate Speed at Current Frame"): "現在のフレームで速度を計算",
        ("*" , "Calculate Speed over Range"): "範囲内の速度を計算",
        ("*" , "Current Speed"): "現在の速度",
        ("*" , "Speed (km/h)"): "時速",
        ("*" , "Average Speed"): "平均速度",
        ("*" , "Max Speed"): "最大速度",
        ("*" , "Min Speed"): "最低速度",
        ("*" , "Frame range is too short (min 2 frames)."): "フレーム範囲が短すぎます（最低2フレーム必要です）。",
        ("*" , "Speedometer"): "速度計",
        ("*" , "Speed Start Frame"): "速度開始フレーム",
        ("*" , "Speed End Frame"): "速度終了フレーム",
        ("*" , "Target Object"): "ターゲットオブジェクト",
        ("*" , "Unit"): "単位",
        ("*" , "Select the unit for speed measurement"): "速度の表示単位を選択します",
        ("*" , "The object whose speed you want to measure"): "速度を測定したいオブジェクト",
        ("*" , "Calculates speed by advancing the timeline frame by frame"): "タイムラインを1フレームずつ進めることで速度を計算します",
        ("*" , "Analyzes speed over a specified frame range using Point A and Point B"): "A点とB点で指定したフレーム範囲の速度を分析します",
        ("*" , "Set the current frame as the start point for range analysis"): "現在のフレームを範囲分析の開始点として設定します",
        ("*" , "Set the current frame as the end point for range analysis"): "現在のフレームを範囲分析の終了点として設定します",
        ("*" , "Calculates the average, maximum, and minimum speed of the target object between the start and end frames"): "開始フレームと終了フレームの間で、ターゲットオブジェクトの平均、最大、最低速度を計算します",



        # Shooting Distance
        ("*" , "Shooting Distance"): "撮影距離",
        ("*" , "Target Mode"): "ターゲットモード",
        ("*" , "3D Cursor"): "3Dカーソル",
        ("*" , "Active Object"): "アクティブオブジェクト",
        ("*" , "Calculate Shooting Distance"): "撮影距離を計算",
        ("*" , "Please set a camera as the scene's active camera."): "シーンのアクティブカメラとしてカメラを設定してください。",
        ("*" , "Target cannot be the camera itself."): "ターゲットをカメラ自身にすることはできません。",
        ("*" , "Calculates the distance from the scene's active camera to the target (3D Cursor or Active Object)"): "シーンのアクティブカメラからターゲット（3Dカーソルまたはアクティブオブジェクト）までの距離を計算します。",
        ("*" , "Choose the target for distance calculation: the 3D Cursor or the currently active object"): "距離計算のターゲットを選択：3Dカーソルまたは現在アクティブなオブジェクト",
        ("*" , "Target cannot be the camera itself."): "ターゲットをカメラ自身にすることはできません。",


        # Horizon
        ("*" , "Horizon Distance"): "水平線 距離",
        ("*" , "Calculate Horizon Distance"): "水平線距離を計算",
        ("*" , "Ground Z Offset"): "地面のZオフセット",
        ("*" , "Height above offset"): "オフセットからの高さ",
        ("*" , "(Atmospheric refraction is considered)"): "(大気屈折を考慮)",
        ("*" , "Calculate Horizon Distance"): "水平線距離を計算",
        ("*" , "Calculates the distance to the horizon from the active camera's height, considering atmospheric refraction"): "アクティブなカメラの高さから、大気屈折を考慮した水平線までの距離を計算します",
        ("*" , "Adjust the ground level (Z-axis) if it's not at 0"): "地面の高さ（Z軸）が0でない場合に調整します",
        ("*" , "Creates an Empty object at the calculated horizon distance in front of the camera"): "計算された水平線距離の、カメラ前方にエンプティオブジェクトを作成します",


        # Parallax
        ("*" , "Parallax Distance"): "視差 距離",
        ("*" , "Calculate Parallax Distance"): "視差距離を計算",
        ("*" , "Current Settings"): "現在の設定情報",
        ("*" , "Resolution"): "解像度",
        ("*" , "Sensor"): "センサー",
        ("*" , "Focal Length"): "焦点距離",
        ("*" , "Please select a camera"): "カメラを選択してください",
        ("*" , "Reference Frames (A, B):"): "基準点フレーム (A, B):",
        ("*" , "Reference Frame A"): "基準点フレーム A",
        ("*" , "Reference Frame B"): "基準点フレーム B",
        ("*" , "Allowed Pixel Shift"): "許容ピクセル数",
        ("*" , "Auto-Detect Max Range"): "最大移動範囲を自動検出",
        ("*" , "Found max range between frame {a} and {b}."): "最大移動範囲をフレーム {a} と {b} で検出しました。",
        ("*" , "{:.1f} Pixel Parallax Distance:"): "{:.1f}ピクセル視差の距離:",
        ("*" , "(Objects farther than this will shift less than {:.1f}px)"): "(これより遠景はズレが{:.1f}px未満)",
        ("*" , "Calculates the distance at which an object would have a parallax shift equal to the 'Allowed Pixel Shift'"): "「許容ピクセル数」で指定した視差と等しくなる距離を計算します",
        ("*" , "The maximum number of pixels an object is allowed to shift between frames A and B to be considered 'in focus' or at a stable distance"): "オブジェクトが「ピントが合っている」または安定した距離にあると見なされるために、フレームAとBの間で許容される最大のピクセルずれ",
        ("*" , "Set the current frame as reference point A for parallax calculation"): "現在のフレームを視差計算の基準点Aとして設定します",
        ("*" , "Set the current frame as reference point B for parallax calculation"): "現在のフレームを視差計算の基準点Bとして設定します",
        ("*" , "Finds the two frames within the scene's frame range where the camera has moved the farthest apart"): "シーンのフレーム範囲内で、カメラが最も大きく移動した2つのフレームを見つけ出します",
        ("*" , "Creates an Empty object at the calculated parallax distance in front of the camera"): "計算された視差距離の、カメラ前方にエンプティオブジェクトを作成します",


        # Empty Creation
        ("*" , "Create Empty at Distance"): "この距離にエンプティを作成",
        ("*" , "Result has not been calculated yet."): "まだ結果が計算されていません。",
        ("*" , "Created Empty at distance."): "指定された距離にエンプティを作成しました。",

        # Unit Converter
        ("*" , "Unit Converter"): "単位換算",
        ("*" , "Feet"): "フィート",
        ("*" , "Inches"): "インチ",
        ("*" , "Centimeters"): "センチメートル",


        # EV Calculator
        ("*" , "EV Calculator"): "EV計算機",
        ("*" , "Mode"): "モード",
        ("*" , "Stills"): "スチル",
        ("*" , "Movie"): "ムービー",
        ("*" , "Aperture"): "絞り",
        ("*" , "F-Stop"): "F値",
        ("*" , "T-Stop"): "T値",
        ("*" , "Shutter"): "シャッター",
        ("*" , "Speed (s)"): "速度 (秒)",
        ("*" , "Angle (°)"): "開角度 (°)",
        ("*" , "Frame Rate"): "フレームレート",
        ("*" , "Sensitivity"): "感度",
        ("*" , "ISO"): "ISO",
        ("*" , "Exposure Value (EV)"): "露出値 (EV)",
        ("*" , "Solve for"): "計算対象",
        ("*" , "Invalid input for calculation."): "計算のための入力値が無効です。",
        ("*" , "ND Filter"): "NDフィルター",
        ("*" , "{stops:.1f} Stops"): "{stops:.1f} ストップ",
        ("*" , "Not Required"): "不要",
        ("*" , "Adjust the Exposure Value by a specific step"): "露出値(EV)を特定の値だけ増減させます",

        # Common
        ("*" , "Please select a camera object."): "カメラオブジェクトを選択してください。",
        ("*" , "Camera height must be greater than 0."): "カメラの高さは0より大きい必要があります。",
        ("*" , "Active object is not a camera."): "アクティブなオブジェクトがカメラではありません。",
        ("*" , "Camera has no animation data."): "カメラにアニメーションデータがありません。",
        ("*" , "Reference points A and B must be on different frames."): "基準点AとBは異なるフレームに設定してください。",
        ("*" , "Allowed pixel shift must be greater than 0."): "許容ピクセル数は0より大きい値を設定してください。",
        ("*" , "Camera did not move between the specified frames."): "指定されたフレーム間でカメラが移動していません。",
        ("*" , "Could not find two distinct animated frames in the scene range."): "シーン内に2つ以上の異なるアニメーションフレームを見つけられませんでした。",
        ("*" , "From Camera: {cam}"): "使用カメラ: {cam}",
    }
}

def register():
    # Attempt to unregister first to handle hot-reloading
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass
    bpy.app.translations.register(__name__, translation_dict)

def unregister():
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass