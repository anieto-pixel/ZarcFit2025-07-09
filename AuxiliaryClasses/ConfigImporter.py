import os
from configupdater import ConfigUpdater
from typing import Optional

# Import slider classes. Replace with the actual module if needed.
from .CustomSliders import EPowerSliderWithTicks, DoubleSliderWithTicks


class ConfigImporter:
    """
    Class to import and manage configuration settings.
    Reads a configuration file to extract paths, slider settings,
    and various widget parameters.
    """

    def __init__(self, config_file: str):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")

        self.config_file = config_file
        self.config = ConfigUpdater()
        self.config.optionxform = str  # Maintain case sensitivity for keys
        self.config.read(config_file)

        # File paths for input and output.
        self.input_file: Optional[str] = None
        self.input_file_type: Optional[str] = None
        self.output_file: Optional[str] = None

        # Slider configurations and default values.
        self.slider_configurations = {}
        self.slider_default_values = []
        self.slider_default_disabled = []

        # Secondary variables to display.
        self.secondary_variables_to_display = []
        self.variables_to_print = []
        
        # Display Preferences
        self.general_font: Optional[int] = None
        self.small_font: Optional[int] = None

        # Read and process the configuration file.
        self._read_config_file()
        self._check_sliders_length()

    def set_input_file(self, new_input_file: str) -> None:
        if self._validate_path(new_input_file):
            self._update_config("InputFile", "path", new_input_file)
            self.input_file = new_input_file
            
    def set_input_file_type(self, new_input_file_type: str) -> None:
        self._update_config("InputFileType", "type", new_input_file_type)
        self.input_file_type = new_input_file_type

    def set_output_file(self, new_output_file: str) -> None:
        if self._validate_path(new_output_file):
            self._update_config("OutputFile", "path", new_output_file)
            self.output_file = new_output_file

    def _update_config(self, section: str, key: str, value: str) -> None:
        if section not in self.config:
            self.config.add_section(section)
        if key not in self.config[section]:
            self.config[section].add_option(key, value)
        else:
            self.config[section][key].value = value
        self.config.update_file(self.config_file)  # preserves comments!

    def _read_config_file(self) -> None:
        # Reload config to ensure updates are included.
        self.config = ConfigUpdater()
        self.config.optionxform = str
        self.config.read(self.config_file)

        self._extract_mandatory_parameters()
        self._extract_optional_parameters()

    def _extract_mandatory_parameters(self) -> None:
        required_sections = [
            "SliderConfigurations",
            "SliderDefaultValues",
            "VariablesToPrint",
            "SecondaryVariablesToDisplay",
        ]
        for section in required_sections:
            if section not in self.config:
                raise ValueError(
                    f"ConfigImporter._extract_mandatory_parameters: Missing '{section}' section in the config file."
                )

        self._extract_sliders_configurations()

        # Note: must use .value with configupdater for Option objects
        defaults_str = self.config["SliderDefaultValues"]["defaults"].value
        self.slider_default_values = [float(val.strip()) for val in defaults_str.split(",")]

        vars_str = self.config["VariablesToPrint"]["variables"].value
        self.variables_to_print = [v.strip() for v in vars_str.split(",") if v.strip()]

        secondary_str = self.config["SecondaryVariablesToDisplay"]["variables"].value
        self.secondary_variables_to_display = [v.strip() for v in secondary_str.split(",") if v.strip()]

    def _extract_sliders_configurations(self) -> None:
        sliders = {}
        for key, option in self.config["SliderConfigurations"].items():
            value = option.value if hasattr(option, "value") else option
            parts = value.split(",")
            if len(parts) != 5:
                raise ValueError(
                    f"Invalid slider configuration for '{key}'. Expected 5 comma-separated values."
                )
            slider_type_str, min_val_str, max_val_str, color, tick_interval_str = [p.strip() for p in parts]
            slider_class = self._safe_import(slider_type_str)
            if slider_class is None:
                raise ValueError(
                    f"ConfigImporter._extract_sliders_configurations: Unrecognized slider type '{slider_type_str}' for slider '{key}'."
                )
            sliders[key.strip()] = (
                slider_class,
                float(min_val_str),
                float(max_val_str),
                color,
                int(tick_interval_str),
            )
        self.slider_configurations = sliders

    def _extract_optional_parameters(self) -> None:
        if 'InputFile' in self.config:
            path = self.config['InputFile'].get('path')
            path = path.value if hasattr(path, "value") else path
            if path and self._validate_path(path):
                self.input_file = path
                
        if 'InputFileType' in self.config:
            my_type = self.config['InputFileType'].get('type')
            my_type = my_type.value if hasattr(my_type, "value") else my_type
            if my_type:
                self.input_file_type = my_type

        if 'OutputFile' in self.config:
            path = self.config['OutputFile'].get('path')
            path = path.value if hasattr(path, "value") else path
            if path and self._validate_path(path):
                self.output_file = path
                
        if 'SliderDisabled' in self.config:
            defaults_str = self.config["SliderDisabled"]["defaults"].value
            self.slider_default_disabled = [val.strip().lower() == "true" for val in defaults_str.split(",")]
            
        if 'GeneralFont' in self.config:
            font = self.config['GeneralFont'].get('font')
            small_font = self.config['GeneralFont'].get('small_font')
            self.general_font = int(font.value if hasattr(font, "value") else font)
            self.small_font = int(small_font.value if hasattr(small_font, "value") else small_font)

    @staticmethod
    def _safe_import(class_name: str):
        slider_classes = {
            "EPowerSliderWithTicks": EPowerSliderWithTicks,
            "DoubleSliderWithTicks": DoubleSliderWithTicks,
        }
        return slider_classes.get(class_name)

    def _validate_path(self, path: str) -> bool:
        try:
            if not isinstance(path, str):
                raise TypeError("Path must be a string.")
            directory = os.path.dirname(path) or '.'
            if not os.path.isdir(directory):
                raise ValueError("ConfigImporter._validate_path: Invalid file path. The directory does not exist.")
            return True
        except (TypeError, ValueError) as e:
            print(f"Path validation error: {e}")
            return False

    def _check_sliders_length(self):
        len1 = len(self.slider_configurations)
        len2 = len(self.slider_default_values)
        len3 = len(self.slider_default_disabled)
        condition1 = len1 == len2
        condition2 = (len1 == len3) or (len3 == 0)
        if not (condition1 and condition2):
            raise ValueError(
                f"ConfigImporter._check_sliders_length: Mismatch detected"
            )
            
    
#####################################
# Testing
#########################################

if __name__ == '__main__':
    #config_file = "config.ini"
    config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
    my_importer = ConfigImporter(config_file)
