# SceneAnalysisToolkit

# 各モジュールをインポート
from . import translations
from . import utils
from . import properties
from . import operators
from . import ui

def register():
    translations.register()
    properties.register()
    operators.register()
    ui.register()
    utils.register() # ハンドラー登録用

def unregister():
    utils.unregister() # ハンドラー登録解除用
    ui.unregister()
    operators.unregister()
    properties.unregister()
    translations.unregister()

