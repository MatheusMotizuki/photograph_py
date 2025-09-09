import dearpygui.dearpygui as dpg
from PIL import Image
from source.nodes.core import NodeCore, get_available_position

from source.utils.theme import theme
import moderngl
import numpy as np

class PosterizationNode(NodeCore):
    name = "Posterization"
    tooltip = "Reduces smooth gradients into flat bands of color"
    tag = "posterization"

    def __init__(self):
        super().__init__()

    def initialize(self, parent=None):
        node_tag = "posterization_" + str(self.counter)
        with dpg.node(
            parent=parent,
            tag=node_tag,
            label="Posterization",
            pos=get_available_position(),
            user_data=self,
        ):
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input):
                dpg.add_text("input")
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output):
                dpg.add_text("output")
            dpg.bind_item_theme(node_tag, theme.apply_theme(node_outline=(169, 169, 169, 255)))
        
        self.settings[node_tag] = {}
        self.last_node_id = node_tag
        return self.end()
    
    def run(self, image: Image.Image, tag: str) -> Image.Image:

        # Create context
        ctx = moderngl.create_standalone_context()

        # Prepare image (ensure RGB)
        input_image = image.convert("RGB").transpose(Image.FLIP_TOP_BOTTOM)
        texture = ctx.texture(input_image.size, 3, input_image.tobytes())
        texture.use()

        # Vertex Shader
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

        # Fragment Shader (Posterization)
        fragment_shader = """
        #version 330
        uniform sampler2D Texture;
        in vec2 uv;
        out vec4 f_color;

        void main() {
            vec3 color = texture(Texture, uv).rgb;
            float levels = 4.0;
            color = floor(color * levels) / levels;
            f_color = vec4(color, 1.0);
        }
        """

        # Compile shaders
        prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

        # Fullscreen quad (x,y,u,v)
        quad_vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype="f4")

        vbo = ctx.buffer(quad_vertices.tobytes())
        vao = ctx.simple_vertex_array(prog, vbo, "in_vert", "in_tex")

        # Render to framebuffer
        fbo = ctx.simple_framebuffer(input_image.size)
        fbo.use()
        vao.render(moderngl.TRIANGLE_STRIP)

        # Read pixels back
        data = fbo.read(components=3)
        output_image = Image.frombytes("RGB", input_image.size, data).transpose(Image.FLIP_TOP_BOTTOM)

        # Convert back to RGBA to match pipeline
        return output_image.convert("RGBA")