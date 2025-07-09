"""
Created on Mon Dec 30 08:27:11 2024

Graphs for impedance data visualization:
  - ParentGraph (base class)
  - PhaseGraph
  - BodeGraph
  - ColeColeGraph
  - TimeGraph
  - WidgetGraphs (displays multiple graphs)
"""
import sys
import copy
import numpy as np
import pyqtgraph as pg
from pyqtgraph import FillBetweenItem, InfiniteLine, mkPen

from PyQt5.QtWidgets import (
    QApplication, QPushButton, QWidget, QTabWidget, QHBoxLayout, QTabWidget,
    QVBoxLayout, QFrame, QSizePolicy, QSplitter, QToolTip, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Example import for the type-hinted method below:
# from ModelManual import CalculationResult
# In your real code, ensure CalculationResult is defined or properly imported.
class CalculationResult:
    """Dummy placeholder so this snippet runs independently."""
    def __init__(self):
        self.main_freq = np.array([1, 10, 100])
        self.main_z_real = np.array([100, 80, 60])
        self.main_z_imag = np.array([-50, -40, -30])
            
        self.rock_z_real = np.ndarray([100, 80, 60])
        self.rock_z_imag = np.ndarray([-48, -32, -28])

        self.special_freq = np.array([10, 50, 90])
        self.special_z_real = np.array([70, 65, 55])
        self.special_z_imag = np.array([-40, -35, -28])

        self.timedomain_freq = np.array([0.01, 4.5, 1.1])
        self.timedomain_time = np.linspace(0, 1, 100)
        self.timedomain_volt_down = np.sin(2 * np.pi * 10 * self.timedomain_time)
        self.timedomain_volt_up = np.cos(2 * np.pi * 10 * self.timedomain_time)


class ParentGraph(pg.PlotWidget):
    """
    A base PlotWidget that manages 'base' data, 'manual' data, and special markers.
    Subclasses may override _prepare_xy(...) and certain UI aspects.
    """
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        
        self._init_data()
        self._init_ui()
        self._init_signals()
        self._special_items = []
        self.fill_region = None
        self._dynamic_plot = None
        self._static_plot = None
        self._autoscale_padding = 0.1

        # Create plot items once, do not recreate them on every refresh
        self._create_plot_items()
        # Populate them once
        self._refresh_graph()
        # Optionally enable auto-scale
        self.auto_scale_button.setChecked(True)

        # Display of coordenates as the mouse hoovers over the plot
        self._coord_label = pg.TextItem("", anchor=(0, 1), color="w")
        self.plotItem.vb.addItem(self._coord_label)
        self.scene().sigMouseMoved.connect(self._mouse_moved)

    # -----------------------------------------------------------------------
    #  Public Methods
    # -----------------------------------------------------------------------
    def reset_default_values(self):
        self._init_data()
        self._refresh_graph()
        
    def filter_frequency_range(self, f_min, f_max):
        """
        Filters base and manual data to only show points in [f_min, f_max].
        """
        base_mask = (
            (self._original_base_data['freq'] >= f_min) &
            (self._original_base_data['freq'] <= f_max)
        )
        self._base_data = {
            'freq': self._original_base_data['freq'][base_mask],
            'Z_real': self._original_base_data['Z_real'][base_mask],
            'Z_imag': self._original_base_data['Z_imag'][base_mask],
        }

        manual_mask = (
            (self._original_manual_data['freq'] >= f_min) &
            (self._original_manual_data['freq'] <= f_max)
        )
        self._manual_data = {
            'freq': self._original_manual_data['freq'][manual_mask],
            'Z_real': self._original_manual_data['Z_real'][manual_mask],
            'Z_imag': self._original_manual_data['Z_imag'][manual_mask],
        }

        self._refresh_graph()

    def update_parameters_base(self, freq, Z_real, Z_imag):
        """
        Updates the 'base' data and refreshes. The original data is also updated
        so filtering is always relative to the new full dataset.
        """
        # Temporarily disable auto-scale so it won't interfere
        self.auto_scale_button.setChecked(False)

        self._base_data = {'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag}
        self._original_base_data = copy.deepcopy(self._base_data)

        # Refresh once
        self._refresh_graph()
        # Re-enable auto-scale if desired
        self.auto_scale_button.setChecked(True)

    def update_parameters_manual(self, freq, Z_real, Z_imag):
        """
        Updates the 'manual' (dynamic) data. Only that plot is changed.
        """
        self._manual_data = {'freq': freq, 'Z_real': Z_real, 'Z_imag': Z_imag}
        self._original_manual_data = copy.deepcopy(self._manual_data)
        self._refresh_plot(self._manual_data, self._dynamic_plot)

    def update_special_frequencies(self, freq_array, z_real_array, z_imag_array):
        """
        Adds or updates special marker points on the graph.
        """
        # 1) Clear out the old items
        for item in self._special_items:
            self.removeItem(item)
        self._special_items = []

        symbols = ['x', 'd', 's']
        colors  = ['r', 'g', 'b']

        # 2) For each frequency triplet, compute its styling then plot it
        for i, (freq, zr, zi) in enumerate(zip(freq_array, z_real_array, z_imag_array)):
            group_index  = i // 3
            symbol       = symbols[ group_index % len(symbols) ]
            color        = colors[ i % len(colors) ]
            filled       = (group_index % 2 == 0)

            plot_item = self._draw_special_marker(
                freq, zr, zi,
                symbol=symbol,
                color=color,
                filled=filled
            )
            self._special_items.append(plot_item)
            
    def _draw_special_marker(self, freq, zr, zi, symbol, color, filled):
        """
        Handles the coordinate transform + single‐point plotting.
        By extracting the scalar out of the 1‐element arrays, we
        avoid any surprises in how PlotDataItem interprets the x,y shapes.
        """
        # transform into plot coordinates
        x_arr, y_arr = self._prepare_xy(
            np.array([freq]),
            np.array([zr]),
            np.array([zi])
        )
        # pull out the scalar floats
        x = float(x_arr[0])
        y = float(y_arr[0])

        pen   = pg.mkPen(color, width=2)
        brush = color if filled else None

        return self.plot(
            [x], [y],              # pass single‐element lists
            pen=None,
            symbol=symbol,
            symbolSize=12,
            symbolPen=pen,
            symbolBrush=brush
        )
    # -----------------------------------------------------------------------
    #  Private Methods
    # -----------------------------------------------------------------------
    def _init_data(self):
        """Initialize default datasets and originals for filtering."""
        self._base_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([100, 80, 60, 40, 20]),
            'Z_imag': np.array([-50, -40, -30, -20, -10]),
        }
        self._manual_data = {
            'freq': np.array([1, 10, 100, 1000, 10000]),
            'Z_real': np.array([90, 70, 50, 30, 10]),
            'Z_imag': np.array([-45, -35, -25, -15, -5]),
        }

        self._original_base_data = copy.deepcopy(self._base_data)
        self._original_manual_data = copy.deepcopy(self._manual_data)
        self._auto_range_in_progress = False

    def _init_ui(self):
        """Setup the UI: title, grid, auto-scale button, etc."""
        self.setTitle("Parent Graph")
        self.showGrid(x=True, y=True)

        self._create_auto_scale_button()

    def _create_auto_scale_button(self):
        self.auto_scale_button = QPushButton("", self)
        self.auto_scale_button.setCheckable(True)
        self.auto_scale_button.setGeometry(10, 10, 15, 15)
        self.auto_scale_button.toggled.connect(self._handle_auto_scale_toggle)
        self.auto_scale_button.setStyleSheet("""
            QPushButton { background-color: lightgray; }
            QPushButton:checked { background-color: rgb(102, 178, 255); }
        """)

    def _init_signals(self):
        self.plotItem.getViewBox().sigRangeChanged.connect(self._on_view_range_changed)

    def _create_plot_items(self):
        """
        Create the static and dynamic plot items once. Do not re-create them every time.
        """
        # Static plot item (base data)
        self._static_plot = self.plot(
            pen='g',  # green line
            symbol='o',
            symbolSize=6,
            symbolBrush='g', symbolPen='g'
        )
        # Dynamic plot item (manual data)
        self._dynamic_plot = self.plot(
            pen=pg.mkPen(color='c', width=2),
            symbol='o',
            symbolSize=11,
            symbolBrush=None, symbolPen='c'
        )

    def _refresh_graph(self):
        """
        Updates the existing static and dynamic plot items with current data.
        No more clearing or re-adding new plot items each time.
        """
        self._refresh_plot(self._manual_data, self._dynamic_plot)
        self._refresh_plot(self._base_data, self._static_plot)

    def _refresh_plot(self, data_dict, plot_item):
        """
        Update a single plot item with new data. data_dict must have freq, Z_real, Z_imag.
        """
        if plot_item is None:
            return  # Not yet created
        x, y = self._prepare_xy(
            data_dict['freq'],
            data_dict['Z_real'],
            data_dict['Z_imag']
        )
        plot_item.setData(x, y)

    def _prepare_xy(self, freq, z_real, z_imag):
        """
        Default transformation: (Z_real, Z_imag) -> (x, y).
        Subclasses override for Bode, Phase, etc.
        """
        return z_real, z_imag

    def _handle_auto_scale_toggle(self, checked):
        if checked:
            self._apply_auto_scale()

    def _on_view_range_changed(self, view_box, view_range):
        if self.auto_scale_button.isChecked() and not self._auto_range_in_progress:
            self._apply_auto_scale()

    def _apply_auto_scale(self):
        """
        Auto-scales the view based on the static (base) plot data.
        """
        x_data, y_data = self._prepare_xy(
            self._base_data['freq'],
            self._base_data['Z_real'],
            self._base_data['Z_imag']
        )
        if x_data.size and y_data.size:
            x_min, x_max = np.min(x_data), np.max(x_data)
            y_min, y_max = np.min(y_data), np.max(y_data)

            self._auto_range_in_progress = True
            self.plotItem.getViewBox().setRange(
                xRange=(x_min, x_max),
                yRange=(y_min, y_max),
                padding= self._autoscale_padding
            )
            self._auto_range_in_progress = False

    def _mouse_moved(self, pos):
        """
        Snaps the hover label to the nearest data point, using pixel distances
        instead of data-space distances. That way, a single threshold works
        across very different scales.
        """
        #sets how close the point needs to be to the cursor
        threshold_pixels = 5.0
            
        # We'll store (distance_in_pixels, x_in_data, y_in_data).
        candidates = []
    
        # Gather points from base data
        x_base, y_base = self._prepare_xy(
            self._base_data['freq'],
            self._base_data['Z_real'],
            self._base_data['Z_imag'],
        )
        candidates.extend(
            self._build_scene_candidates(pos, x_base, y_base)
        )
    
        # Gather points from manual data
        x_man, y_man = self._prepare_xy(
            self._manual_data['freq'],
            self._manual_data['Z_real'],
            self._manual_data['Z_imag'],
        )
        candidates.extend(
            self._build_scene_candidates(pos, x_man, y_man)
        )
    
        # If this is ColeColeGraph or if there's secondary data
        if hasattr(self, '_secondary_manual_data') and self._secondary_manual_data['freq'].size > 0:
            x_sec, y_sec = self._prepare_xy(
                self._secondary_manual_data['freq'],
                self._secondary_manual_data['Z_real'],
                self._secondary_manual_data['Z_imag'],
            )
            candidates.extend(
                self._build_scene_candidates(pos, x_sec, y_sec)
            )
    
        label_text = ""
        if candidates:
            best = min(candidates, key=lambda t: t[0])  # t[0] is pixel distance

            if best[0] < threshold_pixels:
                # "Snap" to that point
                label_text = f"x: {best[1]:.5f}\ny: {best[2]:.5f}"
                self._coord_label.setPos(best[1], best[2])
            else:
                # If no point is near enough, hide label
                mouse_pt = self.plotItem.vb.mapSceneToView(pos)
                self._coord_label.setPos(mouse_pt.x(), mouse_pt.y())
    
        self._coord_label.setText(label_text)
    
    def _build_scene_candidates(self, mouse_scene_pos, x_array, y_array):
        """
        Given arrays of x, y in data space, convert them each to scene
        coords and measure pixel distance to mouse_scene_pos.
        Returns a list of (dist_in_pixels, x_data, y_data).
        """
        vb = self.plotItem.vb
        result = []
        for (xd, yd) in zip(x_array, y_array):
            # Convert (xd, yd) from data coords -> scene coords
            data_point_scene = vb.mapViewToScene(pg.QtCore.QPointF(xd, yd))
    
            # Pixel-distance from mouse to that data point
            dx = data_point_scene.x() - mouse_scene_pos.x()
            dy = data_point_scene.y() - mouse_scene_pos.y()
            dist_pixels = (dx*dx + dy*dy)**0.5
    
            result.append((dist_pixels, xd, yd))
    
        return result

    """
    #this version of mouse moved will display the values of any coordenates 
    #that the mouse is hoovering on
    def _mouse_moved(self, pos):
        # Convert scene pos -> data pos
        mouse_pt = self.plotItem.vb.mapSceneToView(pos)
        # Update text
        self._coord_label.setText(f'x: {mouse_pt.x():.2f}\ny: {mouse_pt.y():.2f}')
        # Place the label *at* the mouse data point
        self._coord_label.setPos(mouse_pt.x(), mouse_pt.y())

        self._coord_label.setFont(QFont('Arial', 5))
        self._coord_label.setPos(mouse_pt.x(), mouse_pt.y())
    """


class PhaseGraph(ParentGraph):
    def __init__(self):
        super().__init__()
        self._autoscale_padding = 0.0
        self.setTitle("Phase (Log Scale of Degrees)")
        self.setLabel('bottom', "log10(Freq[Hz])")
        self.setLabel('left', "log10(|Phase|)")
        self.getViewBox().invertX(True)

    def _prepare_xy(self, freq, z_real, z_imag):
        freq_log = np.log10(freq)
        phase_deg = np.degrees(np.arctan2(z_imag, z_real))
        phase_log = np.log10(np.abs(phase_deg) + 1e-10)  # Avoid log of zero
        return freq_log, phase_log
    
    def _apply_auto_scale(self):
        """
        Auto-scales the view based on the static (base) plot data,
        but clamps the X range to [-1, 6] to ensure edge ticks are visible.
        """
        # Clamp x-range to fixed hard bounds
        x_min =-1.2
        x_max = 6.08
        y_min =-1.2
        y_max = 2.4
    
        self._auto_range_in_progress = True
        self.plotItem.getViewBox().setRange(
        xRange=(x_min, x_max),
        yRange=(y_min, y_max),
            padding=self._autoscale_padding
        )
        self._auto_range_in_progress = False
    
        # Force edge ticks to be shown
        self.getPlotItem().getAxis('bottom').setTicks([
            [(i, str(i)) for i in range(int(x_min), int(x_max+1))]
        ])
        self.getPlotItem().getAxis('left').setTicks([
            [(i, str(i)) for i in range(int(y_min), int(y_max+1))]
        ])
      
    def _draw_special_marker(self, freq, zr, zi, symbol, color, filled):
        if symbol == 'x':
            x_vals, _ = self._prepare_xy(
                np.array([freq]), np.array([zr]), np.array([zi])
            )
            x0 = x_vals[0]
            y_min, y_max = self.getViewBox().viewRange()[1]
            return self.plot(
                [x0, x0], [y_min, y_max],
                pen=mkPen(color, width=2),
                symbol=None
            )
        else:
            return super()._draw_special_marker(
                freq, zr, zi,
                symbol, color, filled
            )
        
                    
class BodeGraph(ParentGraph):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        
        self._autoscale_padding = 0.0 
        self.setTitle("Impedance Magnitude Graph")
        self.setLabel('bottom', "log10(Freq[Hz])")
        self.setLabel('left', "Log10 Magnitude [dB]")
        
        self.getViewBox().invertX(True)

    def _prepare_xy(self, freq, z_real, z_imag):
        freq_log = np.log10(freq)
        mag = np.sqrt(z_real**2 + z_imag**2)
        mag_db = np.log10(mag)  # or 20*np.log10(mag) if you really want dB
        return freq_log, mag_db

    def _draw_special_marker(self, freq, zr, zi, symbol, color, filled):
        if symbol == 'x':
            x_vals, _ = self._prepare_xy(
                np.array([freq]), np.array([zr]), np.array([zi])
            )
            x0 = x_vals[0]
            y_min, y_max = self.getViewBox().viewRange()[1]
            return self.plot(
                [x0, x0], [y_min, y_max],
                pen=mkPen(color, width=2),
                symbol=None
            )
        else:
            # **CORRECT super call** – keep the same order
            return super()._draw_special_marker(
                freq, zr, zi,
                symbol, color, filled
            )
    
    def _apply_auto_scale(self):
        """
        Auto-scales the view based on the static (base) plot data,
        but clamps the X range to [-1, 6] to ensure edge ticks are visible.
        """
        # Clamp x-range to fixed hard bounds
        x_min =-1.2
        x_max = 6.08
        y_min = 2.8
        y_max = 7.4
    
        self._auto_range_in_progress = True
        self.plotItem.getViewBox().setRange(
        xRange=(x_min, x_max),
        yRange=(y_min, y_max),
            padding=self._autoscale_padding
        )
        self._auto_range_in_progress = False
    
        # Force edge ticks to be shown
        self.getPlotItem().getAxis('bottom').setTicks([
            [(i, str(i)) for i in range(int(x_min), int(x_max+1))]
        ])
        self.getPlotItem().getAxis('left').setTicks([
            [(i, str(i)) for i in range(int(y_min), int(y_max+1))]
        ])

    
class ColeColeGraph(ParentGraph):
    """
    Plots real(Z) vs. -imag(Z), plus a secondary manual line.
    """

    def __init__(self):
        
        #modifications needed to add the third plot line
        self._secondary_manual_data = {
            'freq': np.array([]),
            'Z_real': np.array([]),
            'Z_imag': np.array([]),
        }
        self._original_secondary_manual_data = copy.deepcopy(self._secondary_manual_data)  # CHANGED: Save original secondary data for filtering
        self._secondary_plot = None
        
        # Call to parent constructor
        super().__init__()
        
        # Titles and extra visual elements
        # self._autoscale_padding = 0.1 #uncoment if the padding desired differs from the 0.1 parent default
        self.getPlotItem().setAspectLocked(True, 1)
        self.setTitle("Cole-Cole Graph")
        self.setLabel('bottom', "Z' [Ohms]")
        self.setLabel('left', "-Z'' [Ohms]")
        
        # Adding magenta lines
        x_zero_line = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen(color='magenta', width=1))
        y_zero_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen(color='magenta', width=1))
        self.addItem(x_zero_line)
        self.addItem(y_zero_line)

    def _create_plot_items(self):
        """
        Create the main two plot items plus a secondary plot item.
        """
        super()._create_plot_items()
        # Add a third line for the secondary manual data (pink line)
        self._secondary_plot = self.plot(
            pen=pg.mkPen(color='#F4C2C2', style=Qt.DashLine),
            symbol='o',
            symbolSize=2,
            symbolBrush='#F4C2C2'
        )

    def _refresh_graph(self):
        """
        Update base/manual lines plus the secondary line.
        """
        super()._refresh_graph()
        self._refresh_plot(self._secondary_manual_data, self._secondary_plot)

    def update_parameters_secondary_manual(self, freq, Z_real, Z_imag):
        self._secondary_manual_data = {
            'freq': freq,
            'Z_real': Z_real,
            'Z_imag': Z_imag
        }
        self._original_secondary_manual_data = copy.deepcopy(self._secondary_manual_data)  # CHANGED: Update original secondary data for filtering
        if self._secondary_plot is not None:
            self._refresh_plot(self._secondary_manual_data, self._secondary_plot)

    def filter_frequency_range(self, f_min, f_max):  # CHANGED: Overriding filter_frequency_range to include secondary data
        # Filter base and primary manual data using the parent method
        super().filter_frequency_range(f_min, f_max)
        
        # Now filter the secondary manual data (pink line)
        if hasattr(self, '_original_secondary_manual_data'):
            secondary_mask = (
                (self._original_secondary_manual_data['freq'] >= f_min) &
                (self._original_secondary_manual_data['freq'] <= f_max)
            )
            self._secondary_manual_data = {
                'freq': self._original_secondary_manual_data['freq'][secondary_mask],
                'Z_real': self._original_secondary_manual_data['Z_real'][secondary_mask],
                'Z_imag': self._original_secondary_manual_data['Z_imag'][secondary_mask],
            }
            self._refresh_plot(self._secondary_manual_data, self._secondary_plot)

    def _prepare_xy(self, freq, z_real, z_imag):
        return z_real, -z_imag

    def _apply_auto_scale(self):
        """
        Auto-scales the view based on the static (base) plot data,
        and ensures that (0,0) is always visible.
        """
        x_data, y_data = self._prepare_xy(
            self._base_data['freq'],
            self._base_data['Z_real'],
            self._base_data['Z_imag']
        )
        if x_data.size and y_data.size:
            x_min, x_max = np.min(x_data), np.max(x_data)
            y_min, y_max = np.min(y_data), np.max(y_data)
    
            # Ensure (0, 0) is included in the visible range
            x_min = min(x_min, 0)
            x_max = max(x_max, 0)
            y_min = min(y_min, 0)
            y_max = max(y_max, 0)
    
            self._auto_range_in_progress = True
            self.plotItem.getViewBox().setRange(
                xRange=(x_min, x_max),
                yRange=(y_min, y_max),
                padding= self._autoscale_padding
            )
            self._auto_range_in_progress = False


