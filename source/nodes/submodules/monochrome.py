import dearpygui.dearpygui as dpg
from PIL import Image
from source.nodes.core import NodeCore, available_pos

class MonochromeNode(NodeCore):
    name = "Monochrome"
    tooltip = "Convert image to monochrome (grayscale)"

    def __init__(self):
        super().__init__()

    def initialize(self, history=True):
        with dpg.node(
            parent="MainNodeEditor",
            tag="monochrome_" + str(self.counter),
            label="Monochrome",
            pos=available_pos(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("output")
        tag = "monochrome_" + str(self.counter)
        self.settings[tag] = {}
        self.end(tag, history)

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        return image.convert("L").convert("RGBA")