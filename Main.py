"""
Modified on Thu Apr 24 08:59:50 2025

@author: Alicia Nieto

Version 5.2.5
"""

import os
import sys
from datetime import datetime

import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import (QKeySequence, QMouseEvent, QFont, QFontMetrics, QPalette, QColor)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QShortcut, QSizePolicy, QSplitter,
    QWidget, QHBoxLayout, QVBoxLayout,  QPushButton, QLabel
    )

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "AuxiliaryClasses")))

from AuxiliaryClasses.ConfigImporter import ConfigImporter
from AuxiliaryClasses.CustomListSliders import ListSliderRange
from AuxiliaryClasses.Calculator import Calculator
from AuxiliaryClasses.WidgetButtonsRow import WidgetButtonsRow
from AuxiliaryClasses.WidgetGraphs import WidgetGraphs
from AuxiliaryClasses.WidgetInputFile import WidgetInputFile
from AuxiliaryClasses.WidgetOutputFile import WidgetOutputFile
from AuxiliaryClasses.WidgetSliders import WidgetSliders
from AuxiliaryClasses.WidgetTextBar import WidgetTextBar


class MainWidget(QWidget):
    def __init__(self, config_file: str):
        super().__init__()

        # Data attributes
        self.file_data = {"freq": None, "Z_real": None, "Z_imag": None}
        self.v_sliders = None

        # Initialization
        self._initialize_core_widgets()
        self._optimize_sliders_signaling()
        self.v_sliders = self.widget_sliders.get_all_values()

        # Layout UI
        self._build_ui()

        # Connect signals, hotkeys, etc.
        self._connect_listeners()
        self._initialize_hotkeys_and_buttons()
        self._session_initialization()

    #-----------------------UI and Widgets -----------------------------
    def _build_ui(self):
        """Assembles the main layout from smaller UI components."""
        top_bar = self._build_top_bar()
        middle_area = self._build_middle_area()
        bottom_area = self._build_bottom_area()
        
        # Create a vertical splitter to separate middle and bottom areas.
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(middle_area)
        self.splitter.addWidget(bottom_area)
        
        # Set initial sizes (these will be updated dynamically on resize).
 #       self.splitter.setSizes([1, 1])
        self.splitter.setStretchFactor(0, 1)  # Middle area expands
        self.splitter.setStretchFactor(1, 0)  # Bottom area remains fixed initially
        self.splitter.setHandleWidth(10)
             
        main_layout = QVBoxLayout()
        main_layout.addWidget(top_bar)
        main_layout.addWidget(self.splitter)
        main_layout.setContentsMargins(2, 2, 6, 2) #left, top, right, bottom
        #main_layout.setSpacing(0)
        self.setLayout(main_layout)

    def _build_top_bar(self) -> QWidget:
        """Builds the top bar with file input/output widgets."""
        layout = QHBoxLayout()
   
        self.widget_input_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.widget_output_file.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
        layout.addWidget(self.widget_input_file, 1)
        layout.addWidget(self.widget_output_file, 0)
        layout.addWidget(self.toggle_model_button_wrapping)
        layout.setContentsMargins(0, 0, 0, 0)
        
        container = QWidget()
        container.setLayout(layout)     
        
        return container

    def _build_middle_area(self) -> QWidget:
        """Builds the middle area with a frequency slider and graphs."""
        freq_layout = QVBoxLayout()
        freq_layout.addWidget(self.freq_slider_wrapping)
        freq_layout.setContentsMargins(0, 0, 0, 0)
        freq_layout.setSpacing(0)
        freq_widget = QWidget()
        freq_widget.setLayout(freq_layout)
        freq_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        freq_widget.setMaximumWidth(freq_widget.sizeHint().width())

        middle_layout = QHBoxLayout()
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        middle_layout.addWidget(freq_widget, stretch=0)
        middle_layout.addWidget(self.widget_graphs, stretch=1)
        middle_widget = QWidget()
        middle_widget.setLayout(middle_layout)
        middle_widget.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        return middle_widget

    def _build_bottom_area(self) -> QWidget:
        bottom_half_layout = QHBoxLayout()
        bottom_half_layout.setContentsMargins(0,0,0,0)
        bottom_half_layout.setSpacing(0)
    
        # Sliders can expand but will also *shrink* first
        self.widget_sliders.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )
        # Buttons get to stay at their hint/minimum
        self.widget_buttons.setSizePolicy(
            QSizePolicy.Minimum,
            QSizePolicy.Preferred
        )
    
        # The stretch factors (1 vs 0) make sure:
        #  • extra space → sliders  
        #  • too little space → sliders give up before buttons
        bottom_half_layout.addWidget(self.widget_sliders, 1)
        bottom_half_layout.addWidget(self.widget_buttons, 0)
    
        bottom_half_widget = QWidget()
        bottom_half_widget.setLayout(bottom_half_layout)
    
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0,0,0,0)
        bottom_layout.addWidget(bottom_half_widget)
        bottom_layout.addWidget(self.widget_at_bottom)
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_layout)
        return bottom_widget

    def _initialize_core_widgets(self):
        """Initializes configuration, core widgets, and models."""
        self.config = ConfigImporter(config_file)

        self.widget_input_file = WidgetInputFile(self.config.input_file, 
                                                 self.config.input_file_type, 
                                                 font = self.config.small_font
                                                 )    
        self.widget_output_file = WidgetOutputFile(self.config.variables_to_print, 
                                                   self.config.output_file,
                                                   font = self.config.small_font
                                                   )
        self.toggle_model_button_wrapping = self._create_button_toggle_model()
        
        self.widget_graphs = WidgetGraphs()
        self.freq_slider_wrapping = self._create_slider_and_wrapping()
        
        self.widget_sliders = WidgetSliders(
            self.config.slider_configurations, self.config.slider_default_values,
            font = self.config.general_font, small_font = self.config.small_font
            )
        self.widget_buttons = WidgetButtonsRow(font = self.config.small_font)
        self.widget_at_bottom = WidgetTextBar(self.config.secondary_variables_to_display,
                                              font = self.config.general_font
                                              )
        self.calculator = Calculator()
        self.calculator.set_bounds(self.config.slider_configurations)
    
    # minor widget 1
    def _create_button_toggle_model(self):
        """Creates the Circuit Model toggle, sized and wrapped like the other buttons."""
        # Shared font
        font = QFont("Arial", self.config.small_font)
        fm = QFontMetrics(font)
    
        # Label
        button_label = QLabel("Circuit Model")
        button_label.setFont(font)
        button_label.setStyleSheet("color: white;")
        button_label.setAlignment(Qt.AlignCenter)
        button_label.setContentsMargins(0, 0, 0, 0)
        button_label.setMargin(0)
        button_label.adjustSize()                         # ← make its sizeHint tight
    
        # Toggle button
        button = QPushButton()
        button.setFont(font)
        button.off_label = "Parallel"
        button.on_label  = "Serial"
        button.setCheckable(True)
        button.setText(button.off_label)
    
        button.setFixedHeight(fm.height() + 9)
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        button.adjustSize()
    
        button.setStyleSheet(f"""
            QPushButton {{
                color: white;
                background-color: #0078D7;
            }}
            QPushButton:checked {{
                background-color: #005999;
            }}
        """)
        button.toggled.connect(
            lambda checked: button.setText(button.on_label if checked else button.off_label)
        )
        self.toggle_model_button = button
    
        # Container with zero margins/spacing so label+button hug tightly
        container = QWidget()
        container.setAutoFillBackground(True)
        
        pal = container.palette()
        pal.setColor(QPalette.Window, QColor("#0078D7"))
        container.setPalette(pal)
        #container.setStyleSheet("background-color: #0078D7;")
        
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(6, 0, 6, 0)  # ← NO top/bottom padding
        vbox.setSpacing(0)                   # ← NO gap between label & button
