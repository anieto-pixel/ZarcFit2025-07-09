# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 11:50:00 2024

A widget for selecting a folder of input files and extracting data from them.

Renamed from 'InputFileWidget' to 'WidgetInputFile' to match updated class naming conventions.
"""

import os
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog, QHBoxLayout, QFileDialog, 
    QInputDialog, QFileDialog, QMenu, QAction, QMessageBox, QSizePolicy, QLineEdit, QLayout
)
from PyQt5.QtCore import pyqtSignal, Qt, QPoint
from PyQt5.QtGui import QFontMetrics
from .ConfigImporter import ConfigImporter
from .CustomListSliders import ListSlider


#this is a file type. SHould I define a proper class?
class NewZFile:
    """
    Handles writing rows of data to CSV files safely.
    """
    
    name='*.Z'
    
    caracteristics={
        'supported_file_extension': '.z', 
        'skip_rows': '128', 
        'freq_column': '0', 
        'z_real_column': '4', 
        'z_imag_column': '5'
    }
    step ='\t'
    
    
class OldZFile:
    """
    Handles writing rows of data to CSV files safely.
    """
    name='Old .Z'
    
    caracteristics={
        'supported_file_extension': '.z', 
        'skip_rows': '11', 
        'freq_column': '0', 
        'z_real_column': '4', 
        'z_imag_column': '5'
    }
    step =','
    
    
class GamryFile:
    """
    Handles writing rows of data to CSV files safely.
    """
    name='Gamry'
    
    caracteristics={
        'supported_file_extension': '.DTA', 
        'skip_rows': '98', 
        'freq_column': '2', 
        'z_real_column': '3', 
        'z_imag_column': '4'
    }
    step =r'\s+'
    

class FileTypesRegistry:
    
    def __init__(self):
        
        self._registry = {
        NewZFile.name: NewZFile,
        OldZFile.name: OldZFile,
        GamryFile.name: GamryFile,
    }

    def get_file_type(self, file_type_name):
        
        file_cls = self._registry.get(file_type_name)
        if file_cls is None:
            raise ValueError(f"Unknown file type: {file_type_name}")
        return file_cls()
    
    def get_default_file_type(self):
        default_key = list(self._registry.keys())[0]
        return self.get_file_type(default_key)
    
    def get_available_file_types(self):
        """
        Returns a list of all registered file type names.
        """
        return list(self._registry.keys())


class WidgetInputFile(QWidget):
    """
    A widget for browsing supported files in a directory, reading them in,
    and emitting arrays of frequency, real Z, and imaginary Z via a signal.
    """

    file_data_updated = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, current_file=None, file_type_name=None, font = 8):

        super().__init__()
        # Internal state
        self._folder_path = None
        self._files = []
        self._current_index = -1
        
        #file type related options
        self.registry = FileTypesRegistry() 
        self._file_type = None
        self.config_p = None
        
        # Build the UI layout
        self.font = font
        self._initialize_ui() 

        #initialize with parameters
        current_file, file_type_name= self._validate_given_parameters(current_file,file_type_name)
        self._initialize_file_type_parameters(file_type_name)
        self._setup_current_file(current_file)
        
        if self._file_type is not None:
            self.select_file_type_button.setText(self._file_type.name)
        else:
            self.select_file_type_button.setText("Select File Type")

    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def get_folder_path(self) -> str:
        """
        Returns the currently selected folder path.
        """
        return self._folder_path

    def get_current_file_path(self) -> str:
        """
        Returns the absolute path of the currently displayed file.
        """
        if 0 <= self._current_index < len(self._files):
            return os.path.join(self._folder_path, self._files[self._current_index])
        return None

    def get_current_file_name(self) -> str:
        """
        Returns the name of the currently displayed file.
        """
        if 0 <= self._current_index < len(self._files):
            return self._files[self._current_index]
        return None
  
    def get_file_type_name(self):
        return self._file_type.name
    
    def setup_current_file(self, current_file: str, current_file_type:str):
        """
        Sets up the current file by verifying its existence, loading the files
        in its directory, and updating the current index if found.
        """
        current_file, current_file_type= self._validate_given_parameters(current_file,current_file_type)
        if not isinstance(current_file, str):
               return
        self._initialize_file_type_parameters(current_file_type)
        self._setup_current_file(current_file)
            
    def force_emit_signal(self):

        if 0 <= self._current_index < len(self._files):
            current_file = self._files[self._current_index]
        else: return
        # Build full path and extract the file's content
        file_path = os.path.join(self._folder_path, current_file)
        self._extract_content(file_path)

    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------
    # UI Methods
    def _initialize_ui(self):
        self._initialize_widgets()
        self._configure_layout()
        self._apply_styles_and_sizing()
        self._connect_listeners()
    
    def _initialize_widgets(self):
        """Create all UI components."""
        # Buttons
        self.select_folder_button = QPushButton(" Select Input Folder ")
        self.select_file_type_button = QPushButton("Select File Type")
        self.previous_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.file_label = QLabel("No file selected")
        # Slider
        self._slider = ListSlider(font = self.font)
        self._slider.setMinimumWidth(400)
        # Imput box and label
        self._input_box = QLineEdit()
        self._length_slider_label = QLabel("/ Not init")
        # file label
        self.file_label.setAlignment(Qt.AlignCenter)
                  
    def _configure_layout(self):
        """Create and apply the main layout."""
        # Create the main horizontal layout
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)  # left, top, right, bottom
        layout.setSpacing(0)
    
        # Wrap folder and filetype buttons in their own container
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        button_layout.addWidget(self.select_folder_button)
        button_layout.addWidget(self.select_file_type_button)
    
        #  Create slider container with margin customization ---
        slider_container = self._create_slider_container()
        slider_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # Configure input box width ---
        font = self._input_box.font()
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance("9999")
        padding = 5
        self._input_box.setFixedWidth(text_width + padding)
        
        # Wrap input box and label container
        input_and_label_container = QWidget()
        input_and_label_layout = QHBoxLayout(input_and_label_container)
        input_and_label_layout.setContentsMargins(0, 0, 0, 0)
        input_and_label_layout.setSpacing(0)
        input_and_label_layout.addWidget(self._input_box)
        input_and_label_layout.addWidget(self._length_slider_label)
        
        # File‑navigation container (<, filename, >)
        nav_container = QWidget()
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        nav_layout.addWidget(self.previous_button)
        nav_layout.addWidget(self.file_label)
        nav_layout.addWidget(self.next_button)
        
        # Stack input_container & nav_container vertically
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        #bottom_layout.addWidget(input_and_label_container, alignment=Qt.AlignHCenter)
        #bottom_layout.addWidget(nav_container,   alignment=Qt.AlignHCenter)
        bottom_layout.addWidget(input_and_label_container)
        bottom_layout.addWidget(nav_container)
    
        #layout.addWidget(button_container, 0, Qt.AlignTop)
        layout.addWidget(button_container, 0, Qt.AlignVCenter)
        layout.addSpacing(5)  # or whatever inter‑block padding you like
        layout.addWidget(slider_container, 1, Qt.AlignTop)
        layout.addSpacing(5)
        #layout.addWidget(bottom_container, 0, Qt.AlignTop)
        layout.addWidget(bottom_container, 0, Qt.AlignVCenter)
    
        # Finally
        self.setLayout(layout)
    
    def _create_slider_container(self):
        """Build a QWidget that holds the slider, with no extra top margin."""
        slider_container = QWidget()
        slider_container.setContentsMargins(0, 0, 0, 0)
        slider_layout = QHBoxLayout(slider_container)
        slider_layout.setContentsMargins(4, 0, 4, 0) # left, top, right, bottom
        slider_layout.setSpacing(0)
        # slider_layout.addWidget(self._slider, alignment=Qt.AlignTop)
        slider_layout.addWidget(self._slider, 0, Qt.AlignTop)
        return slider_container

    def _apply_styles_and_sizing(self):
        """Apply font sizes, padding, and size policies."""
        
        file_label_font = self.file_label.font()
        file_label_font.setPointSizeF(self.font + 1)
        self.file_label.setFont(file_label_font)
        
        for btn in (
            self.select_folder_button,
            self.select_file_type_button,
            self.previous_button,
            self.next_button
        ):
            f = btn.font()
            f.setPointSize(self.font)
            btn.setFont(f)
    
            fm = QFontMetrics(f)
            btn.setFixedHeight(fm.height() + 9)
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
    
            # Set width only for previous/next buttons ("<" and ">")
            if btn in [self.previous_button, self.next_button]:
                symbol_width = fm.horizontalAdvance(btn.text())
                padding = 20  # Add a bit of extra space
                btn.setFixedWidth(symbol_width + padding)
            else:
                btn.adjustSize()
                
        label_font = self._length_slider_label.font()
        label_font.setPointSize(self.font)
        self._length_slider_label.setFont(label_font)
        
        # Apply font to _input_box
        input_font = self._input_box.font()
        input_font.setPointSize(self.font)
        self._input_box.setFont(input_font)   

    # Conectors
    def _connect_listeners(self):
        # Buttons and fodler related
        self.select_folder_button.clicked.connect(self._select_folder_handler)
        self.select_file_type_button.clicked.connect(self._select_file_type_handler)
        self.previous_button.clicked.connect(self._show_previous_file)
        self.next_button.clicked.connect(self._show_next_file)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        
        # Input box related
        self._slider.valueChanged.connect(self._slider_update_handler)
        self._slider.new_list_was_set.connect(lambda length: self._length_slider_label.setText(f"/{length}"))
        self._slider.valueChanged.connect(lambda v: self._input_box.setText(str(v + 1))) #mine
        self._input_box.editingFinished.connect(self._handle_input_box_update)
        
    # Configuration of file type
    def _initialize_file_type_parameters(self, file_type_name):
        
        if file_type_name is None:
            self._file_type =self.registry.get_default_file_type()
        else: 
            self._file_type = self.registry.get_file_type(file_type_name)

        self.config_p = self._file_type.caracteristics
        # Immediately validate and cast
        self._validate_type_parameters()
    
    def _validate_given_parameters(self, current_file, file_type_name):
                 
        if (not isinstance(current_file, str) or not isinstance(file_type_name, str)):
            return None, None
        # Find the last occurrence of '.' to locate the extension
        dot_index = current_file.rfind('.')
        
        # Extract the extension (including the dot)
        file_extension = current_file[dot_index:]
        expected_file_extension = self.registry.get_file_type(file_type_name).caracteristics['supported_file_extension']

        if not file_extension == expected_file_extension:
            return None, None
        
        return current_file, file_type_name
    
    def _validate_type_parameters(self):
        """
        Validates that all required configuration parameters are present.
        Raises a ValueError if any are missing.
        """
        needed_parameters = [
            'supported_file_extension',
            'skip_rows',
            'freq_column',
            'z_real_column',
            'z_imag_column'
        ]
        missing_params = [param for param in needed_parameters if param not in self.config_p]
        if missing_params:
            missing = ', '.join(missing_params)
            raise ValueError(f"WidgetInputFile._validate_parameters: Configuration must include parameters: {missing}")
        else:
            self.config_p=self._cast_config_parameters(self.config_p)
    
    def _cast_config_parameters(self, config_parameters):
        
        try:
            return {
                'supported_file_extension': config_parameters['supported_file_extension'].lower(),
                'skip_rows': int(config_parameters['skip_rows']),
                'freq_column': int(config_parameters['freq_column']),
                'z_real_column': int(config_parameters['z_real_column']),
                'z_imag_column': int(config_parameters['z_imag_column'])
            }
        except (KeyError, ValueError) as e:
            raise ValueError(f"WidgetInputFile._cast_config_parameters:Invalid configuration parameters: {e}")

    #Configuration oc current input
    def _setup_current_file(self, current_file:str):
        
        if current_file and os.path.isfile(current_file):
            folder_path = os.path.dirname(current_file)
            self._folder_path = folder_path
            self._load_files(skip_extract_default_file=True)#this is the one who needs to have the flag
            file_name = os.path.basename(current_file)#this would need to dissapear I guess?

            if file_name in self._files:
                self._current_index = self._files.index(file_name)
                self._update_file_display()
                self._update_navigation_buttons()
                
            else:#and you go to the first value
                self. _extract_default_file_from_folder()
                print(f"WidgetImputFile.setup_current_file: File '{file_name}' was not found in the folder '{self._folder_path}'.")
        
        elif current_file:
            folder_path = os.path.dirname(current_file)
            
            if os.path.isdir(folder_path):
                self._folder_path = folder_path
                self._load_files()
                print(f"WidgetImputFile.setup_current_file: File '{os.path.basename(current_file)}' was not found in the folder '{self._folder_path}'.")
            else:
                print(f"WidgetImputFile.setup_current_file: Path '{current_file}' was not found.")
        
    #  File/Folder Methods       
    def _select_folder_handler(self):
        """
        Opens a directory selection dialog, then triggers file loading
        if a valid path is chosen.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self._folder_path = folder
            self._load_files()

    def _load_files(self, skip_extract_default_file=False):
        """
        Scans the selected folder for files matching the supported extension,
        resets the current file index, and updates the UI.
        """

        if self._folder_path:
            supported_ext = self.config_p["supported_file_extension"]
            self._files = [
                f for f in os.listdir(self._folder_path)
                if f.lower().endswith(supported_ext)
            ]
            self._files = sorted(self._files)
            if not skip_extract_default_file:
                self._extract_default_file_from_folder()
            
            self._slider.set_list(self._files)

    def _extract_default_file_from_folder(self):
        
        if self._files:
            self._current_index = 0
            self._update_file_display()
            self._update_navigation_buttons()
        else:
            self.file_label.setText(
                f'WidgetImputFile._extract_default_file_from_folder: No {self.config_p["supported_file_extension"]} files found in the selected folder.'
            )
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)

    def _update_file_display(self):
        """
        Updates the UI to show the current file name, and calls
        _extract_content to read the file's data.
        """

        if not (0 <= self._current_index < len(self._files)):
            return
        
        current_file = self._files[self._current_index]
        self.file_label.setText(current_file)
            
        # Block extra signals so the slider doesn’t cause repeated calls
        self._slider.blockSignals(True)
        self._slider.setValue(self._current_index)
        self._slider.blockSignals(False)
        self._input_box.setText(str(self._current_index + 1))

        # Build full path and extract the file's content
        file_path = os.path.join(self._folder_path, current_file)
        self._extract_content(file_path)

    #Content extraction from selected file
    def _extract_content(self, file_path: str):
        """
        Reads the file at file_path using the specified configuration,
        and emits a signal with the extracted data.
        """

        this_step= self._file_type.step
        
        try:
            df = pd.read_csv(
                file_path,
                sep=this_step,
                skiprows=self.config_p["skip_rows"],
                header=None,
                
                encoding="cp1252"  
            )
            freq_col = self.config_p["freq_column"]
            z_real_col = self.config_p["z_real_column"]
            z_imag_col = self.config_p["z_imag_column"]
            max_col = max(freq_col, z_real_col, z_imag_col)
    
            if max_col >= len(df.columns):
                raise ValueError("WidgetInputFile._extract_content :File does not contain the required columns.")
    
            freq = df[freq_col].to_numpy()
            z_real = df[z_real_col].to_numpy()
            z_imag = df[z_imag_col].to_numpy()
    
            # Instead of empty arrays, send the arrays we just read:
            self.file_data_updated.emit(freq, z_real, z_imag)
    
        except Exception as e:
            self._handle_file_read_error(e, file_path)

    def _update_navigation_buttons(self):
        """
        Enables or disables navigation buttons based on the current index.
        """
        self.previous_button.setEnabled(self._current_index > 0)
        self.next_button.setEnabled(self._current_index < len(self._files) - 1)  
    
    #File Type Methods
    def _select_file_type_handler(self):

        file_types = self.registry.get_available_file_types()
        
        # Create a popup menu
        menu = QMenu(self)
        
        # Add one QAction per file type
        for ft in file_types:
            action = QAction(ft, self)
            
            # Connect the action's "triggered" signal
            # Use a lambda to capture ft in the callback
            action.triggered.connect(lambda checked, ft_name=ft: self._on_file_type_selected(ft_name))
            menu.addAction(action)
        
        # Position the menu so it drops down from the button
        # We'll map to global coords and just offset below the button
        button_pos = self.select_file_type_button.mapToGlobal(QPoint(0, self.select_file_type_button.height()))
        menu.exec_(button_pos)

    def _on_file_type_selected(self, selected_type):
        """
        Internal slot called when a file type is chosen from the popup menu.
        """
        self._file_type = self.registry.get_file_type(selected_type)
        self.config_p = self._file_type.caracteristics
        self._validate_type_parameters()
        
        # If a folder is already selected, reload the files so the new extension
        if self._folder_path:
            self._load_files()

        self.select_file_type_button.setText(self._file_type.name)
                 
    # Private Navigation Methods  
    def _show_previous_file(self):
        """
        Moves to the previous file in the list, if possible.
        """
        if self._current_index > 0:
            self._current_index -= 1
            #slider already calls _update_file_display()
            self._slider.down()
            #self._update_file_display()
            self._update_navigation_buttons()

    def _show_next_file(self):
        """
        Moves to the next file in the list, if possible.
        """
        if self._current_index < len(self._files) - 1:
            self._current_index += 1
            #slider already calls _update_file_display()
            self._slider.up()
            #self._update_file_display()
            self._update_navigation_buttons()
               
    def _slider_update_handler(self, index: int):
        self._current_index=index
        self._update_file_display()
        self._update_navigation_buttons()

    # Content methods
    def _handle_file_read_error(self, exc: Exception, file_path: str):
        """
        Displays a warning, updates the file label, and emits empty arrays
        to signal that reading has failed gracefully.
        """
        error_msg = f"WidgetInputFile._extract_content. Could not read file '{file_path}': {exc}"
        print(error_msg)

        # Optionally show a QMessageBox warning to the user
        QMessageBox.warning(self, "File Read Error. Possibly wrong format", error_msg)

        # Update label text
        self.file_label.setText("Error reading file. Possibly wrong filetype.")

        # Emit dummy data so the program doesn't crash downstream.
        self.file_data_updated.emit(np.array([]), np.array([]), np.array([]))

    # Input box handlers
    def _handle_input_box_update(self):
        
        txt = self._input_box.text()
        if txt.isdigit():
            self._slider.set_list_value_index(int(txt) - 1)
        else:
            print("Invalid input")

        self._input_box.editingFinished.connect(self._handle_input_box_update)
         
        
