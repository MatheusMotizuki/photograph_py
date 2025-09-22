import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image
from source.nodes.core import NodeCore, get_available_position
from contextlib import suppress

class PreviewNode(NodeCore):
    name = "Preview"
    tooltip = "Preview the current state of edition"
    tag = "preview"
    DESCRIPTION = "Shows a preview of the image at this point in the processing chain"
    protected = False

    MAX_DISPLAY_SIZE = (200, 200)
    _instance_exists = False  # Class variable to track if instance exists

    def __init__(self):
        super().__init__()
        self.image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        self.texture_tag = None
        self.image_widget = None

    def run(self, image, tag):
        """Process the image and update the preview display."""
        self.image = image.copy()
        self._update_preview_display()
        return image  # Pass through the image unchanged

    def _update_preview_display(self):
        """Update the preview image display."""
        if self.image is None:
            return

        # Prepare display image
        display_image = self.image.copy()
        display_image.thumbnail(self.MAX_DISPLAY_SIZE, Image.Resampling.LANCZOS)
        if display_image.mode != 'RGBA':
            display_image = display_image.convert('RGBA')

        width, height = display_image.size
        texture_data = np.frombuffer(display_image.tobytes(), dtype=np.uint8) / 255.0

        # Delete old texture and image widget
        if self.texture_tag:
            with suppress(SystemError):
                dpg.delete_item(self.texture_tag)
        if self.image_widget:
            with suppress(SystemError):
                dpg.delete_item(self.image_widget)

        # Create new texture and image
        self.texture_tag = f"preview_texture_{self.counter}_{id(self)}"
        with dpg.texture_registry():
            dpg.add_static_texture(
                width,
                height,
                texture_data,
                tag=self.texture_tag
            )
        
        # Add new image widget to the input attribute
        self.image_widget = dpg.add_image(self.texture_tag, parent=self.input_attr)

    def cleanup(self):
        """Clean up resources when node is deleted."""
        if self.texture_tag:
            with suppress(SystemError):
                dpg.delete_item(self.texture_tag)
        if self.image_widget:
            with suppress(SystemError):
                dpg.delete_item(self.image_widget)
        PreviewNode._instance_exists = False

    def initialize(self, parent=None):
        # Check if a preview node already exists
        if PreviewNode._instance_exists:
            from source.utils.popup import Toast
            toast = Toast("Only one Preview node is allowed", 3000)
            toast.show()
            return

        # Mark that an instance now exists
        PreviewNode._instance_exists = True

        # Prepare initial display image
        display_image = self.image.copy()
        display_image.thumbnail(self.MAX_DISPLAY_SIZE, Image.Resampling.LANCZOS)
        if display_image.mode != 'RGBA':
            display_image = display_image.convert('RGBA')

        width, height = display_image.size
        texture_data = np.frombuffer(display_image.tobytes(), dtype=np.uint8) / 255.0
        self.texture_tag = f"preview_texture_{self.counter}_{id(self)}"

        node_tag = "preview_" + str(self.counter)
        
        with dpg.node(
            parent=parent,
            tag=node_tag,
            label="Preview",
            pos=get_available_position(),
            user_data=self,
        ):
            # Input attribute
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input, 
                tag=f"{node_tag}_input"
            ) as self.input_attr:
                with dpg.texture_registry():
                    dpg.add_static_texture(
                        width,
                        height,
                        texture_data,
                        tag=self.texture_tag
                    )
                self.image_widget = dpg.add_image(self.texture_tag)
                dpg.add_text("Input")

            # Output attribute (for chaining to other nodes)
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output,
                tag=f"{node_tag}_output"
            ):
                dpg.add_text("Output")

        # Initialize settings
        if not hasattr(self, 'settings'):
            self.settings = {}
        if node_tag not in self.settings:
            self.settings[node_tag] = {}

        self.end()