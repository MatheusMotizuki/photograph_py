from dearpygui import dearpygui as dpg
from PIL import Image, ImageEnhance

from source.nodes.core import NodeCore, available_pos
from source.utils.theme import theme


class BrightnessNode(NodeCore):
    name = "Brightness"
    tooltip = "Adjust brightness"
    tag = "brightness"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None):
        with dpg.node(
            parent=parent,
            tag="brightness_" + str(self.counter),
            label="Brightness",
            pos=available_pos(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_slider_int(
                    tag="brightness_percentage_" + str(self.counter),
                    label="Brightness",  # Add this fixed label
                    width=150,
                    max_value=100,
                    min_value=1,
                    default_value=1,
                    clamped=True,
                    callback=self.update_output,
                )
            dpg.bind_item_theme("brightness_"+str(self.counter), theme.apply_theme(node_outline=(227, 23, 62, 255)))

        tag = "brightness_" + str(self.counter)
        self.settings[tag] = {"brightness_percentage_" + str(self.counter): 1}
        self.end()

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        tag = tag.split("_")[-1]
        percent = self.settings["brightness_" + tag]["brightness_percentage_" + tag]
        return ImageEnhance.Brightness(image).enhance(percent / 25)