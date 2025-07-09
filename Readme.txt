__**ZarcFit: Impedance Analysis of Rock Samples**__


ZarcFit is a graphical Python application for analyzing impedance data from rock samples, developed as a modern reimplementation of Dr. Enkin's original 2014 LabView-based program. The tool is designed to assist geophysicists and materials researchers in modeling experimental impedance spectra using predefined electrical circuit analogs.
----------------------------------------------------------------------------------------------------------------------------------------------

**Features**


*Circuit Modeling*: Implements two equivalent circuit models to simulate frequency-dependent impedance of geological materials.

*Interactive Visualization*:
	- Plots experimental data (green) vs. modeled curves (blue).
  	- Time-domain transformation is also shown.

*Real-Time Parameter Control*:
  	- Sliders (with color-coded mapping) allow tuning model parameters interactively.
  	- Supports parameter bounds, enabling/disabling sliders, and value reset.
	- Curve fitting of impedance spectrum with respect to the model parameters.

*Configurable Input/Output*:
  	- Uses config.ini to load default parameter ranges, values, and output variable preferences.
  	- Automatically logs results to a CSV file.

*Keyboard Shortcuts*: F1–F12 keys perform fitting, navigation, toggling options, and more. Space bar prints the heading
----------------------------------------------------------------------------------------------------------------------------------------------

**Project Structure**

ZarcFit/
│
├── AuxiliaryClasses/              # Modular components used in Main.py
│   ├── Calculator.py              # Core fitting logic & model simulation
│   ├── ConfigImporter.py          # Loads config.ini
│   ├── CustomListSliders.py       # List-based sliders for frequency selection
│   ├── CustomSliders.py           # Custom sliders with color and control extensions
│   ├── FitBuilder.py              # Fitting logic using optimization routines
│   ├── ModelCircuit.py            # Classes to represent impedance circuit elements
│   ├── TimeDomainBuilder.py       # Transforms frequency domain data to time domain
│   ├── WidgetButtonsRow.py        # Button grid for user interaction
│   ├── WidgetGraphs.py            # Graphical displays (Nyquist, Bode, time plots)
│   ├── WidgetInputFile.py         # Input file loading
│   ├── WidgetOutputFile.py        # Output file management
│   ├── WidgetTextBar.py           # Displays calculated secondary variables
│   └── WidgetSliders.py           # Manages parameter sliders
│
├── Main.py                        # Main executable GUI script
├── config.ini                     # Settings for file paths, sliders, and output
├── .gitignore                     # Git tracking exclusions
└── README.md                      # This documentation
----------------------------------------------------------------------------------------------------------------------------------------------

**Circuit Models**

Two theoretical impedance models are embedded, based on Dr. Enkin’s specifications. These consist of combinations of resistors, capacitors, and constant phase elements, each representing specific geological or electrode behaviors. The program allows to easily code more du classes to the circuit model class, if desired.

- The different Models are coded in ModelCircuit.py.
- Circuit structure is visualized separately (see circuit_models.jpg).
----------------------------------------------------------------------------------------------------------------------------------------------

**Parameters and Sliders**

Sliders are divided by frequency range:

Color | Frequency Component  | Example Variables
------|----------------------|------------------
Red   | High-frequency       | Rh, Fh, Ph
Green | Mid-frequency        | Rm, Fm, Pm
Blue  | Low-frequency        | Rl, Fl, Pl
Black | External effects     | Rinf, Linf, Re, Qe, Pef, Pei

Slider types include:
- EPowerSliderWithTicks: Exponential sliders (e.g., for log-scale resistance values).
- DoubleSliderWithTicks: Linear sliders for phase values or coefficients.

Default ranges, initial values, and disabled states are configured in config.ini.
Inverse sign: The Rinf slider offers the possibility of turning it's value negative in the internal operations of the program. When this option is active and the sign of the slider's value is being reversed, an orange frame is displayed around the slider.
----------------------------------------------------------------------------------------------------------------------------------------------

**Configuration (config.ini)**

Key sections: 
(If left blank, the program will not work correctly)
- [SliderConfigurations]: Parameter names, slider type, min/max range, color, and tick spacing
- [SliderDefaultValues]: Initial values for each parameter
- [SliderDisabled]: Specifies which sliders are initially disabled
- [VariablesToPrint]: Controls which values are recorded in output CSV
- [SecondaryVariablesToDisplay]: Parameters shown in the bottom status bar

Other Sections: 
(If left blank, the program will still work correctly)
- [InputFile] and [InputFileType]: Optional, saves the path to the last used input file, and it's type
- [OutputFile]: Optional, saves the path to the last used output file
- [GeneralFont]: Optional, defines the font sizes of widgets
----------------------------------------------------------------------------------------------------------------------------------------------

**Running the Program**

*Requirements*
- Python 3.8+
- PyQt5
- NumPy

*Launch*
python Main.py

The main window includes:
- Top bar: File input/output selection
- Middle pane: Graphs and frequency range selection
- Bottom pane: Sliders, buttons, and secondary variable display
----------------------------------------------------------------------------------------------------------------------------------------------

**Hotkeys Summary**

Key       | Action
--------- |-----------------------------------------
F1        | Fit using Cole cartesian coordinates
F2        | Fit using Bode polar coordinates
F3        | Use all frequencies in the data fit
F4        | Export current parameters to the output .csv file
F5/F6     | Navigate to previous/next input file
F7        | Recover parameters for the current sample from .cvs file. Default parameters if sample not found
F8        | Reset parameters to default
F9        | Toggle negative Rinf for samples with top frequency imaginary impedance
F10       | Toggle Pei (external impedance phase)
F11       | Fit Damping
F12       | Print variable list to the output file
PgUp/Down | Adjust frequency range ends
Ctrl+Z    | Undo last automatic fit. Resets parameters to the initial guess
----------------------------------------------------------------------------------------------------------------------------------------------

