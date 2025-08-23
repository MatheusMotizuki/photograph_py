"""Core node system for the photograph application."""

from contextlib import suppress
from typing import Optional, Any, Dict, List
import logging

import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image
from pydantic import BaseModel, Field

# Constants
MOUSE_OFFSET = 100

logger = logging.getLogger(__name__)

def get_available_position() -> Optional[list[int]]:
    """Get available position for new nodes based on mouse position.
    
    Returns:
        List of [x, y] coordinates offset from mouse position.
    """
    x, y = dpg.get_mouse_pos(local=False)
    return [max(0, x - MOUSE_OFFSET), max(0, y - MOUSE_OFFSET)]

class NodeCore:
    """Base class for all nodes in the graph."""
    def __init__(self):
        self.counter = 0
        self.update_output = update.update_output
        self.settings = {}
        self.protected = False
        self.is_plugin = False

    def end(self):
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
        if image is None or image == "": # try to solve infinite display bug
            dpg.delete_item("Output_attribute", children_only=True)
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