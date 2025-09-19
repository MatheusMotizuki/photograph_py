from dearpygui import dearpygui as dpg
from pydub import AudioSegment

from source.nodes.core import NodeCore, get_available_position
from source.utils.theme import theme

class VolumeAudioNode(NodeCore):
    name = "Volume"
    tooltip = "modify a audio volume"
    tag = "volume"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None, node_tag: str | None = None, pos: list[None] | None = None):
        if node_tag is None:
            node_tag = "volumeAudio_" + str(self.counter)
        else:
            self._register_tag(node_tag)
        idx = str(node_tag).rsplit("_", 1)[-1]

        with dpg.node(
            parent=parent,
            tag=node_tag,
            label="Volume",
            pos=(pos if pos is not None else get_available_position()),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_slider_int(tag=f"volume_val_{idx}", label="Value", width=150, min_value=0, max_value=200, default_value=100, clamped=True, callback=self.update_output)
            dpg.bind_item_theme(node_tag, theme.apply_theme(node_outline=(100, 200, 255, 255)))

            self.settings[node_tag] = {f"volume_val_{idx}": 100}
            self.last_node_id = node_tag
            return self.end()

    def run(self):
        pass