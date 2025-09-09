import dearpygui.dearpygui as dpg
from PIL import Image
from source.nodes.core import NodeCore, get_available_position

from source.utils.theme import theme

class MonochromeNode(NodeCore):
    name = "Monochrome"
    tooltip = "Convert image to monochrome (grayscale)"
    tag = "monochrome"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None):
        node_tag = "monochrome_" + str(self.counter)
        with dpg.node(
            parent=parent,
            tag=node_tag,
            label="Monochrome",
            pos=get_available_position(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("output")
            dpg.bind_item_theme(node_tag, theme.apply_theme(node_outline=(169, 249, 248, 255)))
        
        self.settings[node_tag] = {}
        self.last_node_id = node_tag
        return self.end()

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        return image.convert("L").convert("RGBA")