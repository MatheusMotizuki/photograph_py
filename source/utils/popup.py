import dearpygui.dearpygui as dpg
import threading

class Toast:
    _tag = "toast"

    def __init__(self, message: str, duration: int = 3000):
        self._message = message
        self._duration = duration / 1000.0  # Convert to seconds

    def show(self):
        if dpg.does_item_exist(self._tag):
            dpg.delete_item(self._tag)

        with dpg.window(tag=self._tag, no_title_bar=True, no_resize=True, no_move=True,
                no_background=False, pos=[100, 100], width=300):
            dpg.add_text(self._message, pos=[25, 35])
            dpg.set_item_pos(self._tag, [dpg.get_viewport_width() - 330, 40])
            
        # Style the toast window
        with dpg.theme() as toast_theme:
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 2, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [30, 30, 30, 180], category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, [100, 41, 38, 255], category=dpg.mvThemeCat_Core)

        dpg.bind_item_theme(self._tag, toast_theme)

        dpg.show_item(self._tag)
        timer = threading.Timer(self._duration, self.hide)
        timer.start()

    def hide(self):
        if dpg.does_item_exist(self._tag):
            dpg.hide_item(self._tag)