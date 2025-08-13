import dearpygui.dearpygui as dpg
from PIL import Image
from typing import Optional
from pathlib import Path
import logging
import numpy as np

from source.nodes.core import NodeCore, update

logger = logging.getLogger(__name__)

class InputNode(NodeCore):
    """Input node for loading and displaying images."""

    name = "Input"
    tooltip = "Where it all starts.\nNode to input an image file"

    # image processing constants
    MAX_DISPLAY_SIZE = (200, 200)
    SUPPORTED_FORMATS = {
        ".png": (255, 0, 0, 255),
        ".jpg": (0, 255, 0, 255),
        ".jpeg": (0, 0, 255, 255),
        ".bmp": (255, 255, 0, 255),
    }

    def __init__(self):
        self._protected = True
        self._current_image: Optional[Image.Image] = None
        self._texture_tag = f"input_texture"
        self._image_tag = f"input_image"
        self._container_tag = f"input_image_container"

    def initialize(self):
        """Initialize the input node."""
        if dpg.does_item_exist("Input"):
            dpg.delete_item("Input")

        with dpg.node(tag="Input", label="Input", pos=[100, 100], user_data=self):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("Input Image")
                with dpg.group(tag=self._container_tag):
                    pass  # Image is added dynamically
                dpg.add_button(label="Upload Image", callback=self._show_file_dialog)
    
    def _show_file_dialog(self):
        """Show file dialog for image selection."""
        dialog_tag = "file_dialog_id"

        if dpg.does_item_exist(dialog_tag):
            dpg.delete_item(dialog_tag)
        
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._handle_file_selection,
            tag=dialog_tag,
            width=700,
            height=400
        ):
            for ext, color in self.SUPPORTED_FORMATS.items():
                dpg.add_file_extension(ext, color=color)

    def _handle_file_selection(self, sender, app_data):
        """Handle file selection from dialog."""
        file_path = Path(app_data['file_path_name'])

        try:
            self._current_image = Image.open(file_path)
            self._display_image()
            logger.info(f"Image loaded: {file_path}")
        except Exception as e:
            logger.error(f"Failed to open image {file_path}: {e}")
        # update.update_output()

    def _display_image(self):
        """Display the loaded image in the node."""
        if not self._current_image:
            return

        # Prepare display image
        display_image = self._current_image.copy()
        display_image.thumbnail(self.MAX_DISPLAY_SIZE, Image.Resampling.LANCZOS)
        
        if display_image.mode != 'RGBA':
            display_image = display_image.convert('RGBA')

        # Convert to texture data
        image_array = np.array(display_image, dtype=np.float32) / 255.0
        texture_data = image_array.flatten()

        # Clean up existing items
        for tag in [self._texture_tag, self._image_tag]:
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)

        # Create texture and image
        width, height = display_image.size
        with dpg.texture_registry():
            dpg.add_raw_texture(
                width=width,
                height=height,
                default_value=texture_data,
                format=dpg.mvFormat_Float_rgba,
                tag=self._texture_tag
            )

        dpg.add_image(self._texture_tag, tag=self._image_tag, parent=self._container_tag)

    def process(self, input_image: Optional[Image.Image], node_tag: str) -> Optional[Image.Image]:
        """Process method for node graph execution."""
        return self._current_image

    @property
    def current_image(self) -> Optional[Image.Image]:
        """Get the currently loaded image."""
        return self._current_image

    @property
    def has_image(self) -> bool:
        """Check if an image is currently loaded."""
        return self._current_image is not None