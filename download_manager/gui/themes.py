import customtkinter as ctk

def apply_theme(root, theme_name="dark-blue"):
    """
    Applies global CustomTkinter theme settings.
    """
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme(theme_name)
    return None
