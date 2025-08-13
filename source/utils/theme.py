import dearpygui.dearpygui as dpg

class NodeTheme:
    def __init__(self):
        super().__init__()

    def apply_theme(self, node_outline=(58, 58, 58, 255)):
        with dpg.theme() as node_theme:
            with dpg.theme_component(dpg.mvNode):
                dpg.add_theme_color(dpg.mvNodeCol_NodeBackground, (30, 30, 30, 255), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundHovered, (42, 42, 42, 255), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundSelected, (48, 48, 48, 255), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (41, 41, 41, 255), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (58, 58, 58, 255), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (14, 14, 14, 255), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, node_outline, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_Pin, (117, 117, 117, 255), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(dpg.mvNodeCol_PinHovered, (0, 255, 255, 255), category=dpg.mvThemeCat_Nodes)

            return node_theme

class NodeButtonTheme:
    def __init__(self):
        super().__init__()

    def apply_theme(self, border_color=(80, 160, 200, 255), border_size=3.0):
        with dpg.theme() as button_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5.0, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 15.0, 5.0, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, border_size, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (41, 41, 41, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (58, 58, 58, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (70, 70, 70, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, border_color, category=dpg.mvThemeCat_Core)
                
            return button_theme

class NodeMenuTheme:
    def __init__(self):
        super().__init__()

    def apply_theme(self):
        with dpg.theme() as menu_theme:
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10.0, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (30, 30, 30, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (41, 41, 41, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (41, 41, 41, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (58, 58, 58, 255), category=dpg.mvThemeCat_Core)
        
            return menu_theme

theme = NodeTheme()
btn_theme = NodeButtonTheme()
menu_theme = NodeMenuTheme()