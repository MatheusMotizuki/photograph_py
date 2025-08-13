from contextlib import suppress
import dearpygui.dearpygui as dpg
from typing import Optional
from PIL import Image
from pydantic import BaseModel
import numpy as np

from source.nodes.io import output

def available_pos() -> Optional[list[int]]:
    x, y = dpg.get_mouse_pos(local=False)
    return [max(0, x - 100), max(0, y - 100)]

class NodeCore:
    """Base class for all nodes in the graph."""
    def __init__(self):
        self.counter = 0
        self.update_output = update.update_output
        self.settings = {}
        self.protected = False
        self.is_plugin = False

    def end(self, tag, history):
        self.counter += 1

class Link(BaseModel):
    """Model for a link between nodes."""
    source: int
    target: int
    id: int

    def __str__(self):
        return f"Link from {self.source} to {self.target}"

    def __repr__(self):
        return self.__str__()
    
class Update:
    def __init__(self):
        self.path = []
        self.node_links = []

    def update_path(self):
        self.path.clear()
        for node in dpg.get_all_items():
            try:
                data_ = dpg.get_item_user_data(node)
            except SystemError:
                continue
            if data_ and data_.name == "Input":
                self.path.append(node)
                break

        while True:
            link = dpg.get_item_info(self.path[-1])["children"][1][-1]
            found = False
            for link_ in self.node_links:
                if link_.source == link:
                    try:
                        self.path.append(dpg.get_item_info(link_.target)["parent"])
                    except SystemError:
                        continue

                    found = True
                    break

            if not found:
                break

    def update_output(self, sender=None, app_data=None, history=True):
        if sender and app_data:
            try:
                node = dpg.get_item_info(dpg.get_item_info(sender)["parent"])["parent"]
                module = dpg.get_item_user_data(node)
            except SystemError:
                return

            alias = dpg.get_item_alias(node)
            module.settings[alias][sender] = app_data
        try:
            output = dpg.get_item_user_data(self.path[-1])
        except IndexError:
            dpg.delete_item("Output_attribute", children_only=True)
            return
        if output.name != "Output":
            dpg.delete_item("Output_attribute", children_only=True)
            return

        input_node = dpg.get_item_user_data("Input")
        image = input_node.current_image
        output = dpg.get_item_user_data(self.path[-1])
        if image is None:
            # Show placeholder image
            blank = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
            texture_data = np.frombuffer(blank.tobytes(), dtype=np.uint8) / 255.0
            texture_tag = "output_placeholder"
            width, height = blank.size

            dpg.delete_item("Output_attribute", children_only=True)
            with dpg.texture_registry():
                dpg.add_static_texture(
                    width,
                    height,
                    texture_data,
                    tag=texture_tag
                )
            dpg.add_image(texture_tag, parent="Output_attribute")
            return
        
        img_size = image.size
        for node in self.path[1:-1]:
            tag = dpg.get_item_alias(node)
            node = dpg.get_item_user_data(node)
            image = node.run(image, tag)

        dpg.delete_item(output.image)
        with suppress(SystemError):
            dpg.remove_alias(output.image)

        if not isinstance(output.image, str):
            output.image = "output_0"
        counter = output.image.split("_")[-1]
        output.image = "output_" + str(int(counter) + 1)
        output.pillow_image = image.copy()
        image.thumbnail((450, 450), Image.LANCZOS)
        with dpg.texture_registry():
            dpg.add_static_texture(
                image.width,
                image.height,
                np.frombuffer(image.tobytes(), dtype=np.uint8) / 255.0,
                tag=output.image,
            )
        dpg.delete_item("Output_attribute", children_only=True)
        dpg.add_image(output.image, parent="Output_attribute")
        if output.pillow_image.size != img_size:
            dpg.add_spacer(height=5, parent="Output_attribute")
            dpg.add_text(
                f"Image size: {output.pillow_image.width}x{output.pillow_image.height}", parent="Output_attribute"
            )



update = Update()