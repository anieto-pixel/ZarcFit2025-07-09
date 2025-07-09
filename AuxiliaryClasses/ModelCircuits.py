# -*- coding: utf-8 -*-
"""
Created on Wed Mar  5 11:59:26 2025

@author: agarcian
"""
import numpy as np


###############################################################################
# Circuit Models
###############################################################################
class ModelCircuitParent(object):
    """
    Parent class for circuit models.
    """
    def __init__(self, negative_rinf=False, q=None, par_second=None, par_other_sec=None):
        super().__init__()
        # Avoid mutable default arguments; properly assign attributes.
        if q is None:
            q = {}
        if par_second is None:
            par_second = {}
        if par_other_sec is None:
            par_other_sec = {}
        # Attributes
        self.name=""
        
        self.negative_rinf = negative_rinf
        self.q = q
        self.par_second = par_second #secondary variables used in the calculations
        self.par_other_sec=par_other_sec   #other secondary variables not used in calculations

    # ------------------------------------------
    # Public Methods
    # ------------------------------------------
    def init_parameters(self):
        """Return the current state of the model's attributes."""
        return self.negative_rinf, self.q, self.par_second, self.par_other_sec

    def run_model(self, parameters: dict, freq_array: np.ndarray, old_par_second=False):
        """
        Model of an electric circuit that uses the received values v as variables
        and returns the impedance array of the circuit.
        """
        return np.array([])

    def run_rock(self, parameters: dict, freq_array: np.ndarray, old_par_second=False):
        """Placeholder method for a variant of the rock's circuit model."""
        return np.array([])
    
    def estimate_rock(self, parameters: dict, freq_array: np.ndarray, impedance: np.ndarray):
        """Estimates the rock impedance from experimental data."""
        par = parameters
        z_to_substract= []
        
        for f in freq_array:
            z_cpee = self._cpe(f, par["Qe"], par["Pef"], par["Pei"])
            zarce = self._parallel(z_cpee, par["Re"])
            
            z_cpeh = self._cpe(f, self.q["Qh"], par["Ph"], par["Ph"])
            zarch = self._parallel(z_cpeh, par["Rh"])
    
            z_to_substract.append( zarch + zarce - par["Rh"])
    
        z_to_substract = np.array(z_to_substract)
        
        # Ensure correct shape for subtraction
        if z_to_substract.shape != impedance.shape:
            raise ValueError(f"Shape mismatch: impedance has shape {impedance.shape}, but z_to_subtract has shape {z_to_substract.shape}")
    
        z_estimated_rock = impedance - z_to_substract
    
        return z_estimated_rock
    
    # ------------------------------------------
    # Private Methods
    # ------------------------------------------
    def _calculate_secondary_parameters(self, par):
        """
        Compute 'series' and 'parallel' secondary variables.

        Returns a dict of newly calculated secondary variables.
        """
        Qh = self._q_from_f0(par["Rh"], par["Fh"], par["Ph"])
        Qm = self._q_from_f0(par["Rm"], par["Fm"], par["Pm"])
        Ql = self._q_from_f0(par["Rl"], par["Fl"], par["Pl"])

        self.q["Qh"] = Qh
        self.q["Qm"] = Qm
        self.q["Ql"] = Ql

        self.par_second["R0"] = par["Rinf"] + par["Rh"] + par["Rm"] + par["Rl"]
        self.par_second["pRh"] = par["Rinf"] * (par["Rinf"] + par["Rh"]) / par["Rh"]
        self.par_second["pQh"] = Qh * (par["Rh"] / (par["Rinf"] + par["Rh"])) ** 2
        self.par_second["pRm"] = (par["Rinf"] + par["Rh"]) * (par["Rinf"] + par["Rh"] + par["Rm"]) / par["Rm"]
        self.par_second["pQm"] = Qm * (par["Rm"] / (par["Rinf"] + par["Rh"] + par["Rm"])) ** 2
        self.par_second["pRl"] = (par["Rinf"] + par["Rh"] + par["Rm"]) * (par["Rinf"] + par["Rh"] + par["Rm"] + par["Rl"]) / par["Rl"]
        self.par_second["pQl"] = Ql * (par["Rl"] / (par["Rinf"] + par["Rh"] + par["Rm"] + par["Rl"])) ** 2
        
        self.par_other_sec["Ch"]= 1/(2*np.pi*par["Fh"]*par["Rh"] )
        #self.par_other_sec["pCh"]=1/(2*np.pi*par["Fh"]*self.par_second["pRh"] )
        self.par_other_sec["pCh"]= self.par_other_sec["Ch"]*(par["Rh"]/(par["Rinf"] + par["Rh"]))**2
        self.par_other_sec["Cm"]= 1/(2*np.pi*par["Fm"]*par["Rm"] )
        #self.par_other_sec["pCm"]=1/(2*np.pi*par["Fm"]*self.par_second["pRm"] )
        self.par_other_sec["pCm"]= self.par_other_sec["Cm"]*(par["Rm"]/(par["Rinf"] + par["Rh"] + par["Rm"]))**2
        self.par_other_sec["Cl"]=1/(2*np.pi*par["Fl"]*par["Rl"] )
        #self.par_other_sec["pCl"] =1/(2*np.pi*par["Fl"]*self.par_second["pRl"] )
        self.par_other_sec["pCl"] = self.par_other_sec["Cl"]*(par["Rl"]/(par["Rinf"] + par["Rh"] + par["Rm"] + par["Rl"]))**2
             
    def _inductor(self, freq, linf):
        """
        Return the impedance of an inductor at a given frequency and inductance.
        """
        if linf == 0:
            raise ValueError("Inductance (linf) cannot be zero.")
        if freq < 0:
            raise ValueError("Frequency cannot be negative.")
        result = (2 * np.pi * freq) * linf * 1j
        return result

    def _q_from_f0(self, r, f0, p):
        """
        Return the Q of a CPE given the f0.
        """
        if r == 0:
            raise ValueError("Resistance r cannot be zero.")
        if f0 <= 0:
            raise ValueError("Resonant frequency f0 must be positive.")
        result = 1.0 / (r * ((2.0 * np.pi * f0) ** p))
        
        return result

    def _cpe(self, freq, q, pf, pi):
        """
        Return the impedance of a CPE for a given frequency.
        """

        if q == 0:
            raise ValueError("Parameter q cannot be zero.")
        if freq < 0:
            raise ValueError("Frequency must be non-negative for CPE model.")
        if freq == 0 and pf > 0:
            raise ValueError("freq=0 and pf>0 results in division by zero in CPE.")
        if freq == 0 and pf < 0:
            raise ValueError("freq=0 and pf<0 is undefined (0 to a negative power).")

        phase_factor = (1j) ** pi
        omega_exp = (2.0 * np.pi * freq) ** pf
        result = 1.0 / (q * phase_factor * omega_exp)
    
        return result

    def _parallel(self, z_1, z_2):
        """
        Return the impedance of two components in parallel.
        """
        if z_1 == 0 or z_2 == 0:
            raise ValueError("Cannot take parallel of impedance 0 (=> infinite admittance).")
        
        denominator = (1.0 / z_1) + (1.0 / z_2)
        result = 1.0 / denominator
  
        return result
    
    def _parallel_arrays(self, z_1, z_2):
        """ Return the impedance of two components in parallel."""

        if np.any(z_1 == 0 ) or  np.any(z_2 == 0):
            raise ValueError("Cannot take parallel of impedance 0 (=> infinite admittance).")
        
        denominator = (1.0 / z_1) + (1.0 / z_2)
        result = 1.0 / denominator
        return result