**General Notes**

- Results and session metadata (date/time, file name) are automatically added to the output.
- Model switching is performed at runtime with zero-code modification.
- Program designed and developed by Alicia Nieto, supervised by Dr. Enkin, with the library recommendations of Joshua Goodeve.
- Program actively maintained. For any issues, send email to aliciagnieto@gmail.com with subject "ZarcFit Maintenance".
----------------------------------------------------------------------------------------------------------------------------------------------

**Maintenance Notes**

*- Disabled sliders*:
QSliders has a method that allows the disabling of sliders. However, sliders disabled in such a way cannot be readjusted while remaining disabled. Dr Enkin desired the option of manually adjusting the sliders that appeared as disabled, while keeping their values from being included among the values to be optimized by the fit. For this reason the "disable" button of the sliders does not truly disable them in the QSlider sense. Instead:
 - When the "Disable" button on a slider in the WidgetSliders panel is clicked, the application toggles an internal flag and triggers a custom signal — slider_was_disabled — emmited by the slider.
 - This signal is captured by a "listener" in the WidgetSliders, which re-emits it. This new signal includes a dictionary mapping parameter names to their enabled/disabled status. 
 -The New signal is connected to a listener in the MainWidget class, which passes the updated status dictionary to the Calculator via the set_disabled_variables() method. 
 - Once the Calculator receives this dictionary, it stores the disabled state of each parameter. During fitting operations—executed through functions such as fit_model_cole() or fit_model_bode()—the calculator checks this dictionary and excludes any disabled parameters from optimization, effectively freezing their values. As a result, although disabled sliders remain visually and interactively active, their values do not influence the model fitting, ensuring users can selectively fix certain parameters without altering the rest of the fit.

*- Negative Rinf*:
When the program was originally designed, it was determined that the value displayed by the label under the CustomSlider must display the value emitted by the signal of the slider, for ease of debugging. However, sending a negative value for Rinf required changes in Rinf outward appearance that the users found undesirable, as well as problems during some basic fit calculations. For this reason some non intuitive workarounds have been included in order to allow the models and fits to use a negative Rinf while keeping the slider value positive:
 - When the F9 key is pressed, it programmatically toggles the f9_button located in the WidgetButtonsRow component. 
 - This button is connected to a signal in MainWidget, which invokes the _handle_rinf_negative(state) method with the new toggle state (True or False).
 - Inside this method, the application:
	- First calls set_rinf_negative(state) on the Calculator. passing the current toggle state (True if negative Rinf is enabled, False otherwise). This method stores the state in an internal flag inside the Calculator class—typically as self.rinf_is_negative or similar.
	- Then, the method retrieves the Rinf slider from WidgetSliders and calls toggle_orange_effect(state), a visual cue function that likely highlights the slider when in the negative state. 
	- After updating the state, run_model_manual(self.v_sliders) is called to recompute the impedance model using the updated sign convention for Rinf. 
 - Later, when Calculator.run_model_manual(self.v_sliders) is invoked (either immediately after toggling or during manual model evaluation), the calculator retrieves the current value of Rinf from the passed slider dictionary. At that point, it checks the internal flag set earlier: if the rinf_is_negative flag is True, the value of Rinf is multiplied by -1 before it is inserted into the model equations.
This way, even though the UI slider always holds a positive value (for logarithmic range control), the actual model receives and processes Rinf as negative when the toggle is active. This logic ensures that model behavior can reflect both physical cases without requiring changes to the slider itself.

*- Negative Rinf and f7*:
When the F7 key is pressed, it activates the f7_button in WidgetButtonsRow, which is connected to the _handle_recover_file_values() method in MainWidget. This function retrieves the current input file’s name and searches the output CSV file (managed by WidgetOutputFile) for a matching row using find_row_in_file(). Once a matching row is found, the application loads all parameter values, including Rinf, into the v_sliders dictionary. At this point, the sign of Rinf is checked explicitly. Depending on the result the necessary steps for "negative Rinf" are taken, toggling the right button and setting the right flags

*- Fit Optimization*:
Calculator:
The method first filters the v_sliders dictionary to exclude any parameters marked as disabled using the disabled_dict (previously set via set_disabled_variables()).

Then it defines:
An initial guess vector (from the enabled slider values)
Lower/upper bounds (from the config)
A cost function (depending on Cole or Bode fitting)
Calls FitBuilder

FitBuilder
The actual optimization task is delegated to FitBuilder, which runs an optimization algorithm (scipy.optimize.least_squares, methof 'trust region reflective').
The cost function compares the model-generated impedance (real & imaginary) against the experimental data over a defined frequency range.
The algorithm adjusts parameters iteratively to minimize the difference.
Once optimization completes, FitBuilder emits model_manual_values with the best-fit parameters.

This signal is connected to WidgetSliders.set_all_variables, which updates the sliders accordingly.
The new values are stored in MainWidget.v_sliders, and a call to Calculator.run_model_manual updates the graphs.
Secondary variables are recalculated and displayed via WidgetTextBar.


*- Unbounded Pei*:
To allow Pei to be unbounded during the fit, while still allowing for a dynamic creation of bounds from the config file: Pei is handled as a special case within FitBuilder.set_bounds().
After all the bounds defined in the config file are applied, the bounds of Pei are removed.
To ensure that Pei returns a desired angle within the bounds, despite not being bound during the fit: After the ersults from the fit are obtained, they are modified to "wrap" the value of Pei. This is accomplished by adding the line best_fit['Pei'] = (best_fit['Pei']+1)%4. - 1 to FitBuilder.Fit()

