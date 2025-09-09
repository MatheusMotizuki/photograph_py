import dearpygui.dearpygui as dpg
import logging
import numpy as np
from PIL import Image
from typing import Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class OutputNode:
    """Output node for displaying images."""

    name = "Output"
    tooltip = "Where it all ends.\nNode to output an image file"
    protected = True

    MAX_DISPLAY_SIZE = (200, 200)

    def __init__(self, image):
        self.counter = 0
        self.protected = True
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
            # image attribute (this is the only part update_output will replace)
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, tag="Output_image_attribute"):
                with dpg.texture_registry():
                    dpg.add_static_texture(
                        width,
                        height,
                        texture_data,
                        tag=texture_tag
                    )
                dpg.add_image(texture_tag)

            # controls attribute (persistent across updates) - buttons, dialogs, etc.
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static, tag="Output_controls"):
                dpg.add_button(label="Download Image", callback=self._show_save_dialog)
                dpg.add_button(label="Quick Save Output", callback=self.quick_save)
                # Add file dialog (hidden by default) under controls so it isn't removed by updates
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
                        
        # Add Export menu entries under existing File menu (created earlier)
        try:
            # add menu items if file menu exists and they are not already present
            if dpg.does_item_exist("file"):
                if not dpg.does_item_exist("menu_export_output"):
                    dpg.add_menu_item(tag="menu_export_output", label="Export Output...", parent="file", callback=lambda: self._show_save_dialog())
                if not dpg.does_item_exist("menu_quick_save_output"):
                    dpg.add_menu_item(tag="menu_quick_save_output", label="Quick Save Output", parent="file", callback=lambda: self.quick_save())
        except Exception:
            # non-fatal; menu isn't required for the save functionality
            pass

    def _show_save_dialog(self):
        dpg.show_item("output_save_dialog")

    def _save_image_callback(self, sender, app_data):
        if self.pillow_image is not None and "file_path_name" in app_data:
            self.pillow_image.save(app_data["file_path_name"])
            print(f"Image saved to {app_data['file_path_name']}")

    def quick_save(self, sender=None, app_data=None):
        """Quick save the current output image to ~/Pictures or cwd with timestamped filename."""
        if self.pillow_image is None:
            print("Quick save failed: no output image available")
            return
        try:
            pictures = os.path.expanduser("~/Pictures")
            if not os.path.isdir(pictures):
                pictures = os.getcwd()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photograph_output_{timestamp}.png"
            path = os.path.join(pictures, filename)
            self.pillow_image.save(path, format="PNG")
            print(f"Output quick-saved to: {path}")
        except Exception as e:
            print(f"Quick save failed: {e}")