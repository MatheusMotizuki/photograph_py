import dearpygui.dearpygui as dpg
from PIL import Image, ImageFilter
import numpy as np

from source.nodes.core import NodeCore, get_available_position

from source.utils.theme import theme

class BlurNode(NodeCore):
    name = "Blur"
    tooltip = "Apply blur filter"
    tag = "blur"

    BLUR_TYPES = {
        "BoxBlur": ImageFilter.BoxBlur,
        "GaussianBlur": ImageFilter.GaussianBlur,
    }

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None):
        with dpg.node(
            parent=parent,
            tag="blur_" + str(self.counter),
            label="Blur",
            pos=get_available_position(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_combo(
                    items=list(self.BLUR_TYPES.keys()),
                    default_value="BoxBlur",
                    tag="blur_type_" + str(self.counter),
                    label="Blur Type",
                    width=150,
                    callback=self.update_output,
                )
                dpg.add_slider_int(
                    tag="blur_strength_" + str(self.counter),
                    label="Strength",
                    width=150,
                    min_value=0,
                    max_value=20,
                    default_value=0,
                    clamped=True,
                    callback=self.update_output,
                )
            dpg.bind_item_theme("blur_"+str(self.counter), theme.apply_theme(node_outline=(255, 150, 79, 255)))

        tag = "blur_" + str(self.counter)
        self.settings[tag] = {
            "blur_type_" + str(self.counter): "BoxBlur",
            "blur_strength_" + str(self.counter): 0,
        }
        self.end()

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        tag_id = tag.split("_")[-1]
        blur_type = self.settings["blur_" + tag_id]["blur_type_" + tag_id]
        strength = self.settings["blur_" + tag_id]["blur_strength_" + tag_id]

        if strength == 0 or blur_type not in self.BLUR_TYPES:
            return image

        if blur_type == "BoxBlur":
            return image.filter(ImageFilter.BoxBlur(strength))
        elif blur_type == "GaussianBlur":
            return image.filter(ImageFilter.GaussianBlur(strength))
        else:
            return image