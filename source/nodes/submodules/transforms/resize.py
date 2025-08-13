import dearpygui.dearpygui as dpg
from PIL import Image

from source.nodes.core import NodeCore, available_pos

class ResizeNode(NodeCore):
    name = "Resize"
    tooltip = "Resize image"
    tag = "resize"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None):
        with dpg.node(
            parent=parent,
            tag="resize_" + str(self.counter),
            label="Resize",
            pos=available_pos(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_input_int(
                    tag="resize_width_" + str(self.counter),
                    label="Width",
                    width=100,
                    min_value=1,
                    max_value=4096,
                    default_value=800,
                    callback=self.update_output,
                )
                dpg.add_input_int(
                    tag="resize_height_" + str(self.counter),
                    label="Height",
                    width=100,
                    min_value=1,
                    max_value=4096,
                    default_value=600,
                    callback=self.update_output,
                )

        tag = "resize_" + str(self.counter)
        self.settings[tag] = {
            "resize_width_" + str(self.counter): 100,
            "resize_height_" + str(self.counter): 100,
        }
        self.end()

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        tag_id = tag.split("_")[-1]
        width = min(self.settings["resize_" + tag_id]["resize_width_" + tag_id], 4096)
        height = min(self.settings["resize_" + tag_id]["resize_height_" + tag_id], 4096)
        if width > 0 and height > 0:
            return image.resize((width, height), Image.Resampling.LANCZOS)