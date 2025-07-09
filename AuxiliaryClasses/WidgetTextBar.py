import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QVBoxLayout,  #  ← added QVBoxLayout
    QLabel, QWidget, QTextEdit, QSlider, QLineEdit
)
from PyQt5.QtGui import QFontMetrics, QFont

# --------------------------------------------------
# Main widget
# --------------------------------------------------
class WidgetTextBar(QWidget):
    """Displays key/value pairs with coloured labels plus a comment box."""
    # --------------------------
    # Construction
    # --------------------------
    def __init__(self, keys_1=None, font = 8):
        super().__init__()

        # ---- user‑tunable font size (points) ----
        self.my_font_size = font             # Master size knob

        # ----------------------------------------
        self.default_text  = "Comment"
        self.value_labels  = {}              # key → QLabel
        self.key_colors    = {}              # key → colour string
        self._user_comment = self.default_text
        self._user_comment  = ""

        # Build UI
        keys_1 = keys_1 or []
        ordered_keys = self._sort_keys_by_suffix(keys_1)
        self._build_ui(ordered_keys)

    # --------------------------
    # Public helpers
    # --------------------------
    def get_comment(self):
        return {'comment': self._user_comment}

    def clear_text_box(self):
        self._comment_edit.clear()
        #self._comment_edit.setText(self.default_text)
        self._user_comment = ""

    # --------------------------
    # Internal helpers
    # --------------------------
    @staticmethod
    def _sort_keys_by_suffix(keys):
        """Return keys grouped by final letter (h/m/l) then alphabetic."""
        buckets = {"h": [], "m": [], "l": [], "other": []}
        for k in keys:
            buckets[k[-1] if k[-1] in buckets else "other"].append(k)
        return (
            sorted(buckets["h"], reverse=True) +
            sorted(buckets["m"], reverse=True) +
            sorted(buckets["l"], reverse=True) +
            sorted(buckets["other"], reverse=True)
        )

    @staticmethod
    def _assign_color_by_suffix(key):
        return {"h": "red", "m": "green", "l": "blue"}.get(key[-1], "black")

    # --------------------------
    # Build the interface
    # --------------------------
    def _build_ui(self, ordered_keys):
        font = QFont()
        font.setPointSize(self.my_font_size)              
        fm = QFontMetrics(font)
        line_px = fm.lineSpacing()       
        
        # ---- main horizontal layout (labels + comment box) ----
        main = QHBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ---- sub‑layout for the labels ----
        h_labels = QHBoxLayout()
        h_labels.setContentsMargins(0, 0, 0, 0)
        h_labels.setSpacing(10)

        for key in ordered_keys:
            colour       = self._assign_color_by_suffix(key)
            self.key_colors[key] = colour

            html = (
                f"<b>"
                f"<span style='font-size:{self.my_font_size}pt; color:{colour};'>{key}:</span>"
                f"</b> 0.000000"
            )

            lbl = QLabel(html)
            lbl.setAlignment(Qt.AlignLeft)
            lbl.setStyleSheet(f"font-size:{self.my_font_size}pt;")      # makes numbers match
            lbl.setFixedHeight(line_px)
            lbl.setFixedWidth(125  + len(key))

            h_labels.addWidget(lbl)
            self.value_labels[key] = lbl

        # ---- comment box ----
        self._comment_edit = QLineEdit()
        self._comment_edit.setFont(font)
        self._comment_edit.setPlaceholderText(self.default_text)
        # enforce same font size in placeholder
        self._comment_edit.setStyleSheet(f"font-size:{self.my_font_size}pt;")
        # height = line + descent to avoid clipping
        self._comment_edit.setFixedHeight(line_px + fm.descent())
        self._comment_edit.textChanged.connect(self._on_text_changed)

        # ---- assemble ----
        main.addLayout(h_labels)
        main.addWidget(self._comment_edit)

        # overall widget height also tracks font size
        self.setFixedHeight(line_px + fm.descent())

    # --------------------------
    # Runtime updates
    # --------------------------
    def _update_text(self, dictionary):
        font_pt = self.my_font_size
        for key, val in dictionary.items():
            lbl = self.value_labels.get(key)
            if lbl:
                colour = self.key_colors[key]
                lbl.setText(
                    f"<b><span style='font-size:{font_pt}pt; color:{colour};'>{key}:</span></b> "
                    f"{val:.3g}"
                )

    def _on_text_changed(self):
        self._user_comment = self._comment_edit.text()


#########################
# Manual Testing
#########################
if __name__ == "__main__":
    from PyQt5.QtWidgets import QMainWindow
    app = QApplication(sys.argv)

    # Example dictionaries.
    dic_1 = {"pQh": 2.0067, "pRh": 2.0067, "pQm": 0.00008, "pQl": 20.450004, "pS": 999.0}
    dic_2 = {"unknown": 0.0067}
    dic_3 = dic_1 | dic_2

    # Create a main window.
    window = QMainWindow()

    # Create the WidgetTextBar using keys from both dictionaries.
    text_bar = WidgetTextBar(dic_1.keys() | dic_2.keys())
    text_bar._update_text(dic_3)

    # Create a central widget and layout.
    central_widget = QWidget()
    central_layout = QVBoxLayout()
    central_layout.addWidget(text_bar)

    # For each key, create a label and corresponding horizontal slider.
    sliders = {}
    for key, value in dic_3.items():
        lbl = QLabel(key)
        central_layout.addWidget(lbl)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(-1000000)
        slider.setMaximum(1000000)
        slider.setValue(int(value * 10))
        slider.valueChanged.connect(
            lambda val, k=key: (
                dic_3.update({k: val / 100.0}),
                text_bar._update_text(dic_3)
            )
        )
        sliders[key] = slider
        central_layout.addWidget(slider)

    central_widget.setLayout(central_layout)
    window.setCentralWidget(central_widget)
    window.setWindowTitle("Testing WidgetTextBar with Sliders")
    window.show()

    sys.exit(app.exec_())
