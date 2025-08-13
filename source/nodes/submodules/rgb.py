import dearpygui.dearpygui as dpg
from PIL import Image
import numpy as np

from source.nodes.core import NodeCore, available_pos

class RGBNode(NodeCore):
    name = "RGB"
    tooltip = "Adjust RGB channels (decrease each color)"
    tag = "rgb"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None):
        with dpg.node(
            parent=parent,
            tag="rgb_" + str(self.counter),
            label="RGB",
            pos=available_pos(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_slider_int(
                    tag="rgb_r_" + str(self.counter),
                    label="Red",
                    width=150,
                    min_value=-255,
                    max_value=255,
                    default_value=0,
                    clamped=True,
                    callback=self.update_output,
                )
                dpg.add_slider_int(
                    tag="rgb_g_" + str(self.counter),
                    label="Green",
                    width=150,
                    min_value=-255,
                    max_value=255,
                    default_value=0,
                    clamped=True,
                    callback=self.update_output,
                )
                dpg.add_slider_int(
                    tag="rgb_b_" + str(self.counter),
                    label="Blue",
                    width=150,
                    min_value=-255,
                    max_value=255,
                    default_value=0,
                    clamped=True,
                    callback=self.update_output,
                )

        tag = "rgb_" + str(self.counter)
        self.settings[tag] = {
            "rgb_r_" + str(self.counter): 0,
            "rgb_g_" + str(self.counter): 0,
            "rgb_b_" + str(self.counter): 0,
        }
        self.end()

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        tag_id = tag.split("_")[-1]
        r_decrease = self.settings["rgb_" + tag_id]["rgb_r_" + tag_id]
        g_decrease = self.settings["rgb_" + tag_id]["rgb_g_" + tag_id]
        b_decrease = self.settings["rgb_" + tag_id]["rgb_b_" + tag_id]

        arr = np.array(image).astype(np.int16)
        arr[..., 0] = np.clip(arr[..., 0] + r_decrease, 0, 255)
        arr[..., 1] = np.clip(arr[..., 1] + g_decrease, 0, 255)
        arr[..., 2] = np.clip(arr[..., 2] + b_decrease, 0, 255)
        return Image.fromarray(arr.astype(np.uint8), mode=image.mode)