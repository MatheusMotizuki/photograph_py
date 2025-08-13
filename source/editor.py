from PIL import Image
import dearpygui.dearpygui as dpg

from source.nodes.io.input import InputNode
from source.nodes.io.output import OutputNode

from source.nodes.submodules.brightness import BrightnessNode
from source.nodes.submodules.rotate import RotateNode
from source.nodes.submodules.monochrome import MonochromeNode
from source.nodes.submodules.rgb import RGBNode

from source.nodes.core import Link, update
from source.utils.theme import btn_theme, menu_theme
from source.utils.popup import Toast

class PhotoGraphEditor:
    """Main class for the PhotoGraph editor."""

    name = "photoGraph Editor"
    tag = "photoGraphEditor"
    node_menu_ctx = "node_context_menu"
    node_info_ctx = "node_info_menu"

    def __init__(self, parent: str = "PhotoGraphMain"):
        """Initialize the PhotoGraph editor."""
        blank_image = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        self.parent = parent

        self.submodules = [
            InputNode(), 
            BrightnessNode(), 
            RotateNode(), 
            MonochromeNode(), 
            RGBNode(), 
            OutputNode(blank_image)
        ]

    def initialize(self) -> None:
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
            self.submodules[-1].initialize()  # OutputNode

            self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Setup mouse event handlers."""
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(dpg.mvMouseButton_Right, callback=self._handle_popup)
            dpg.add_mouse_release_handler(dpg.mvMouseButton_Left, callback=self._handle_popup)
            dpg.add_key_press_handler(dpg.mvKey_Delete, callback=self.delete_nodes)

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

    def _on_link_deleted(self, _sender, app_data) -> None:
        dpg.delete_item(app_data)
        for link in update.node_links:
            if link.id == app_data:
                update.node_links.remove(link)
                break

        update.update_path()
        update.update_output()

    def _handle_popup(self, _sender, app_data):
        if app_data == 1 and dpg.is_item_hovered(self.tag):
            selected_nodes = dpg.get_selected_nodes(self.tag)

            if len(selected_nodes) != 0:
                # Show node info menu for selected nodes
                if not dpg.does_item_exist(self._node_info_ctx):
                    # Get data from all selected nodes
                    selected_data = [dpg.get_item_user_data(node) for node in selected_nodes]
                    self._node_info_menu(selected_data)
                dpg.show_item(self._node_info_ctx)
                dpg.set_item_pos(self._node_info_ctx, dpg.get_mouse_pos(local=False))
                # Hide the main context menu if it's open
                if dpg.does_item_exist(self.node_menu_ctx):
                    dpg.hide_item(self.node_menu_ctx)
            else:
                # Show main context menu when no nodes are selected
                if not dpg.does_item_exist(self.node_menu_ctx):
                    self._menu_context()
                dpg.show_item(self.node_menu_ctx)
                dpg.set_item_pos(self.node_menu_ctx, dpg.get_mouse_pos(local=False))
                # Hide the node info menu if it's open
                if dpg.does_item_exist(self.node_info_ctx):
                    dpg.hide_item(self.node_info_ctx)
        else:
            # Hide both menus when clicking elsewhere
            if dpg.does_item_exist(self.node_menu_ctx):
                dpg.hide_item(self.node_menu_ctx)
            if dpg.does_item_exist(self.node_info_ctx):
                dpg.hide_item(self.node_info_ctx)

    def _menu_context(self):
        """Context menu for the node editor"""
        with dpg.window(
            tag=self.node_menu_ctx,
            no_move=True,
            no_close=True,
            no_resize=True,
            no_collapse=True,
            show=False,
            label="Add Node",
        ):
            # with dpg.child_window(
            #     width=200,
            #     height=25,
            #     border=False,
            #     tag="node_context_menu_buttons",
            # ):
            #     with dpg.group(horizontal=True):
            #         dpg.add_button(
            #             label="normal",
            #             tag="normal_node_button",
            #             callback=None,
            #             width=100,
            #             height=25
            #         )
            #         dpg.add_button(
            #             label="shaders",
            #             tag="shaders_node_button",
            #             callback=toggle_option,
            #             width=100,
            #             height=25
            #         )

            #     if option:
            #         dpg.bind_item_theme("normal_node_button", btn_theme.apply_theme(border_color=(66, 171, 73, 255)))
            #     else:
            #         dpg.bind_item_theme("shaders_node_button", btn_theme.apply_theme(border_color=(227, 23, 62, 255)))


            # dpg.add_spacer(height=5)
            # dpg.add_separator()

            dpg.add_spacer(height=5, parent="node_context_menu")
            for i, sub in enumerate(self.submodules[1:-1]):
                dpg.add_button(
                    label=sub.name, 
                    tag=sub.tag+"_popup", 
                    callback=lambda sender, app_data, user_data: user_data[0].initialize(parent=user_data[1]), 
                    user_data=(sub, self.tag), 
                    indent=3, 
                    width=200
                )
                dpg.add_spacer(height=5)

        dpg.bind_item_theme("node_context_menu", menu_theme.apply_theme())
        
        colors = [
            (227, 23, 62, 255),  # Brightness
            (255, 150, 79, 255),  # Rotate
            (15, 178, 235, 255),  # Monochrome
            (169, 249, 248, 255),  # Cyan
            (255, 124, 255, 255),  # Magenta
            (255, 253, 116, 255),  # Yellow
            (169, 169, 169, 255),  # Orange
        ]

        border_size = 1.5
        
        for i, sub in enumerate(self.submodules[1:-1]):
            color = colors[i % len(colors)]  # Cycle through colors if more buttons than colors
            dpg.bind_item_theme(sub.tag+"_popup", btn_theme.apply_theme(border_color=color, border_size=border_size))

    def _node_info_menu(self, node_data=None):
        """Context menu for node information"""
        with dpg.window(
            tag=self.node_info_ctx,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            show=False,
            label="Node information",
        ):
            dpg.add_text(f"Node is {node_data.name if node_data else 'Unknown'}", color=(248, 248, 248))
            dpg.add_text(f"{node_data.description if node_data else 'No description available.'}", color=(200, 200, 200))
            if not node_data.protected:
                dpg.add_spacer(height=5)
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Delete Node",
                        callback=None,
                    )
                    dpg.add_button(
                        label="Duplicate Node",
                        callback=None,
                    )

    def delete_nodes(self, sender=None, app_data=None):
        print("delete_nodes called")
        selected_nodes = dpg.get_selected_nodes(self.tag)
        print(f"Selected nodes for deletion: {selected_nodes}")
        for node in selected_nodes:
            data = dpg.get_item_user_data(node)
            print(f"Processing node: {node}, user_data: {data}")
            if data.protected:
                print(f"Node {node} is protected and cannot be deleted.")
                toast = Toast("Cannot delete protected nodes", 3000)
                toast.show()
                continue

            # Remove all links associated with the node
            node_links = dpg.get_item_info(node)["children"][1]
            print(f"Node {node} links to be checked for removal: {node_links}")

            dpg.delete_item(node)
            print(f"Node {node} deleted from UI.")

            # Remove links from update.node_links
            removed_links = []
            for l in update.node_links[:]:
                if l.source in node_links or l.target in node_links:
                    update.node_links.remove(l)
                    removed_links.append(l)
            print(f"Removed links for node {node}: {removed_links}")

        update.update_path()
        update.update_output()

    def _delete_links(self):
        pass

    def _duplicate_nodes(self):
        pass