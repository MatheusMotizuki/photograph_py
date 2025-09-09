import dearpygui.dearpygui as dpg  # type: ignore
from PIL import Image
import numpy as np  # type: ignore

from source.nodes.core import NodeCore, get_available_position

from source.utils.theme import theme

class RGBNode(NodeCore):
    name = "RGB"
    tooltip = "Adjust RGB channels (decrease each color)"
    tag = "rgb"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None, node_tag: str | None = None, pos: list[int] | None = None):
        """
        Create a new RGB node. If node_tag/pos are provided (remote creation),
        use them so all clients create the same tag and position.
        """
        if node_tag is None:
            node_tag = "rgb_" + str(self.counter)
        else:
            self._register_tag(node_tag)
        idx = str(node_tag).rsplit("_", 1)[-1]

        node_tag_r = f"rgb_r_{idx}"
        node_tag_g = f"rgb_g_{idx}"
        node_tag_b = f"rgb_b_{idx}"
        with dpg.node(
            parent=parent,
            tag=node_tag,
            label="RGB",
            pos=(pos if pos is not None else get_available_position()),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_slider_int(tag=node_tag_r, label="Red", width=150, min_value=-255, max_value=255, default_value=0, clamped=True, callback=self.update_output)
                dpg.add_slider_int(tag=node_tag_g, label="Green", width=150, min_value=-255, max_value=255, default_value=0, clamped=True, callback=self.update_output)
                dpg.add_slider_int(tag=node_tag_b, label="Blue", width=150, min_value=-255, max_value=255, default_value=0, clamped=True, callback=self.update_output)

        self.settings[node_tag] = {node_tag_r:0, node_tag_g:0, node_tag_b:0}
        dpg.bind_item_theme(node_tag, theme.apply_theme(node_outline=(15,178,235,255)))
        self.last_node_id = node_tag
        return self.end()

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