class TimeGraph(ParentGraph):
    
    LOG_Y_AXIS = False # False # === Set this to True for a logarithmic Y‑axis (Voltage)

    def __init__(self):
        
        self._secondary_manual_data = {
            'freq': np.array([]),
            'Z_real': np.array([]),  # time
            'Z_imag': np.array([]),  # voltage_up
        }
        self._secondary_dynamic_plot = None

        self.mx = self.mt = self.m0 = self.Vp = None
        # Anchor so that (1, 0) is the reference point – top-right corner of the text.
        self.mx_text = pg.TextItem(color='w', anchor=(1, 0))
        self.mt_text = pg.TextItem(color='w', anchor=(1, 0))
        self.m0_text = pg.TextItem(color='w', anchor=(1, 0))

        super().__init__()
        
        # configure title & labels
        self._configure_plot()
        
        # apply log‑mode if requested
        if self.LOG_Y_AXIS:
            # PlotItem.setLogMode(x=…, y=…) lives on both PlotWidget & PlotItem
            self.plotItem.setLogMode(x=False, y=True)
        
        self._setup_text_items()
        self._refresh_graph()
        #self.plotItem.vb.setLimits(xMin=0.0, yMin=0.0)
        self.plotItem.getViewBox().autoRange()

    def _configure_plot(self):
        self.setTitle("Time Domain Graph")
        self.setLabel('bottom', "Time [s]")
        self.setLabel('left', "Voltage" + (" (log)" if self.LOG_Y_AXIS else ""))

    def _create_plot_items(self):
        super()._create_plot_items()
        
        if self._static_plot is not None:
            self._static_plot.setSymbol(None)
            self._static_plot.hide()
        if self._dynamic_plot is not None:
            self._dynamic_plot.setSymbol(None)
            self._dynamic_plot.setPen(pg.mkPen(color='r', width=2))  # Red line for manual data

        # Shading item.
        self._shading_item = pg.PlotDataItem(
            pen=pg.mkPen('c', width=0),
            fillLevel=0,
            brush=pg.mkBrush(0, 255, 0, 180)
        )
        self._shading_item.setZValue(-10)  # Ensure it's behind other plot elements
        self.addItem(self._shading_item)

        # Secondary line for "voltage_up."
        self._secondary_dynamic_plot = self.plot(
            pen=pg.mkPen(color='white', width=2)
        )
        self._secondary_dynamic_plot.setSymbol(None)

    def _setup_text_items(self):
        """
        Connect the text items to the ViewBox so that we can control their
        positions in screen (scene) space. We then attach a slot to sigResized
        to update their positions whenever the plot is resized.
        """
        vb = self.plotItem.vb
        for txt in (self.mx_text, self.mt_text, self.m0_text):
            txt.setParentItem(vb)

        # Update positions when the ViewBox is resized
        vb.sigResized.connect(self._update_text_positions)
        # Ensure positions are correct immediately
        self._update_text_positions()
            
    def _update_text_positions(self):
        """
        Positions the Mx, Mt, M0 labels relative to the plot size,
        so they automatically adjust with window/DPI changes.
    
        ADJUST THESE to move the tags:
          x_pct       = fraction of width to inset from the right  (increase → move left)
          y_pct       = fraction of height to inset from the top   (increase → move down)
          spacing_pct = fraction of height between each label      (increase → more gap)
        """
        vb = self.plotItem.vb
    
        # 1) Fixed-pixel font & ignore transformations
        font = pg.QtGui.QFont()
        font.setPointSizeF(15)
        font.setBold(True)
        for txt in (self.mx_text, self.mt_text, self.m0_text):
            txt.setFont(font)
            txt.setFlag(pg.QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
            txt.setParentItem(vb)
    
        # 2) Get the view & its size in device pixels
        views = vb.scene().views()
        if not views:
            return
        view = views[0]
        vp = view.viewport()
        w_px = vp.width()
        h_px = vp.height()
    
        # === Tweak these ===
        x_pct       = 0.20   # 20% in from right; increase to move labels further left
        y_pct       = 0.15   # 15% down from top; increase to move labels lower
        spacing_pct = 0.05   #  5% of height between each label; increase for more gap
        # ====================
    
        # 3) Compute absolute pixel offsets
        x_off_px   = int(w_px * x_pct)
        y_off_px   = int(h_px * y_pct)
        spacing_px = int(h_px * spacing_pct)
    
        # 4) Map view‑pixel positions into the scene
        m0_scene = view.mapToScene(w_px - x_off_px, y_off_px )
        mx_scene = view.mapToScene(w_px - x_off_px, y_off_px + spacing_px)
        mt_scene = view.mapToScene(w_px - x_off_px, y_off_px + 2*spacing_px)

    
        # 5) Apply positions
        self.mx_text.setPos(mx_scene)
        self.mt_text.setPos(mt_scene)
        self.m0_text.setPos(m0_scene)

    def _refresh_graph(self):
        """
        Updates:
          - The main (base) line
          - The manual (dynamic) line
          - The secondary "voltage_up" line
          - The shaded region
          - M-values text (Mx, Mt, M0)
        Called by the parent or in update methods.
        """
        # Update the parent’s base + manual lines
        super()._refresh_graph()

        # Refresh the secondary line if there's data
        self._refresh_plot(self._secondary_manual_data, self._secondary_dynamic_plot)

        # Update the shading and M-values
        self._update_shading_and_text()

        # Auto-range once at the end
        self.plotItem.getViewBox().autoRange()

    def _prepare_xy(self, freq, z_real, z_imag):
        """
        For this time plot: interpret Z_real as time, Z_imag as voltage.
        The freq array is not directly used here, but we keep the signature
        for consistency.
        """
        return z_real, z_imag

    def update_parameters_base(self, freq, z_real, z_imag):
        """
        Set new 'base' (static) data. Just calls the parent's method
        and optionally re-refreshes if needed.
        """
        super().update_parameters_base(freq, z_real, z_imag)

    def update_parameters_manual(self, freq, time, voltage_down, voltage_up):
        """
        - The parent's manual data holds (time, voltage_down).
        - The 'secondary' line will hold (time, voltage_up).
        """
        super().update_parameters_manual(freq, time, voltage_down)

        # Assign the secondary data (voltage_up)
        self._secondary_manual_data = {
            'freq': freq,
            'Z_real': time,
            'Z_imag': voltage_up
        }
        if self._secondary_dynamic_plot is not None:
            self._refresh_plot(self._secondary_manual_data, self._secondary_dynamic_plot)

        # Recompute shading and M-values
        self._refresh_graph()

    def _update_shading_and_text(self):
        """
        Computes the shading region, draws it via self._shading_item,
        and updates Mx, Mt, M0 text. 
        """
        t = self._manual_data['Z_real']  # time
        v = self._manual_data['Z_imag']  # voltage down

        # If there's no data, clear shading and return
        if t.size == 0 or v.size == 0:
            self._shading_item.setData([], [])
            return

        # Example shading region [0.45, 1.1]
        start_shading = 0.45
        end_shading = 1.1
        mask = (t >= start_shading) & (t <= end_shading)

        if np.any(mask):
            # Use the dedicated shading item so we don't add new items each time
            self._shading_item.setData(t[mask], v[mask])
        else:
            # No shading in that range
            self._shading_item.setData([], [])

        # Compute M-values
        self.Vp = np.interp(0.0, t, v)
        if abs(self.Vp) < 1e-12:
            self.mx, self.mt, self.m0 = 0.0, 0.0, 0.0
        else:
            integral_mx = self._integrate_chargeability(t, v, 0.45, 1.1)
            integral_mt = self._integrate_chargeability(t, v, 0.0, 2.0)
            v_at_0p001 = np.interp(0.001, t, v) if np.any(t >= 0.001) else 0.0

            self.mx = 1000.0 * (integral_mx / self.Vp)
            self.mt = 1000.0 * (integral_mt / self.Vp)
            self.m0 = (v_at_0p001 / self.Vp)

        # Update the text items
        self.mx_text.setText(f"Mx= {self.mx:8.3f} ms")
        self.mt_text.setText(f"Mt= {self.mt:9.3f} ms")
        self.m0_text.setText(f"M0 = {self.m0:13.3f}")
        
        w = self
        while w is not None and not isinstance(w, QTabWidget):
            w = w.parentWidget()
        if isinstance(w, QTabWidget):
            idx = w.indexOf(self)
            if idx != -1:
                w.setTabText(idx, f"Time Domain Graph: Mx {self.mx:6.3f} ms")

    @staticmethod
    def _integrate_chargeability(t, v, tmin, tmax):
        """
        Simple trapezoidal integration of v(t) from tmin to tmax.
        """
        mask = (t >= tmin) & (t <= tmax)
        if not np.any(mask):
            return 0.0
        return np.trapz(y=v[mask], x=t[mask])

    def get_special_values(self):
        """
        Example method returning the last computed M-values.
        """
        return {'mx': self.mx, 'mt': self.mt, 'm0': self.m0, 'Vp': self.Vp}

    def _apply_auto_scale(self):
        # Collect base data
        x_base, y_base = self._prepare_xy(
            self._base_data['freq'],
            self._base_data['Z_real'],
            self._base_data['Z_imag'],
        )
        # Collect manual (time) data
        x_manual, y_manual = self._prepare_xy(
            self._manual_data['freq'],
            self._manual_data['Z_real'],
            self._manual_data['Z_imag'],
        )
        # Optionally collect secondary data
        x_sec, y_sec = self._prepare_xy(
            self._secondary_manual_data['freq'],
            self._secondary_manual_data['Z_real'],
            self._secondary_manual_data['Z_imag'],
        )

        # Combine them all
        all_x = np.concatenate([x_base, x_manual, x_sec])
        all_y = np.concatenate([y_base, y_manual, y_sec])

        # Skip if empty
        if all_x.size == 0 or all_y.size == 0:
            return

        x_min, x_max = np.min(all_x), np.max(all_x)
        y_min, y_max = np.min(all_y), np.max(all_y)

        self._auto_range_in_progress = True
        self.plotItem.getViewBox().setRange(
            xRange=(x_min, x_max),
            yRange=(y_min, y_max),
            padding=0.0
        )
        self._auto_range_in_progress = False
        

class WidgetGraphs(QWidget):
    """
    A widget with multiple graphs in a split/tabbed layout.
    """
    
    def __init__(self):
        super().__init__()
        self._init_graphs()
        self._init_ui()

    def _init_graphs(self):
        self._big_graph = ColeColeGraph()
        self._small_graph_1 = BodeGraph()
        self._small_graph_2 = PhaseGraph()
        self._tab_graph = TimeGraph()

    def _init_ui(self):
        self._tab_widget = QTabWidget()
        self._tab_widget.addTab(self._big_graph, "Cole Graph")
        self._tab_widget.addTab(self._tab_graph, f"T.Domain Graph")
        self._tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._tab_widget.setStyleSheet("QTabWidget::pane { border: none; }")
        
        tab_bar = self._tab_widget.tabBar()
        font = tab_bar.font()
        font.setPointSizeF(9)
        tab_bar.setFont(font)
    
        tab_bar_height = self._tab_widget.tabBar().sizeHint().height()
    
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel(tab_bar_height)
    
        # Use QSplitter to allow manual dragging between the left and right panels.
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Optionally, set initial sizes.
        splitter.setSizes([600, 300])  # Adjust these numbers as needed.
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        # Instead of adding left_panel and right_panel directly, add the splitter.
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def _create_left_panel(self):
        frame = self._create_frame()
        layout = self._create_vbox_layout(frame)
        layout.addWidget(self._tab_widget)
        return frame

    def _create_right_panel(self, tab_bar_height):
        frame = self._create_frame()
        layout = self._create_vbox_layout(frame, margins=(0, tab_bar_height, 0, 0))
        layout.addWidget(self._small_graph_1)
        layout.addWidget(self._small_graph_2)
        return frame

    @staticmethod
    def _create_frame():
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        return frame

    @staticmethod
    def _create_vbox_layout(parent, margins=(0, 0, 0, 0)):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(*margins)
        layout.setSpacing(0)
        return layout

    #---------------------------------------------
    #   Public Methods
    #---------------------------------------------
    def reset_default_values(self):
        self._big_graph.reset_default_values()
        self._small_graph_1.reset_default_values()
        self._small_graph_2.reset_default_values()
        self._tab_graph.reset_default_values()
    
    def update_front_graphs(self, freq, z_real, z_imag):
        self._big_graph.update_parameters_base(freq, z_real, z_imag)
        self._small_graph_1.update_parameters_base(freq, z_real, z_imag)
        self._small_graph_2.update_parameters_base(freq, z_real, z_imag)

    def update_timedomain_graph(self, freq, time, voltage):
        self._tab_graph.update_parameters_base(freq, time, voltage)

    def update_manual_plot(self, calc_result):
        freq_main = calc_result.main_freq
        z_real_main = calc_result.main_z_real
        z_imag_main = calc_result.main_z_imag
        z_rock_real = calc_result.rock_z_real
        z_rock_imag = calc_result.rock_z_imag

        self._big_graph.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        self._small_graph_1.update_parameters_manual(freq_main, z_real_main, z_imag_main)
        self._small_graph_2.update_parameters_manual(freq_main, z_real_main, z_imag_main)

        self._big_graph.update_parameters_secondary_manual(freq_main, z_rock_real, z_rock_imag)

        freq_sp = calc_result.special_freq
        z_real_sp = calc_result.special_z_real
        z_imag_sp = calc_result.special_z_imag
        self._big_graph.update_special_frequencies(freq_sp, z_real_sp, z_imag_sp)
        self._small_graph_1.update_special_frequencies(freq_sp, z_real_sp, z_imag_sp)
        self._small_graph_2.update_special_frequencies(freq_sp, z_real_sp, z_imag_sp)

        self._tab_graph.update_parameters_manual(
            calc_result.timedomain_freq,
            calc_result.timedomain_time,
            calc_result.timedomain_volt_down,
            calc_result.timedomain_volt_up
        )

    def apply_filter_frequency_range(self, f_min, f_max):
        self._big_graph.filter_frequency_range(f_min, f_max)
        self._small_graph_1.filter_frequency_range(f_min, f_max)
        self._small_graph_2.filter_frequency_range(f_min, f_max)

    def get_graphs_parameters(self):
        return self._tab_graph.get_special_values()


# -----------------------------------------------------------------------
#  Quick Test
# -----------------------------------------------------------------------
import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout,
    QSlider, QLabel
)
from PyQt5.QtCore import Qt