# -----------------------------------------------------------------------
#  TEST
# -----------------------------------------------------------------------
import sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton
)
from PyQt5.QtCore import Qt


class TestWindow(QWidget):
    def __init__(self, config_parameters):
        
        super().__init__()
        self.setWindowTitle("Test for WidgetInputFile")

        # 1) Create the WidgetInputFile instance
        self.widget_input_file = WidgetInputFile(config_parameters)

        # 2) Connect its signal to see incoming data in console
        self.widget_input_file.file_data_updated.connect(self.handle_file_data_updated)

        # 3) Build a layout: the widget + some test buttons
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.widget_input_file)

        # Buttons to test the public methods
        button_layout = QHBoxLayout()

        btn_folder_path = QPushButton("Get Folder Path")
        btn_folder_path.clicked.connect(self.show_folder_path)
        button_layout.addWidget(btn_folder_path)

        btn_current_file_path = QPushButton("Get Current File Path")
        btn_current_file_path.clicked.connect(self.show_current_file_path)
        button_layout.addWidget(btn_current_file_path)

        btn_current_file_name = QPushButton("Get Current File Name")
        btn_current_file_name.clicked.connect(self.show_current_file_name)
        button_layout.addWidget(btn_current_file_name)

        # Optional: a button to demonstrate setup_current_file
        btn_setup_file = QPushButton("Setup Current File")
        btn_setup_file.clicked.connect(self.test_setup_current_file)
        button_layout.addWidget(btn_setup_file)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    # -----------------------------------------------------------------------
    #  Button Handlers
    # -----------------------------------------------------------------------
    def show_folder_path(self):
        print("Folder path:", self.widget_input_file.get_folder_path())

    def show_current_file_path(self):
        print("Current file path:", self.widget_input_file.get_current_file_path())

    def show_current_file_name(self):
        print("Current file name:", self.widget_input_file.get_current_file_name())

    def test_setup_current_file(self):
        """
        Example usage:
        Suppose we have some file like 'C:/data/test.z'.
        If it exists, WidgetInputFile will load that folder and set that file.
        """
        dummy_file = "C:/path/to/your/test.z"
        self.widget_input_file.setup_current_file(dummy_file)

    # -----------------------------------------------------------------------
    #  Slot for file_data_updated
    # -----------------------------------------------------------------------
    def handle_file_data_updated(self, freq, z_real, z_imag):
        pass
#        print("Received file_data_updated signal:")
#        print("  freq:", freq)
#        print("  z_real:", z_real)
#        print("  z_imag:", z_imag)


if __name__ == "__main__":

    # Sample config dict. Normally you might read these from a ConfigImporter or JSON
    config = {
        'supported_file_extension': '.z',
        'skip_rows': 1,
        'freq_column': 0,
        'z_real_column': 1,
        'z_imag_column': 2
    }

    app = QApplication(sys.argv)

    test_window = TestWindow(config)
    test_window.resize(800, 100)
    test_window.show()

    sys.exit(app.exec_())