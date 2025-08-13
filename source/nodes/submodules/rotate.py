import dearpygui.dearpygui as dpg
from PIL import Image
from typing import Optional

from source.nodes.core import NodeCore, available_pos

class RotateNode(NodeCore):
    name = "Rotate"
    tooltip = "Rotate image"

    def __init__(self):
        super().__init__()

    def initialize(self, history=True):
        with dpg.node(
            parent="MainNodeEditor",
            tag="rotate_" + str(self.counter),
            label="Rotate",
            pos=available_pos(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_slider_int(
                    tag="rotate_degrees_" + str(self.counter),
                    label="Degrees",
                    width=150,
                    min_value=0,
                    max_value=360,
                    default_value=0,
                    clamped=True,
                    callback=self.update_output,
                )

        tag = "rotate_" + str(self.counter)
        self.settings[tag] = {"rotate_degrees_" + str(self.counter): 0}
        self.end(tag, history)

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        tag_id = tag.split("_")[-1]
        degrees = self.settings["rotate_" + tag_id]["rotate_degrees_" + tag_id]
        return image.rotate(degrees)