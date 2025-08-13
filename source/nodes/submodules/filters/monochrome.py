import dearpygui.dearpygui as dpg
from PIL import Image
from source.nodes.core import NodeCore, available_pos

from source.utils.theme import theme

class MonochromeNode(NodeCore):
    name = "Monochrome"
    tooltip = "Convert image to monochrome (grayscale)"
    tag = "monochrome"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None):
        with dpg.node(
            parent=parent,
            tag="monochrome_" + str(self.counter),
            label="Monochrome",
            pos=available_pos(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("output")
            dpg.bind_item_theme("monochrome_"+str(self.counter), theme.apply_theme(node_outline=(15, 178, 235, 255)))
        
        tag = "monochrome_" + str(self.counter)
        self.settings[tag] = {}
        self.end()

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        return image.convert("L").convert("RGBA")