import sys
import weakref
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QMessageBox, QGraphicsColorizeEffect
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QFont, QFontMetrics


class DualLabelButton(QPushButton):
    """
    A QPushButton subclass that provides two distinct labels for its off and on states.
    """
    def __init__(self, off_label: str, on_label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(off_label, parent)
        self.off_label = off_label
        self.on_label = on_label
        self.setCheckable(True)

class WidgetButtonsRow(QWidget):
    """
    A widget that provides a vertical layout of multiple buttons for quick actions.
    The widget is designed to have a minimum height about 1/3 of the screen,
    """
    def __init__(self, font = 10) -> None:
        super().__init__()
        self.font = font # Base font size at 100%

        # Create regular (non-checkable) buttons.
        self.f1_button: QPushButton = QPushButton("F1. Fit Cole")
        self.f2_button: QPushButton = QPushButton("F2 Fit Bode")
        self.f3_button: QPushButton = QPushButton("F3 AllFreqs")
        self.f4_button: QPushButton = QPushButton("F4 Save plot")
        self.f5_button: QPushButton = QPushButton("F5 File Back")
        self.f6_button: QPushButton = QPushButton("F6 File Forth")
        self.f7_button: QPushButton = QPushButton("F7 Recover")
        self.f8_button: QPushButton = QPushButton("F8 Sliders Default")

        # Create checkable buttons using DualLabelButton.
        self.f9_button: DualLabelButton = DualLabelButton("F9 +Rinf", "F9 -Rinf")
        self.f10_button: DualLabelButton = DualLabelButton("F10 Tail Right", "F11 Tail Left")
        self.f11_button: DualLabelButton = DualLabelButton("F11 Damping", "F12 Constrains On")

        # Create additional regular buttons.
        self.f12_button: DualLabelButton = QPushButton("F12 Print Headers")
        self.fup_button: QPushButton = QPushButton("PUp. Min Freq")
        self.fdown_button: QPushButton = QPushButton("PDown. Max freq")
        self.ctrlz_button: QPushButton = QPushButton("Ctrl+Z Undo Fit")

        # Group all buttons into a list for easy iteration.
        self._buttons_list = [
            self.f1_button, self.f2_button, self.f3_button,
            self.f4_button, self.f5_button, self.f6_button,
            self.f7_button, self.f8_button, self.f9_button,
            self.f10_button, self.f11_button, self.f12_button,
            self.fup_button, self.fdown_button, self.ctrlz_button
        ]

        self._setup_layout()
        self._setup_connections()

    def _setup_layout(self) -> None:
        """
        Set up the vertical layout for all buttons without spacing,
        and adjust button size using DPI-aware scaling.
        """
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

#       button_height = 30
        font = QFont()
        font.setPointSizeF(self.font)                # base point size
        metrics = QFontMetrics(font)
        button_height = metrics.height()  + 15

        for button in self._buttons_list:
            # build and cache the DPI‑aware base style
            button.setFont(font)
            base_style = (
                f"font-size: {self.font}pt;"
                " margin: 0; padding: 8px; text-align: left;"
                )
            button.setStyleSheet(base_style)
            button._base_style = base_style
            button.setFixedHeight(button_height)
            layout.addWidget(button)

        self.setLayout(layout)
        self.setMaximumWidth(200)

        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            screen_height = screen.availableGeometry().height()
            min_height = screen_height // 5 #3
        else:
            min_height = button_height * len(self._buttons_list)
        self.setMinimumSize(30, min_height)

    def _setup_connections(self) -> None:
        """
        Connect each button's signal to its appropriate slot.
        """
        for btn in self._buttons_list:
            if not btn.isCheckable():
                btn.clicked.connect(self._on_regular_button_clicked)
            else:
                btn.toggled.connect(self._on_checkable_toggled)

    def _on_regular_button_clicked(self) -> None:
        """
        Handle clicks for non-checkable buttons: flash green if successful or show an error.
        """
        button = self.sender()
        if not isinstance(button, QPushButton):
            return

        order_is_correct = True  # Replace with actual operation logic

        if order_is_correct:
            self._flash_button_green(button, duration=1500)
        else:
            QMessageBox.warning(self, "Error", "Order not correctly executed!")

    def _on_checkable_toggled(self, state: bool) -> None:
        """
        Handle toggling of checkable buttons: update text and style
        """
        button = self.sender()
        if not isinstance(button, QPushButton):
            return

        if state:
            button.setText(button.on_label)  # type: ignore[attr-defined]
            new_style = f"{button._base_style} background-color: orange;"
        else:
            button.setText(button.off_label)  # type: ignore[attr-defined]
            new_style = f"{button._base_style} background-color: none;"

        button.setStyleSheet(new_style)

    def _flash_button_green(self, button: QPushButton, duration: int = 1500) -> None:
        """
        Briefly flash the button green for the specified duration.
        """
        effect = QGraphicsColorizeEffect()
        effect.setColor(QColor(0, 150, 0, 255))
        effect.setStrength(1.0)
        button.setGraphicsEffect(effect)

        weak_button = weakref.ref(button)
        QTimer.singleShot(
            duration, lambda: weak_button() and weak_button().setGraphicsEffect(None)
        )

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    widget = WidgetButtonsRow()
    widget.setWindowTitle("Test WidgetButtonsRow")
    widget.show()
    sys.exit(app.exec_())
