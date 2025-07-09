# -*- coding: utf-8 -*-
"""
Created on Thu Feb  6 15:21:01 2025

@author: agarcian
"""

import sys
import math
from PyQt5.QtGui import QFontMetrics, QFont
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QApplication, QSlider, QVBoxLayout, QWidget, QLabel


# ---------------------------------------------------------------------
# Single-handle slider that maps a list of discrete values.
# ---------------------------------------------------------------------
class ListSlider(QtWidgets.QSlider):
    
    """
    A single-handle slider that maps a list of discrete values.
    The slider's internal integer range corresponds directly to the indices
    of the provided values_list.
    """
    
    #emmits a signal when the slider is set to a new list
    new_list_was_set = pyqtSignal(int)
    
    def __init__(self, values_list=None, font = 7, *args, **kwargs):
        """
        Initialize the slider.
        Args:values_list (list, optional): List of discrete values.
        """
        super().__init__(*args, **kwargs)
        if values_list is None:
            values_list = [0.0]
            
        self.values_list = values_list
        self.my_font = font
        
        font = QtGui.QFont("Arial")
        font.setPointSizeF(self.my_font)
        self._initialize_orientation()
        self._configure_range()
        self._apply_custom_style()
        self.setContentsMargins(0, 0, 0, 0) #new change
        
    #-----------------------
    # public Methods
    #------------------------
    def get_list_value(self):
        """
        Return the value corresponding to the current slider index.
        
        Returns:
            The discrete value from values_list based on the current index.
        """
        idx = self.value()
        if 0 <= idx < len(self.values_list):
            return self.values_list[idx]
        return None

    def set_list_value(self, value):
        """
        Set the slider based on the given value from the list.

        Args:
            value: The value to select from values_list.
        """
        if value in self.values_list:
            index = self.values_list.index(value)
            self.setValue(index)
            self.update()
        else: print("Value not found.")

    def set_list_value_index(self, index):
        """
        Set the slider based on the given index of the list.

        Args:
            index: The index to select from values_list.
        """
    
        index = int(index)
        
        if 0 < index < len(self.values_list):
            self.setValue(index)
            self.update()
        else: print(f"Index {index} is out of bounds.")

    def set_list(self, values_list: list[float]):
        """
        Update the slider with a new list of valid values.

        Args:
            values_list (list): New list of discrete values.
        """
        if not values_list:
            self.values_list = [0.0]
        else:
            self.values_list = values_list
        # Update the slider's range to match the new list length.
        self.setMinimum(0)
        self.setMaximum(len(self.values_list) - 1)
        self.setValue(self.minimum())
        self.update()
        
        #emit signal to allow updating label in OutputWidget
        self.new_list_was_set.emit(len(self.values_list))

    def up(self):
        """
        Move the slider one step upward (to a higher index).
        """
        current = self.value()
        new_val = current + 1
        if new_val <= self.maximum():
            self.setValue(new_val)

    def down(self):
        """
        Move the slider one step downward (to a lower index).
        """
        current = self.value()
        new_val = current - 1
        if new_val >= self.minimum():
            self.setValue(new_val)
    
    def minimumSizeHint(self) -> QSize:
        base = super().minimumSizeHint()
        # figure out how tall your font is
        fm = QFontMetrics(self.font())
        label_height = fm.height()
        # plus a couple pixels of spacing
        extra = label_height + 4  
        return QSize(base.width(), base.height() + extra)
    
    def sizeHint(self) -> QSize:
        # same idea for sizeHint if you want “preferred” size to grow, too
        base = super().sizeHint()
        fm = QFontMetrics(self.font())
        label_height = fm.height()
        extra = label_height + 4
        return QSize(base.width(), base.height() + extra)

    #-----------------------
    # Private Methods
    #------------------------

    def _initialize_orientation(self):
        """Set the slider orientation to horizontal."""
        self.setOrientation(Qt.Horizontal)

    def _configure_range(self):
        """
        Configure the slider's range to match the indices of values_list,
        and set its initial value.
        """
        self.setMinimum(0)
        self.setMaximum(len(self.values_list) - 1)
        self.setValue(self.minimum())

    def _apply_custom_style(self):
        """Apply a custom style to improve the slider's visual appearance."""
        groove_height = 6            
        groove_radius = 4           
        groove_margin = 2           
        handle_width = 6           
        handle_margin = -5          
        handle_radius = 8        
        border_width = 1       

        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: {border_width}px solid #bbb;
                background: white;
                height: {groove_height}px;
                border-radius: {groove_radius}px;
                margin: {groove_margin}px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: #0078D7;
                border-radius: {groove_radius}px;
            }}
            QSlider::add-page:horizontal {{
                background: #bbb;
                border-radius: {groove_radius}px;
            }}
            QSlider::handle:horizontal {{
                background: #005999;
                border: {border_width}px solid #0078D7;
                width: {handle_width}px;
                margin: {handle_margin}px 0;
                border-radius: {handle_radius}px;
            }}
        """)
         
    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.values_list:
            return
        if len(self.values_list) <2:
            return
        
        painter = QtGui.QPainter(self)
        font = QtGui.QFont("Arial")
        font.setPointSizeF(self.my_font)
        painter.setFont(font)
        font_metrics= painter.fontMetrics()
        
        slider_opt = QtWidgets.QStyleOptionSlider()
        
        self.initStyleOption(slider_opt)
        groove_rect = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider, slider_opt,
            QtWidgets.QStyle.SC_SliderGroove, self
        )
        box_x = groove_rect.x()
        box_y = groove_rect.y()
        box_length = groove_rect.width()  #clumsy accounting for tick length. Neess to refine later
        box_height = groove_rect.height()
        groove_bottom = groove_rect.bottom()

        space_of_tick= box_length / (len(self.values_list) -1 )
        
        tick_height = max(4, int(box_height * 0.3))
        step = ((len(self.values_list)  - 1) //10) +1
        
        for i, value in enumerate(self.values_list):
            if i % step == 0:
                
               label = f"{i+1}" 
               
               x = box_x + int(i * space_of_tick)
               label_width = font_metrics.horizontalAdvance(label)
               label_height = font_metrics.height()
               
               # Align text *centered horizontally* under the tick
               text_x = x - label_width // 2
               # Place text below the groove with DPI-aware padding
               padding = 4   # or tweak as needed
               text_y = groove_bottom + tick_height + label_height + padding
               
               painter.drawLine(x, groove_bottom + 1, x, groove_bottom + 1 + tick_height)
               painter.drawText(text_x, text_y, label)


# ---------------------------------------------------------------------
# Dual-handle slider for log10 ranges.
# ---------------------------------------------------------------------
class ListSliderRange(QtWidgets.QSlider):
    """
    A dual-handle slider for log10 ranges.
    QSlider remains integer-based; here the integers represent indices for the
    discrete log10-scaled values in values_list.
    """
    sliderMoved = pyqtSignal(int, int, float, float)
    # The signal emits: (low_index, high_index, low_value, high_value)

    def __init__(self, values_list=None, font=8, *args):
        """Initialize the range slider."""
        
        super().__init__(*args)
        self.my_font = font
        self._setup_slider_configuration(values_list)
        self._init_mouse_variables()

#-------------------------------------
# Public methods
#-----------------------------------------
    def up(self):
        """
        Move the slider one step upward (to a higher index).
        """
        current = self.value()
        new_val = current + 1
        if new_val <= self.maximum():
            self.setValue(new_val)

    def down(self):
        """
        Move the slider one step downward (to a lower index).
        """
        current = self.value()
        new_val = current - 1
        if new_val >= self.minimum():
            self.setValue(new_val)

    def low(self):
        """Return the index of the lower handle."""
        return self._low

    def low_value(self):
        """Return the float value of the lower handle."""
        if 0 <= self._low < len(self.values_list):
            return self.values_list[self._low]
        return None

    def set_low(self, low: int):
        """
        Set the lower handle index, ensuring it is less than the high handle.

        Args:
            low (int): New lower index.
        """
        if low < self._high:
            self._low = low
            self.update()

    def high(self):
        """Return the index of the higher handle."""
        return self._high

    def high_value(self):
        """Return the float value of the higher handle."""
        if 0 <= self._high < len(self.values_list):
            return self.values_list[self._high]
        return None

    def set_high(self, high: int):
        """
        Set the higher handle index, ensuring it is greater than the low handle.

        Args:
            high (int): New higher index.
        """
        if self._low < high:
            self._high = high
            self.update()

    def set_list_value(self, value: float):
        """
        Set one of the handles based on the given value.
        Args:value: The desired value from values_list.
        """
        if value not in self.values_list:
            return  # Ignore if value is not valid.

        index = self.values_list.index(value)
        # Move the handle that is closer to the desired index.
        if abs(index - self._low) <= abs(index - self._high):
            self.set_low(index)
        else:
            self.set_high(index)
        self.update()

    def set_list(self, values_list: list):
        """
        Update the slider with a new list of valid values and adjust its range.
        Args:values_list (list): New list of discrete values.
        """
        if values_list is None or len(values_list) == 0:
            values_list = [0.0]
        self.values_list = values_list
        self.setMinimum(0)
        self.setMaximum(len(self.values_list) - 1)
        # Reset handles to the new extreme positions.
        self._low = self.minimum()
        self._high = self.maximum()
        self.update()
        self.sliderMoved.emit(self._low, self._high,
                              self.values_list[self._low],
                              self.values_list[self._high])

    def up_min(self):
        """
        Shift the lower handle upward by one index.
        Emit the updated indices and corresponding values.
        """
        new_low = self.low() + 1
        if new_low < self.high():
            self.set_low(new_low)
        self.sliderMoved.emit(self._low, self._high,
                              self.values_list[self._low],
                              self.values_list[self._high])

    def down_max(self):
        """
        Shift the upper handle downward by one index.
        Emit the updated indices and corresponding values.
        """
        new_high = self.high() - 1
        if new_high > self.low():
            self.set_high(new_high)
        self.sliderMoved.emit(self._low, self._high,
                              self.values_list[self._low],
                              self.values_list[self._high])

    def default(self):
        """
        Reset the slider to its full range.
        Emit the updated indices and corresponding values.
        """
        self._low = self.minimum()
        self._high = self.maximum()
        self.update()
        self.sliderMoved.emit(self._low, self._high,
                              self.values_list[self._low],
                              self.values_list[self._high])

#-----------------------------------------------
# Private methods
#-------------------------------------------
    def _setup_slider_configuration(self, values_list):
        """
        Setup the slider configuration: set the discrete value list, orientation,
        tick marks, range, handle positions, and dimensions.
        """
        if values_list is None:
            values_list = [0.0]
        self.values_list = values_list

        self.setOrientation(Qt.Vertical)
        self.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.setMinimum(0)
        self.setMaximum(len(self.values_list) - 1)
        self._low = self.minimum()
        self._high = self.maximum()
        self.setMinimumWidth(100)
        self.number_of_ticks = 20

    def _init_mouse_variables(self):
        """
        Initialize variables needed for mouse interaction.
        """
        self.pressed_control = QtWidgets.QStyle.SC_None
        self.hover_control = QtWidgets.QStyle.SC_None
        self.click_offset = 0
        self.active_slider = -1

    def _draw_ticks_and_labels(self, painter, groove_rect, style, opt):
        """
        Draw tick marks and numeric labels along the slider.

        Args:
            painter: QPainter object.
            groove_rect: Rectangle defining the slider groove.
            style: Current application style.
            opt: QStyleOptionSlider instance.
        """

        # Calculate tick interval based on the number of ticks.
        step = math.ceil((self.maximum() - self.minimum()) / (self.number_of_ticks - 1))
        if step:
            painter.setPen(QtGui.QPen(QtCore.Qt.black))
            painter.setFont(QtGui.QFont("Arial", self.my_font))
            tick_length = 8
            head_thickness = 5

            if opt.orientation == Qt.Horizontal:
                slider_min = groove_rect.x()
                slider_max = groove_rect.right()
                available = slider_max - slider_min
                text_offset = groove_rect.bottom() + 15
                tick_offset = groove_rect.bottom() + 2
            else:
                slider_min = groove_rect.y() + head_thickness
                slider_max = groove_rect.bottom() - head_thickness
                available = slider_max - slider_min
                text_offset = groove_rect.right() - 20
                tick_offset = groove_rect.right() - 35

            # Loop through indices and draw tick marks.
            for i in range(self.minimum(), self.maximum() + 1, step):
                pixel_offset = style.sliderPositionFromValue(
                    self.minimum(), self.maximum(), i, available, opt.upsideDown
                )
                label = f"{i}"
                if opt.orientation == Qt.Horizontal:
                    x = slider_min + pixel_offset
                    painter.drawLine(x, tick_offset, x, tick_offset + tick_length)
                    text_rect = QtCore.QRect(x - 15, text_offset, 30, 12)
                    painter.drawText(text_rect, QtCore.Qt.AlignCenter, label)
                else:
                    y = slider_min + pixel_offset
                    painter.drawLine(tick_offset, y, tick_offset + tick_length, y)
                    text_rect = QtCore.QRect(text_offset, y - 6, 50, 12)
                    painter.drawText(text_rect, QtCore.Qt.AlignVCenter, label)

    def _draw_span(self, painter, style, groove_rect, opt):
        """
        Draw the highlighted span (the area between the two handles).
        """
        self.initStyleOption(opt)
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        opt.sliderValue = 0

        # Get handle rectangles for the low and high handles.
        opt.sliderPosition = self._low
        low_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                        QtWidgets.QStyle.SC_SliderHandle, self)
        opt.sliderPosition = self._high
        high_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                         QtWidgets.QStyle.SC_SliderHandle, self)

        # Helper to choose coordinate based on orientation.
        def pick(pt):
            return pt.x() if opt.orientation == Qt.Horizontal else pt.y()

        low_pos = pick(low_rect.center())
        high_pos = pick(high_rect.center())
        min_pos = min(low_pos, high_pos)
        max_pos = max(low_pos, high_pos)
        center_pt = QtCore.QRect(low_rect.center(), high_rect.center()).center()

        if opt.orientation == Qt.Horizontal:
            span_rect = QtCore.QRect(
                QtCore.QPoint(min_pos, center_pt.y() - 2),
                QtCore.QPoint(max_pos, center_pt.y() + 2)
            )
            groove_rect.adjust(0, 0, -1, 0)
        else:
            span_rect = QtCore.QRect(
                QtCore.QPoint(center_pt.x() - 2, min_pos),
                QtCore.QPoint(center_pt.x() + 2, max_pos)
            )
            groove_rect.adjust(0, 0, 0, 1)

        highlight = self.palette().color(QtGui.QPalette.Highlight)
        painter.setBrush(QtGui.QBrush(highlight))
        painter.setPen(QtGui.QPen(highlight, 0))
        painter.drawRect(span_rect.intersected(groove_rect))

    def _draw_handles(self, painter, style, opt):
        """
        Draw both slider handles.
        """
        for value in [self._low, self._high]:
            opt.sliderPosition = value
            opt.sliderValue = value
            opt.subControls = QtWidgets.QStyle.SC_SliderHandle
            style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)

    def __pick(self, pt):
        """
        Return the x-coordinate if horizontal, else the y-coordinate.
        """
        return pt.x() if self.orientation() == Qt.Horizontal else pt.y()

    def __pixel_pos_to_range_value(self, pos):
        """
        Convert a pixel position to the slider's value.
        """
        style = QtWidgets.QApplication.style()
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
        sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)

        if self.orientation() == Qt.Horizontal:
            slider_length = sr.width()
            slider_min = gr.x()
            slider_max = gr.right() - slider_length + 1
        else:
            slider_length = sr.height()
            slider_min = gr.y()
            slider_max = gr.bottom() - slider_length + 1

        # Convert the pixel offset to a value within the slider's range.
        return style.sliderValueFromPosition(self.minimum(),
                                             self.maximum(),
                                             pos - slider_min,
                                             slider_max - slider_min,
                                             opt.upsideDown)
    
#----------------------------------
# Events
#----------------------------------
    def paintEvent(self, event):
        """
        Custom paint event to draw the slider groove, ticks, labels, span, and handles.
        """
        painter = QtGui.QPainter(self)
        style = QtWidgets.QApplication.style()

        # 1) Draw the groove.
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        opt.sliderValue = 0
        opt.sliderPosition = 0
        opt.subControls = QtWidgets.QStyle.SC_SliderGroove
        style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)
        groove_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt,
                                           QtWidgets.QStyle.SC_SliderGroove, self)

        # 2) Draw ticks and labels in logarithmic steps.
        self._draw_ticks_and_labels(painter, groove_rect, style, opt)

        # 3) Draw the highlighted span between the two handles.
        self._draw_span(painter, style, groove_rect, opt)

        # 4) Draw the slider handles.
        self._draw_handles(painter, style, opt)

    def mousePressEvent(self, event):
        """
        Handle mouse press events to determine which handle is being moved.
        """
        event.accept()
        style = QtWidgets.QApplication.style()
        button = event.button()

        if button:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            self.active_slider = -1

            # Check if a handle was clicked.
            for i, value in enumerate([self._low, self._high]):
                opt.sliderPosition = value
                hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
                if hit == style.SC_SliderHandle:
                    self.active_slider = i
                    self.pressed_control = hit
                    self.triggerAction(self.SliderMove)
                    self.setRepeatAction(self.SliderNoAction)
                    self.setSliderDown(True)
                    break

            # If no handle was hit, set a click offset for later adjustment.
            if self.active_slider < 0:
                self.pressed_control = QtWidgets.QStyle.SC_SliderHandle
                self.click_offset = self.__pixel_pos_to_range_value(self.__pick(event.pos()))
                self.triggerAction(self.SliderMove)
                self.setRepeatAction(self.SliderNoAction)
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events to update the handle positions.
        """
        if self.pressed_control != QtWidgets.QStyle.SC_SliderHandle:
            event.ignore()
            return

        event.accept()
        new_pos = self.__pixel_pos_to_range_value(self.__pick(event.pos()))

        if self.active_slider < 0:
            # Move both handles if no specific handle is active.
            offset = new_pos - self.click_offset
            self._low += offset
            self._high += offset
            # Clamp the values within slider boundaries.
            if self._low < self.minimum():
                diff = self.minimum() - self._low
                self._low += diff
                self._high += diff
            if self._high > self.maximum():
                diff = self.maximum() - self._high
                self._low += diff
                self._high += diff
        elif self.active_slider == 0:
            # Move the lower handle.
            if new_pos >= self._high:
                new_pos = self._high - 1
            self._low = new_pos
        else:
            # Move the upper handle.
            if new_pos <= self._low:
                new_pos = self._low + 1
            self._high = new_pos

        self.click_offset = new_pos
        self.update()

        # Emit signal with updated indices and corresponding float values.
        self.sliderMoved.emit(self._low, self._high,
                              self.values_list[self._low],
                              self.values_list[self._high])


