##### external dependencies #####
import customtkinter as ctk
import base64
import io
from PIL import Image, ImageTk, ImageFile
from threading import Thread
from time import sleep

##### importing same project files #####
import sys

if sys.platform == "linux":
    file_sep = '/'
else:
    file_sep = '\\'
cur_parent_dirs = sys.path[0].split(file_sep)
parent_dir_index = cur_parent_dirs.index("P2")
sys.path.append(file_sep.join(cur_parent_dirs[0:parent_dir_index+1])) # allows imports from P2 folder

from implementation.network_monitorer import NetworkMonitorer

##### for testing purposes #####
import pytest
import unittest
from unittest.mock import patch, Mock
from http import HTTPStatus


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, width = 200, height = 200, corner_radius = None, border_width = None, bg_color = "transparent", fg_color = None, border_color = None, background_corner_colors = None, overwrite_preferred_drawing_method = None, **kwargs):
        super().__init__(master, width, height, corner_radius, border_width, bg_color, fg_color, border_color, background_corner_colors, overwrite_preferred_drawing_method, **kwargs)
