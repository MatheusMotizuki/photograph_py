import dearpygui.dearpygui as dpg
from PIL import Image
from typing import Optional
from pathlib import Path
import logging
import numpy as np
import io
import base64

from source.nodes.core import NodeCore, update
from source.client.socket_client import CURRENT_CLIENT

logger = logging.getLogger(__name__)

class InputNode(NodeCore):
    """Input node for loading and displaying images."""

    name = "Input"
    tooltip = "Where it all starts.\nInput node"

    # image processing constants
    MAX_DISPLAY_SIZE = (200, 200)
    SUPPORTED_FORMATS = {
        ".*": (255, 255, 255, 255),
        ".png": (255, 0, 0, 255),
        ".jpg": (0, 255, 0, 255),
        ".jpeg": (0, 0, 255, 255),
    }

    def __init__(self):
        self.protected = True
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
                dpg.add_text("Input")
                with dpg.group(tag=self._container_tag):
                    pass  # Image is added dynamically
                dpg.add_button(label="Upload file", callback=self._show_file_dialog)
    
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
        # Replicate image to collaborators if connected
        try:
            # prepare base64 of the original file bytes (preserve format)
            buf = io.BytesIO()
            fmt = self._current_image.format or "PNG"
            self._current_image.save(buf, format=fmt)
            bts = buf.getvalue()
            b64 = base64.b64encode(bts).decode("ascii")

            # DEBUG: print client/session info before emitting
            try:
                client_repr = repr(CURRENT_CLIENT)
                client_session = getattr(CURRENT_CLIENT, "current_session", None)
            except Exception:
                client_repr = None
                client_session = None
            logger.info(f"Attempting to replicate image. CURRENT_CLIENT={client_repr} session={client_session}")

            # Fallback: if CURRENT_CLIENT is None, try to find a socket client attached to a running editor
            if CURRENT_CLIENT is None:
                try:
                    import source.client.socket_client as scmod
                    if getattr(scmod, "CURRENT_CLIENT", None):
                        client = scmod.CURRENT_CLIENT
                        client_session = getattr(client, "current_session", None)
                        client_repr = repr(client)
                        logger.info(f"Found fallback socket client via module: {client_repr} session={client_session}")
                    else:
                        client = None
                except Exception:
                    client = None
            else:
                client = CURRENT_CLIENT

            # send via available client if we have a session id
            if client is not None and getattr(client, "current_session", None):
                payload = {
                    "type": "set_input_image",
                    "node_id": "Input",
                    "image_b64": b64,
                    "format": fmt,
                }
                client.emit_op(client.current_session, payload)
                logger.info("Replicated input image to session %s", client.current_session)
            else:
                logger.warning("Not replicating input image: no socket client or session id available")
        except Exception as e:
            logger.exception("Failed to replicate input image: %s", e)

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