# ---------------------------------------------------------------------
# Testing both classes.
# ---------------------------------------------------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = QtWidgets.QMainWindow()

    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)

    # ----- Test for ListSlider (Single Handle) -----
    single_slider = ListSlider([0, 10, 20, 30, 40, 10, 20, 30, 40, 10, 20, 30, 40, 10, 20, 30, 40, 10, 20, 30, 40, 10, 20, 30, 40, 10, 20, 30, 40, 10, 20, 30, 40, 10, 20, 30, 40, 10, 20, 30, 40])
    single_slider.setMinimumHeight(60)
    # Connect the sliderMoved signal with a lambda that accepts a single parameter.
    single_slider.sliderMoved.connect(
        lambda idx: print(f"ListSlider moved: index={idx}, value={single_slider.values_list[idx]}")
    )
    layout.addWidget(QtWidgets.QLabel("ListSlider (Single Handle)"))
    layout.addWidget(single_slider)

    # Buttons for testing ListSlider functionalities.
    btn_single_empty = QtWidgets.QPushButton("Set Single Slider Empty List")
    btn_single_empty.clicked.connect(lambda: single_slider.set_list([]))
    btn_single_multi = QtWidgets.QPushButton("Set Single Slider Multi")
    btn_single_multi.clicked.connect(lambda: single_slider.set_list([5, 15, 25, 35, 45]))
    btn_single_up = QtWidgets.QPushButton("Single Slider Up")
    btn_single_up.clicked.connect(single_slider.up)
    btn_single_down = QtWidgets.QPushButton("Single Slider Down")
    btn_single_down.clicked.connect(single_slider.down)
    btn_single_test = QtWidgets.QPushButton("Test Single Slider getListValue")
    btn_single_test.clicked.connect(lambda: print(f"Single slider value: {single_slider.get_list_value()}"))
    layout.addWidget(btn_single_empty)
    layout.addWidget(btn_single_multi)
    layout.addWidget(btn_single_up)
    layout.addWidget(btn_single_down)
    layout.addWidget(btn_single_test)

    # ----- Test for ListSliderRange (Dual Handle) -----
    range_slider = ListSliderRange([1, 5, 10, 15, 20])
    range_slider.setMinimumHeight(100)  # Extra vertical space for dual handles and ticks.
    range_slider.sliderMoved.connect(
        lambda low, high, low_val, high_val: print(
            f"RangeSlider moved: Low={low} ({low_val}), High={high} ({high_val})"
        )
    )
    layout.addWidget(QtWidgets.QLabel("ListSliderRange (Dual Handle)"))
    layout.addWidget(range_slider)

    # Buttons for testing ListSliderRange functionalities.
    btn_range_empty = QtWidgets.QPushButton("Set Range Slider Empty List")
    btn_range_empty.clicked.connect(lambda: range_slider.set_list([]))
    btn_range_single = QtWidgets.QPushButton("Set Range Slider Single Item")
    btn_range_single.clicked.connect(lambda: range_slider.set_list([10]))
    btn_range_multi = QtWidgets.QPushButton("Set Range Slider Multi")
    btn_range_multi.clicked.connect(lambda: range_slider.set_list([10, 20, 30, 40, 50]))
    btn_range_up = QtWidgets.QPushButton("Range Slider UpMin")
    btn_range_up.clicked.connect(range_slider.up_min)
    btn_range_down = QtWidgets.QPushButton("Range Slider DownMax")
    btn_range_down.clicked.connect(range_slider.down_max)
    btn_range_test = QtWidgets.QPushButton("Test Range Slider Values")
    btn_range_test.clicked.connect(
        lambda: print(f"Range slider low_value: {range_slider.low_value()}, high_value: {range_slider.high_value()}")
    )
    layout.addWidget(btn_range_empty)
    layout.addWidget(btn_range_single)
    layout.addWidget(btn_range_multi)
    layout.addWidget(btn_range_up)
    layout.addWidget(btn_range_down)
    layout.addWidget(btn_range_test)

    win.setCentralWidget(central_widget)
    win.show()
    sys.exit(app.exec_())

