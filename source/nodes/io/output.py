import dearpygui.dearpygui as dpg
import logging
import numpy as np
from PIL import Image
from typing import Optional

logger = logging.getLogger(__name__)

class OutputNode:
    """Output node for displaying images."""

    name = "Output"
    tooltip = "Where it all ends.\nNode to output an image file"

    MAX_DISPLAY_SIZE = (200, 200)

    def __init__(self, image):
        self.counter = 0
        self.image = image
        self.pillow_image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        self.protected = True

    def initialize(self):
        if dpg.does_item_exist("Output"):
            dpg.delete_item("Output")

        # Prepare display image
        display_image = self.image.copy()
        display_image.thumbnail(self.MAX_DISPLAY_SIZE, Image.Resampling.LANCZOS)
        if display_image.mode != 'RGBA':
            display_image = display_image.convert('RGBA')

        width, height = display_image.size
        texture_data = np.frombuffer(display_image.tobytes(), dtype=np.uint8) / 255.0
        texture_tag = f"output_texture_{id(self)}"

        with dpg.node(
            tag="Output", 
            label="Output", 
            pos=[1600, 600], 
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, tag="Output_attribute"):
                with dpg.texture_registry():
                    dpg.add_static_texture(
                        width,
                        height,
                        texture_data,
                        tag=texture_tag
                    )
                dpg.add_image(texture_tag)
                dpg.add_button(label="Download Image", callback=self._show_save_dialog)
                # Add file dialog (hidden by default)
                if not dpg.does_item_exist("output_save_dialog"):
                    with dpg.file_dialog(
                        directory_selector=False,
                        show=False,
                        callback=self._save_image_callback,
                        tag="output_save_dialog",
                        width=400,
                        height=200
                    ):
                        dpg.add_file_extension(".png")
                        dpg.add_file_extension(".jpg")
                        dpg.add_file_extension(".jpeg")
                        dpg.add_file_extension(".bmp")
    
    def _show_save_dialog(self):
        dpg.show_item("output_save_dialog")

    def _save_image_callback(self, sender, app_data):
        if self.pillow_image is not None and "file_path_name" in app_data:
            self.pillow_image.save(app_data["file_path_name"])
            print(f"Image saved to {app_data['file_path_name']}")