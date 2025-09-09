import dearpygui.dearpygui as dpg
import sys
import os

from source.editor import PhotoGraphEditor
from source.client.socket_client import SocketClient
import threading
import time

# start helper functions
def setup_fonts():
    """Setup fonts"""
    try:
        with dpg.font_registry():
            font_path = os.path.join(os.path.dirname(__file__), "assets", "fonts", "Roboto-Regular.ttf")
            if os.path.exists(font_path):
                dpg.add_font(font_path, 20, tag="default_font")
                dpg.bind_font("default_font")
            else:
                print(f"Warning: Font file not found at {font_path}. Using default font.")
    except Exception as e:
        print(f"Error setting up fonts: {e}")
        sys.exit(1)
    
def setup_menus():
    """Application menus setup"""
    with dpg.menu_bar():
        with dpg.menu(tag="file", label="File"):
            dpg.add_menu_item(label="New Project", callback=None)
            dpg.add_menu_item(label="Open Project", callback=None)
            dpg.add_menu_item(label="Save Project", callback=None)
            dpg.add_separator()
            dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

        with dpg.menu(tag="help", label="Help"):
            dpg.add_menu_item(tag="gh", label="GitHub repository", 
                             callback=lambda: __import__('webbrowser').open('https://github.com/MatheusMotizuki'))
            dpg.add_menu_item(label="About", callback=show_about)
        
        with dpg.menu(tag="development", label="Dev"):
            dpg.add_menu_item(tag="dev", label="DPG Docs", callback=lambda: dpg.show_documentation())
            dpg.add_menu_item(label="Debug Info", callback=lambda: dpg.show_debug())

def show_about():
    """Show about dialog."""
    with dpg.window(label="About PhotoGraph", no_close=True, show=True, tag="about_window", 
                   pos=[800, 435], width=400, height=140, no_resize=True, no_move=True, modal=True):
        dpg.add_text("PhotoGraph - Node-Based Image Editor")
        dpg.add_separator()
        dpg.add_text("TCC - UNIFESO 2025 - Matheus Motizuki")
        dpg.add_button(label="Close", tag="close_button", callback=lambda: dpg.delete_item("about_window"), pos=[170, 100])

    # Binding themes
    # dpg.bind_item_theme("about_window", ModalTheme.apply_theme())
    # dpg.bind_item_theme("close_button", ButtonTheme.apply_theme(border_col=(255, 60, 120, 255)))
#End helper functions

# Main portion
def main():
    """Main function to create a simple Dear PyGui window."""
    try:
        dpg.create_context()
        dpg.create_viewport(title='PhotoGraph Editor', width=1200, height=800, min_width=800, min_height=600)

        setup_fonts()

        editor = PhotoGraphEditor()

        # start socket client here (app lifecycle)
        client = SocketClient("http://localhost:8000")
        client.start()
        # attach to editor so callbacks can use it
        editor.socket_client = client

        with dpg.window(tag='photoGraphMain', menubar=True, no_title_bar=True, no_move=True, no_resize=True, no_close=True):
            setup_menus()
            # create UI and node editor inside window
            editor.initialize()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.maximize_viewport()
        dpg.set_primary_window("photoGraphMain", True)

        # Method 1: Try timer first, fallback to a dedicated daemon thread that polls periodically
        timer_added = False
        try:
            dpg.add_timer(callback=lambda: client.poll(editor), delay=0.05, repeat_count=-1)
            timer_added = True
            print("Timer added successfully for socket polling")
        except Exception as e:
            print(f"Timer not available: {e}. Falling back to a polling thread.")

        if not timer_added:

            # Event to allow a clean stop if desired; attached to client for optional external control
            stop_event = threading.Event()
            client._poll_stop_event = stop_event

            def _poll_loop():
                try:
                    while not stop_event.is_set():
                        client.poll(editor)
                        time.sleep(0.05)
                except Exception as e:
                    print(f"Polling thread error: {e}")

            poll_thread = threading.Thread(target=_poll_loop, name="SocketPollThread", daemon=True)
            poll_thread.start()
            print("Started polling thread for socket client")

        dpg.start_dearpygui()

    except Exception as e: # catch exceptions
        print(f"Error creating context or viewport: {e}")
    finally: # clean up
        try:
            client.stop()
        except Exception:
            pass
        dpg.destroy_context()

if __name__ == "__main__":
    main()