###############################################################################
# TestWidget
###############################################################################
class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manual Test: Blue & Pink lines move (ColeColeGraph)")

        # 1) Create the main "WidgetGraphs" container
        self.graphs = WidgetGraphs()

        # 2) Create sliders & labels for parameters
        params = [("param1", 20), ("param2", 10), ("param3", 5)]
        self.sliders, self.labels = {}, {}
        slider_layout = QVBoxLayout()
        for name, init_val in params:
            label = QLabel(f"{name}: {init_val}")
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)  # slider from 0..100
            slider.setValue(init_val)
            slider.valueChanged.connect(self._update_blue_line)

            self.labels[name] = label
            self.sliders[name] = slider

            slider_layout.addWidget(label)
            slider_layout.addWidget(slider)

        # 2.5) Add reset button
        self.reset_button = QPushButton("Reset Defaults")
        self.reset_button.clicked.connect(self._handle_reset_defaults)
        slider_layout.addWidget(self.reset_button)

        # 3) Put everything in the main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.graphs, stretch=1)
        main_layout.addLayout(slider_layout)
        self.setLayout(main_layout)

        # 4) Generate & set up the base (green) data once
        self.base_data = self._generate_base_data()
        freq, z_real, z_imag, time, volt = self.base_data
        self.graphs.update_front_graphs(freq, z_real, z_imag)    # Cole/Bode/Phase
        self.graphs.update_timedomain_graph(freq, time, volt)    # TimeGraph

        # 5) Initial draw of the manual lines (blue & pink)
        self._update_blue_line()

    @staticmethod
    def _generate_base_data(num_points=50):
        """
        Creates some 'base' data for testing.
        """
        freq = np.logspace(0, 5, num_points)   # 1 .. 100000
        z_real = 50 + 10 * np.sqrt(freq)       # some made-up data
        z_imag = -5 * np.log10(freq + 1)
        time = np.linspace(0, 1, 200)          # 0..1
        volt = 0.5 * np.sin(2 * np.pi * 5 * time)
        return freq, z_real, z_imag, time, volt

    @staticmethod
    def _generate_manual_data(base_data, param1, param2, param3):
        """
        Generates the 'manual' (blue) line data from the base data,
        with transformations to make changes clearly visible.
        """
        freq, z_real, z_imag, time, volt = base_data

        # Increase factor & offset so changes are obvious:
        # param1 (0..100) => factor ~ [1..6], param2 => offset up to ~50, etc.
        factor = 1 + param1 / 20.0
        offset_z = param2 * 0.5
        offset_v = param3 / 20.0

        freq_out = freq
        z_real_out = factor * (z_real + offset_z)
        z_imag_out = factor * (z_imag + offset_z)
        volt_out = factor * volt + offset_v

        return freq_out, z_real_out, z_imag_out, time, volt_out

    def _update_blue_line(self):
        """
        1) Re-compute the 'manual' (blue) data from sliders,
        2) Update it in all relevant graphs,
        3) Generate & update the 'secondary' pink line in ColeColeGraph.
        """
        # -- Read slider values --
        p1 = self.sliders["param1"].value()
        p2 = self.sliders["param2"].value()
        p3 = self.sliders["param3"].value()

        # -- Update labels --
        for name, val in zip(["param1", "param2", "param3"], (p1, p2, p3)):
            self.labels[name].setText(f"{name}: {val}")

        # -- 1) Update the BLUE line --
        freq, z_real, z_imag, time, volt = self._generate_manual_data(
            self.base_data, p1, p2, p3
        )

        # Update the 'blue line' (manual) in Cole/Bode/Phase
        self.graphs._big_graph.update_parameters_manual(freq, z_real, z_imag)
        self.graphs._small_graph_1.update_parameters_manual(freq, z_real, z_imag)
        self.graphs._small_graph_2.update_parameters_manual(freq, z_real, z_imag)

        # Update the 'blue line' in the TimeDomain
        self.graphs._tab_graph.update_parameters_manual(freq, time, volt, -volt)

        # -- 2) Update the PINK (secondary) line in ColeColeGraph --
        # Create a bigger shift so the pink line is clearly different:
        freq2 = freq * (1.2 + p1 / 15.0)
        z_real2 = z_real + 30 + 2 * p2
        z_imag2 = z_imag - 30 - 2 * p3

        # This method is only valid on ColeColeGraph
        self.graphs._big_graph.update_parameters_secondary_manual(
            freq2, z_real2, z_imag2
        )

    def _handle_reset_defaults(self):
        self.graphs.reset_default_values()
        # Reset sliders to their initial values
        self.sliders["param1"].setValue(20)
        self.sliders["param2"].setValue(10)
        self.sliders["param3"].setValue(5)
        # Ensure the blue/pink lines are also redrawn to match
        self._update_blue_line()

###############################################################################
#  MAIN
###############################################################################

if __name__ == '__main__':
    
    from PyQt5.QtWidgets import QApplication

#---Allowing proper display in different resolutions-----------------------
    import platform
    import ctypes
    if platform.system()=='Windows' and int(platform.release()) >= 8:   
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
#---Allowing proper display in different resolutions-----------------------    
    
    # Make sure we have a QApplication instance
    app = QApplication(sys.argv)
    
#    app.setAttribute(Qt.AA_Use96Dpi) #maybe it is fixing it to the wrong value?
 

    # Create and show the test widget
    tester = TestWidget()
    tester.show()

    sys.exit(app.exec_())
