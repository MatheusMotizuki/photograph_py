import dearpygui.dearpygui as dpg
from PIL import Image
from source.nodes.core import NodeCore, get_available_position

from source.utils.theme import theme

import moderngl
import numpy as np

class DitherNode(NodeCore):
    name = "Dither"
    tooltip = "Adds dither effect to an image"
    tag = "dither"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None, node_tag: str | None = None, pos: list[int] | None = None):
        if node_tag is None:
            node_tag = "dither_" + str(self.counter)
        else:
            self._register_tag(node_tag)
        idx = str(node_tag).rsplit("_", 1)[-1]

        with dpg.node(
            parent=parent,
            tag=node_tag,
            label="Dither",
            pos=(pos if pos is not None else get_available_position()),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("output")
            dpg.bind_item_theme(node_tag, theme.apply_theme(node_outline=(255, 253, 116, 255)))
        
        self.settings[node_tag] = {}
        self.last_node_id = node_tag
        return self.end()

    def run(self, image: Image.Image, tag: str) -> Image.Image:
        # Ensure image is RGB
        img = image.convert("RGB")
        width, height = img.size

        # Create moderngl context
        ctx = moderngl.create_standalone_context()

        # Upload image as texture
        texture = ctx.texture((width, height), 3, img.tobytes())
        texture.use()

        # Vertex shader
        vertex_shader = """
        #version 330
        in vec2 in_vert;
        in vec2 in_tex;
        out vec2 uv;
        void main() {
            gl_Position = vec4(in_vert, 0.0, 1.0);
            uv = in_tex;
        }
        """

        # Fragment shader (Ordered Dithering with Bayer matrix)
        fragment_shader = """
        #version 330
        uniform sampler2D Texture;
        in vec2 uv;
        out vec4 f_color;

        const int N = 4;
        const float bayer[16] = float[16](
             0.0/16.0,  8.0/16.0,  2.0/16.0, 10.0/16.0,
            12.0/16.0,  4.0/16.0, 14.0/16.0,  6.0/16.0,
             3.0/16.0, 11.0/16.0,  1.0/16.0,  9.0/16.0,
            15.0/16.0,  7.0/16.0, 13.0/16.0,  5.0/16.0
        );

        void main() {
            vec3 color = texture(Texture, uv).rgb;
            ivec2 pos = ivec2(floor(gl_FragCoord.xy));
            int index = (pos.x % N) + (pos.y % N) * N;
            float threshold = bayer[index];
            vec3 result;
            result.r = (color.r < threshold) ? 0.0 : 1.0;
            result.g = (color.g < threshold) ? 0.0 : 1.0;
            result.b = (color.b < threshold) ? 0.0 : 1.0;
            f_color = vec4(result, 1.0);
        }
        """

        # Compile shaders
        prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        # Fullscreen quad
        quad_vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype="f4")
        vbo = ctx.buffer(quad_vertices.tobytes())
        vao = ctx.simple_vertex_array(prog, vbo, "in_vert", "in_tex")

        # Render to framebuffer
        fbo = ctx.simple_framebuffer((width, height))
        fbo.use()
        vao.render(moderngl.TRIANGLE_STRIP)

        # Read pixels and convert to PIL Image
        data = fbo.read(components=3)
        out_img = Image.frombytes("RGB", (width, height), data)
        return out_img.convert("RGBA")