from dearpygui import dearpygui as dpg
from PIL import Image, ImageEnhance

from source.nodes.core import NodeCore, get_available_position
from source.utils.theme import theme

class BrightnessNode(NodeCore):
    name = "Brightness"
    tooltip = "Adjust brightness"
    tag = "brightness"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None, node_tag: str | None = None, pos: list[int] | None = None):
        if node_tag is None:
            node_tag = "brightness_" + str(self.counter)
        else:
            self._register_tag(node_tag)
        idx = str(node_tag).rsplit("_", 1)[-1]

        with dpg.node(
            parent=parent,
            tag=node_tag,
            label="Brightness",
            pos=(pos if pos is not None else get_available_position()),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_slider_int(tag=f"brightness_val_{idx}", label="Value", width=150, min_value=0, max_value=255, default_value=0, clamped=True, callback=self.update_output)
            dpg.bind_item_theme(node_tag, theme.apply_theme(node_outline=(227, 23, 62, 255)))

        self.settings[node_tag] = {f"brightness_val_{idx}": 0}
        self.last_node_id = node_tag
        return self.end()

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        # Expect tag like "brightness_<idx>" — extract idx and lookup settings
        idx = str(tag).rsplit("_", 1)[-1]
        node_key = f"brightness_{idx}"
        value_key = f"brightness_val_{idx}"
        percent = self.settings.get(node_key, {}).get(value_key, 255)
        factor = float(percent) / 127.5 if percent else 0.0
        return ImageEnhance.Brightness(image).enhance(factor)