class ModelCircuitSeries(ModelCircuitParent):
    """
    Circuit model where elements are in series.
    """
    
    def __init__(self, negative_rinf=False, q=None, par_second=None, par_other_sec=None):
        super().__init__(negative_rinf, q, par_second, par_other_sec)
        self.name = "Series Circuit"

    def run_rock(self, parameters: dict, freq_array: np.ndarray, old_par_second=False):
        par = parameters.copy()

        if self.negative_rinf:
            par['Rinf'] = -par['Rinf']
        if not old_par_second:
            self._calculate_secondary_parameters(par)

        z = []

        for freq in freq_array:
            z_cpem = self._cpe(freq, self.q["Qm"], par["Pm"], par["Pm"])
            zarcm = self._parallel(z_cpem, par["Rm"])
            z_cpel = self._cpe(freq, self.q["Ql"], par["Pl"], par["Pl"])
            zarcl = self._parallel(z_cpel, par["Rl"])

            z_total = zarcm + zarcl
            z.append(z_total)

        return np.array(z)

    def run_model(self, parameters: dict, freq_array: np.ndarray, old_par_second=False):
        
        par = parameters.copy()
        if self.negative_rinf:
            par['Rinf'] = -par['Rinf']
        if not old_par_second:
            self._calculate_secondary_parameters(par)
            
        z_rock = self.run_rock(par, freq_array, old_par_second=True)

        zinf = [self._inductor(freq, par["Linf"]) + par["Rinf"] for freq in freq_array]
        z_cpeh =[ self._cpe(freq, self.q["Qh"], par["Ph"], par["Ph"]) for freq in freq_array]
        zarch = [self._parallel(z_cpeh[i], par["Rh"]) for i in range(len(freq_array))]
        
        z_cpee = [self._cpe(freq, par["Qe"], par["Pef"], par["Pei"]) for freq in freq_array]
        zarce = [self._parallel(z_cpee[i], par["Re"]) for i in range(len(freq_array))]

        return np.array([zinf[i] + zarch[i] + z_rock[i] + zarce[i] for i in range(len(freq_array))]), np.array(z_rock)
    

