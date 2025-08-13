from PIL import Image
import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional

from source.nodes.io.input import InputNode
from source.nodes.io.output import OutputNode

from source.nodes.submodules.brightness import BrightnessNode
from source.nodes.submodules.rotate import RotateNode
from source.nodes.submodules.monochrome import MonochromeNode
from source.nodes.submodules.rgb import RGBNode

from source.nodes.core import Link, update

class PhotoGraphEditor:
    """Main class for the PhotoGraph editor."""

    def __init__(self, parent: str = "PhotoGraphMain"):
        """Initialize the PhotoGraph editor."""
        self.name = "PhotoGraph Editor"
        self.tag = "photoGraphEditor"
        self.node_menu_ctx = "node_menu_context"
        self.node_detail_ctx = "node_detail_context"
        self.parent = parent

        blank_image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        self.submodules = [InputNode(), BrightnessNode(), RotateNode(), MonochromeNode(), RGBNode(), OutputNode(blank_image)]
        self.links: Dict = {}
        self.registry: List = []

    def _initialize(self) -> None:
        """Initialize the PhotoGraph editor."""
        self._show_startup_message()
        self._create_node_editor()

    def _show_startup_message(self) -> None:
        """Display a startup message."""
        print(f"Welcome to {self.name}!")

    def _create_node_editor(self) -> None:
        """Create the main node editor interface."""
        with dpg.node_editor(
            tag=self.tag,
            parent=self.parent,
            callback=self._on_link_created,
            delink_callback=self._on_link_deleted,
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
        ):
            self.submodules[0].initialize()  # InputNode
            self.submodules[1].initialize()  # MonochromeNode
            self.submodules[2].initialize()  # RotateNode
            self.submodules[3].initialize()  # BrightnessNode
            self.submodules[4].initialize()  # RGBNode
            self.submodules[-1].initialize()  # OutputNode

            self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Setup mouse event handlers."""
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(dpg.mvMouseButton_Right, callback=self._handle_right_click)
            dpg.add_mouse_release_handler(dpg.mvMouseButton_Left, callback=self._handle_left_release)

    def _on_link_created(self, sender, app_data):
        """Handle node link creation."""
        for link in update.node_links:
            if link.source == app_data[0]:
                try:
                    dpg.delete_item(link.id)
                except SystemError:
                    continue
                update.node_links.remove(link)

        link = dpg.add_node_link(app_data[0], app_data[1], parent=sender)
        update.node_links.append(Link(source=app_data[0], target=app_data[1], id=int(link)))
        update.update_path()
        update.update_output()

    def _on_link_deleted(self, sender, app_data) -> None:
        dpg.delete_item(app_data)
        for link in update.node_links:
            if link.id == app_data:
                update.node_links.remove(link)
                break

        update.update_path()
        update.update_output()

    def _handle_right_click(self, sender, app_data) -> None:
        """Handle right mouse click events."""
        # TODO: Implement context menu logic
        pass

    def _handle_left_release(self, sender, app_data) -> None:
        """Handle left mouse release events."""
        # TODO: Implement selection logic
        pass