#        vbox.setAlignment(Qt.AlignTop)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.addWidget(button_label, alignment=Qt.AlignHCenter)
        vbox.addWidget(button,      alignment=Qt.AlignHCenter)
    
        container.setLayout(vbox)
    
        return container
    
    def _create_slider_and_wrapping(self):
        
        self.freq_slider = ListSliderRange(font = self.config.small_font)
        self.freq_slider.setInvertedAppearance(True)
    
        # 2) 3 labels: a unit title, low‐value, high‐value
        title     = QLabel("Hz")
        self.low_freq_label   = QLabel(f"{self.freq_slider.high_value():.2e}")
        self.high_freq_label  = QLabel(f"{self.freq_slider.low_value():.2e}")
    
        # 3) fonts
        title.setFont(    QFont("Arial", self.config.small_font))
        for lbl in (self.low_freq_label, self.high_freq_label):
            lbl.setFont( QFont("Arial", self.config.small_font))
            # white background + a little padding
            lbl.setStyleSheet("background: white; padding: 2px;")
    
        # 4) center everything
        for lbl in (title, self.low_freq_label, self.high_freq_label):
            lbl.setAlignment(Qt.AlignCenter)
    
        # 5) build layout: title, low, slider, high
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(title)
        layout.addWidget(self.high_freq_label)
        layout.addWidget(self.freq_slider)
        layout.addWidget(self.low_freq_label)
    
        container = QWidget()
        container.setLayout(layout)
        return container

    # ---------------- SIGNAL CONNECTIONS ----------------
    def _connect_listeners(self):
        """Connects signals from other widgets to their matching handle methods."""
        
        # File-related signals
        self.widget_input_file.file_data_updated.connect(self._handle_update_file_data)
        self.widget_output_file.output_file_selected.connect(self.config.set_output_file)

        # Slider signals
        self.widget_sliders.slider_value_updated.connect(self._handle_slider_update)
        self.widget_sliders.all_sliders_values_reseted.connect(self._reset_v_sliders)
        self.widget_sliders.slider_was_disabled.connect(self.calculator.set_disabled_variables)
        self.freq_slider.sliderMoved.connect(self._handle_frequency_update)
        # Calculator signals
        self.calculator.model_manual_result.connect(self.widget_graphs.update_manual_plot)
        self.calculator.fit_builder.model_manual_values.connect(self.widget_sliders.set_all_variables)

    def _initialize_hotkeys_and_buttons(self):
        """Initializes keyboard shortcuts and connects button actions."""
        
        # All actions from buttons in WidgetButon
        shortcut_f1 = QShortcut(QKeySequence(Qt.Key_F1), self)
        shortcut_f1.activated.connect(self.widget_buttons.f1_button.click)
        self.widget_buttons.f1_button.clicked.connect(
            lambda: self.calculator.fit_model_cole(self.v_sliders)
        )

        shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self)
        shortcut_f2.activated.connect(self.widget_buttons.f2_button.click)
        self.widget_buttons.f2_button.clicked.connect(
            lambda: self.calculator.fit_model_bode(self.v_sliders)
        )

        shortcut_f3 = QShortcut(QKeySequence(Qt.Key_F3), self)
        shortcut_f3.activated.connect(self.widget_buttons.f3_button.click)
        self.widget_buttons.f3_button.clicked.connect(self._handle_set_allfreqs)

        shortcut_f4 = QShortcut(QKeySequence(Qt.Key_F4), self)
        shortcut_f4.activated.connect(self.widget_buttons.f4_button.click)
        self.widget_buttons.f4_button.clicked.connect(self._print_model_parameters)

        shortcut_f5 = QShortcut(QKeySequence(Qt.Key_F5), self)
        shortcut_f5.activated.connect(self.widget_buttons.f5_button.click)
        self.widget_buttons.f5_button.clicked.connect(self.widget_input_file._show_previous_file)

        shortcut_f6 = QShortcut(QKeySequence(Qt.Key_F6), self)
        shortcut_f6.activated.connect(self.widget_buttons.f6_button.click)
        self.widget_buttons.f6_button.clicked.connect(self.widget_input_file._show_next_file)

        shortcut_f7 = QShortcut(QKeySequence(Qt.Key_F7), self)
        shortcut_f7.activated.connect(self.widget_buttons.f7_button.click)
        self.widget_buttons.f7_button.clicked.connect(self._handle_recover_file_values)

        shortcut_f8 = QShortcut(QKeySequence(Qt.Key_F8), self)
        shortcut_f8.activated.connect(self.widget_buttons.f8_button.click)
        self.widget_buttons.f8_button.clicked.connect(self._handle_set_default)

        shortcut_f9 = QShortcut(QKeySequence(Qt.Key_F9), self)
        shortcut_f9.activated.connect(self.widget_buttons.f9_button.click)
        self.widget_buttons.f9_button.toggled.connect(self._handle_rinf_negative)

        shortcut_f10 = QShortcut(QKeySequence(Qt.Key_F10), self)
        shortcut_f10.activated.connect(self.widget_buttons.f10_button.click)
        self.widget_buttons.f10_button.clicked.connect(self._handle_toggle_pei)

        shortcut_f11 = QShortcut(QKeySequence(Qt.Key_F11), self)
        shortcut_f11.activated.connect(self.widget_buttons.f11_button.click)
        self.widget_buttons.f11_button.clicked.connect(self.calculator.set_gaussian_prior)
        
        shortcut_f12 = QShortcut(QKeySequence(Qt.Key_F12), self)
        shortcut_f12.activated.connect(self.widget_buttons.f12_button.click)
        self.widget_buttons.f12_button.clicked.connect(self.widget_output_file.print_variables_list)

        shortcut_page_down = QShortcut(QKeySequence(Qt.Key_PageDown), self)
        shortcut_page_down.activated.connect(self.widget_buttons.fdown_button.click)
        self.widget_buttons.fdown_button.clicked.connect(self.freq_slider.up_min)

        shortcut_page_up = QShortcut(QKeySequence(Qt.Key_PageUp), self)
        shortcut_page_up.activated.connect(self.widget_buttons.fup_button.click)
        self.widget_buttons.fup_button.clicked.connect(self.freq_slider.down_max)

        shortcut_ctrl_z = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Z), self)
        shortcut_ctrl_z.activated.connect(self.calculator.fit_builder.recover_previous_fit)
        self.widget_buttons.ctrlz_button.clicked.connect(self.calculator.fit_builder.recover_previous_fit)

        # The button for the models
        self.toggle_model_button.toggled.connect(self.calculator.switch_circuit_model)

    # ------------------- HANDLERS -------------------
    def _handle_update_file_data(self, freq: np.ndarray, Z_real: np.ndarray, Z_imag: np.ndarray):
        """
        Updates graphs, model, frequency slider, and configuration with new file data.
        """
        if (freq is None or Z_real is None or Z_imag is None or
            len(freq) == 0 or len(Z_real) == 0 or len(Z_imag) == 0):
            
            self.widget_graphs.reset_default_values()
            print("MainWidget: Received empty or invalid data. Skipping update.")
            return
        
        self.file_data.update(freq=freq, Z_real=Z_real, Z_imag=Z_imag)
        self.widget_graphs.update_front_graphs(freq, Z_real, Z_imag)
            
        freqs_uniform, t, volt = self.calculator.transform_to_time_domain()
        self.widget_graphs.update_timedomain_graph(freqs_uniform, t, volt)
            
        self.calculator.initialize_expdata(self.file_data)
        self.freq_slider.set_list(freq)
        self._update_sliders_data()
            
        self.config.set_input_file_type(self.widget_input_file.get_file_type_name())
        self.config.set_input_file(self.widget_input_file.get_current_file_path())
            
        #self.widget_at_bottom.clear_text_box()

    def _handle_recover_file_values(self):
        """Recovers file values from output. Updates sliders position."""
        
        head = self.widget_input_file.get_current_file_name()
        dictionary = self.widget_output_file.find_row_in_file(head)
        
        if dictionary is None:
            print(f"Main._handle_recover_file_values: Output file has no row with head: {head}")
            self._handle_set_default()
            return 

        for key in set(self.config.slider_configurations.keys()).intersection(dictionary.keys()):
            self.v_sliders[key] = float(dictionary[key])
            
        if 'Rinf' in self.v_sliders:
            if self.v_sliders['Rinf'] < 0:
                self.v_sliders['Rinf']=abs(self.v_sliders['Rinf'])
                self.widget_buttons.f9_button.setChecked(True)  # Toggle ON
            else:
                self.widget_buttons.f9_button.setChecked(False)  # Toggle OFF
            
        if 'Pei' in self.v_sliders:
            self.v_sliders['Pei'] = (self.v_sliders['Pei']+1)%4. - 1.
            
        self.widget_sliders.set_all_variables(self.v_sliders)

    def _handle_slider_update(self, key, value):
        """
        Handles incoming slider updates by storing them and starting the debounce timer.
        """
        arbitrary_time_delay=5 #reduce for more responsive sliders, icnrease for more optimization
        
        self.pending_updates[key] = value
        self.update_timer.start(arbitrary_time_delay)  

    def _update_sliders_data(self):
        """Processes all pending slider updates. Updates affected widgets and refreshes the UI."""
        
        for key, value in self.pending_updates.items():
            self.v_sliders[key] = value
        self.pending_updates.clear()

        self.calculator.run_model_manual(self.v_sliders)
        v_second = self.calculator.get_latest_secondaries()
        self.widget_at_bottom._update_text(v_second)

    def _reset_v_sliders(self, dictionary):
        """
        Resets slider values to the values in the incoming dictionary.
        """
        if set(dictionary.keys()) != set(self.v_sliders.keys()):
            raise ValueError(
                "Main._reset_v_sliders:Incoming dictionary keys do not match the slider keys in WidgetSliders."
            )
        self.v_sliders = dictionary
        self._update_sliders_data()

    def _handle_frequency_update(self, bottom_i, top_i, f_max, f_min):
        """
        Handles frequency filtering based on freq_slider positions.
        """
        
        freq_filtered = self.file_data['freq'][bottom_i: top_i + 1]
        z_real_filtered = self.file_data["Z_real"][bottom_i: top_i + 1]
        z_imag_filtered = self.file_data["Z_imag"][bottom_i: top_i + 1]

        new_data = {
            "freq": freq_filtered,
            "Z_real": z_real_filtered,
            "Z_imag": z_imag_filtered,
        }
        
        self.low_freq_label .setText(f"{self.freq_slider.high_value():.2e}")
        self.high_freq_label.setText(f"{self.freq_slider.low_value():.2e}")

        self.calculator.initialize_expdata(new_data)
        self.widget_graphs.apply_filter_frequency_range(f_min, f_max)

    def _handle_set_allfreqs(self):
        """
        Resets the frequency slider to default,
        reinitializes the model with current file data,
        and updates front graphs.
        """
        self.freq_slider.default()
        self.calculator.initialize_expdata(self.file_data)
        self.widget_graphs.update_front_graphs(
            self.file_data['freq'],
            self.file_data['Z_real'],
            self.file_data['Z_imag']
        )
        # TODO: Update time-domain graph if needed.
        self._update_sliders_data()

    def _handle_set_default(self):
        """
        Resets sliders to their default values and refreshes frequency settings.
        """
        self.widget_sliders.set_to_default_values() 
        self.widget_sliders.set_to_default_disabled() 
        #self._handle_set_allfreqs()

    def _handle_rinf_negative(self, state):
        """Handles toggling for Rinf being negative."""
        self.calculator.set_rinf_negative(state)
        self.widget_sliders.get_slider('Rinf').toggle_orange_effect(state)
        self.calculator.run_model_manual(self.v_sliders)

    def _handle_toggle_pei(self, state):
        """Handles toggling for Pei value."""
        
        if state:
            self.widget_sliders.get_slider('Pei').set_value_exact(2.0)
        else:
            self.widget_sliders.get_slider('Pei').set_value_exact(0.0)

    # ------------------- OTHER METHODS ------------------- 
    def _session_initialization(self):

        self.widget_input_file.force_emit_signal()
        #Set default disabled sliders
        self.widget_sliders.set_default_disabled(self.config.slider_default_disabled)
        #self._update_sliders_data() #Needed anymore?
         
    def _optimize_sliders_signaling(self):
        """Optimizes sliders signaling by initializing a debounce timer."""
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_sliders_data)
        self.pending_updates = {}
        self.value_labels = {}

    def _print_model_parameters(self):
        """
        Called when Print is requested.
        Merges slider values, timestamp, and file information before writing output.
        """
        date = {'date/time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        file = {'file': self.widget_input_file.get_current_file_name()}
        v_copy = self.v_sliders.copy()
        
        # If button-9 is toggled, modify values accordingly (e.g., change sign of 'Rinf')
        if self.widget_buttons.f9_button.isChecked():
            if 'Rinf' in v_copy:
                v_copy['Rinf'] *= -1  # Negate Rinf if needed

        main_dictionary = v_copy | date | file
        model_dictionary = self.calculator.get_model_parameters()
        graphs_dictionary = self.widget_graphs.get_graphs_parameters()
        bottom_dictionary= self.widget_at_bottom.get_comment()

        self.widget_output_file.write_to_file(
            main_dictionary | model_dictionary | graphs_dictionary | bottom_dictionary
        )


if __name__ == "__main__":
    
#---Allowing proper display in different resolutions-----------------------
    import platform
    import ctypes
    if platform.system()=='Windows' and int(platform.release()) >= 8:   
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
        
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            base_path = sys._MEIPASS  # PyInstaller sets this when running as a bundled app
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
        
        
#---Allowing proper display in different resolutions-----------------------   
    
    app = QApplication(sys.argv)
#    app.setAttribute(Qt.AA_Use96Dpi) #VER ESTO
    
    config_file = resource_path("config.ini")

    # MainWindow container
    window = QMainWindow()
    main_widget = MainWidget(config_file)
    window.setCentralWidget(main_widget)
    window.setWindowTitle("ZarcFit 5.6")
    
    window.setGeometry(0, 0, 1500, 900)  # Set the initial size and position (x=0, y=0, width=800, height=600)

    window.show()

    sys.exit(app.exec_())