class ModelCircuitParallel(ModelCircuitParent):
    """
    Circuit model where elements are in parallel.
    """
    def __init__(self, negative_rinf=False, q=None, par_second=None, par_other_sec=None):
        super().__init__(negative_rinf, q, par_second, par_other_sec)
        self.name = "Parallel Circuit"

    def run_rock(self, parameters: dict, freq_array: np.ndarray, old_par_second=False):
        
        par = parameters.copy()
        
        if self.negative_rinf:
            par['Rinf'] = -par['Rinf']
        if not old_par_second:
            self._calculate_secondary_parameters(par)

        par2 = self.par_second

        z = []

        for f in freq_array:
            z_line_m = par2["pRm"] + self._cpe(f, par2["pQm"], par["Pm"], par["Pm"])
            z_line_l = par2["pRl"] + self._cpe(f, par2["pQl"], par["Pl"], par["Pl"])

            z_lines = self._parallel(z_line_m, z_line_l)
            z_rock = self._parallel(z_lines, par2["R0"])
            #zparallel = self._parallel(z_line_h, z_rock)

            z.append(z_rock)

        return np.array(z)

    def run_model(self, parameters: dict, freq_array: np.ndarray, old_par_second=False):
        
        par = parameters.copy()
        par2 = self.par_second
        
        if self.negative_rinf:
            par['Rinf'] = -par['Rinf']
        if not old_par_second:
            self._calculate_secondary_parameters(par)
        
        z_rock = self.run_rock(par, freq_array, old_par_second=True)
        z_line_h = np.array([par2["pRh"] + self._cpe(f, par2["pQh"], par["Ph"], par["Ph"]) for f in freq_array])
        z_rock_line_h = self._parallel_arrays(z_line_h, z_rock)

        zinf = [self._inductor(f, par["Linf"]) for f in freq_array]
        z_cpee = [self._cpe(f, par["Qe"], par["Pef"], par["Pei"]) for f in freq_array]
        zarce = [self._parallel(z_cpee[i], par["Re"]) for i in range(len(freq_array))]
        
        z_circuit= np.array([zinf[i] + z_rock_line_h[i] + zarce[i] for i in range(len(freq_array))])


        return z_circuit, np.array(z_rock)


###############################################################################
#   Test    
###############################################################################
def manual_test_circuit_models():
    """
    Manually test the ModelCircuitParent subclasses (Series and Parallel)
    by providing sample parameters and frequency arrays.
    
    This function prints:
      - The total impedance and rock impedance from run_model
      - The estimated rock impedance (using a dummy experimental impedance)
    """
    # Sample parameters dictionary.
    # These values are chosen to be physically plausible for testing.
    parameters = {
        "Rinf": 10.0,
        "Rh": 20.0,
        "Rm": 30.0,
        "Rl": 40.0,
        "Linf": 0.001,   # Inductance in Henrys
        "Re": 50.0,
        "Ph": 0.8,       # Exponent for Q calculation
        "Pm": 0.6,
        "Pl": 0.4,
        "Fh": 100.0,     # Resonant frequency in Hz for "H" arc
        "Fm": 10.0,      # For "M" arc
        "Fl": 1.0,       # For "L" arc
        "Pef": 0.7,
        "Pei": 0.5,
        "Qe": 0.9       # Q for the E arc
    }

    # Create a frequency array (e.g., 10 frequencies between 1 Hz and 1000 Hz)
    freq_array = np.linspace(1, 1000, 10)

    print("---- Testing ModelCircuitSeries ----")
    try:
        # Instantiate a series model
        series_model = ModelCircuitSeries()
        
        # Call run_model: returns (total impedance, rock impedance)
        z_total_series, z_rock_series = series_model.run_model(parameters, freq_array)
        print("Series model run_model total impedance:")
        print(z_total_series)
        print("Series model run_model rock impedance:")
        print(z_rock_series)
    except Exception as e:
        print("Error in ModelCircuitSeries.run_model:", e)

    print("\n---- Testing ModelCircuitParallel ----")
    try:
        # Instantiate a parallel model
        parallel_model = ModelCircuitParallel()
        
        # Call run_model for the parallel circuit
        z_total_parallel, z_rock_parallel = parallel_model.run_model(parameters, freq_array)
        print("Parallel model run_model total impedance:")
        print(z_total_parallel)
        print("Parallel model run_model rock impedance:")
        print(z_rock_parallel)
    except Exception as e:
        print("Error in ModelCircuitParallel.run_model:", e)

    print("\n---- Testing estimate_rock (Series Model) ----")
    try:
        # Simulate experimental impedance as a slightly modified version of computed impedance.
        # Here we take the series model total impedance and add a 5% offset.
        z_exp = z_total_series * 1.05
        z_estimated_rock = series_model.estimate_rock(parameters, freq_array, z_exp)
        print("Estimated rock impedance from series model:")
        print(z_estimated_rock)
    except Exception as e:
        print("Error in ModelCircuitSeries.estimate_rock:", e)


if __name__ == '__main__':
    manual_test_circuit_models()