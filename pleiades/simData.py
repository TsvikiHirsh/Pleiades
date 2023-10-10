import re
import configparser
import numpy as np
from scipy.interpolate import interp1d
import pleiades.nucData as pnd

AVOGADRO = 6.02214076E23    # Avogadro's number
CM2_TO_BARN = 1E24          # Conversion factor from cm2 to barns

def create_transmission(energy_grid, isotope):
    """Create the transmission data for the given material based on interpolation of the 
    cross-section data and the energy grid for a given material thickness and density.
    This uses the the attenuation formula: T = e^(-sigma * A) where sigma is the cross-section,
    and A is the areal density, which can be taken as thickness * density.

    Args:
        xs_data (tuple array): list of tuples containing the energy and cross-section data
        thickness (float): thickness of the material
        thickness_unit (string): unit of the thickness for the given material
        density (float): density of the material
        density_unit (string): unit of the density for the given material
    """
    
    # TODO: Convert thickness and density to consistent units if necessary. 
    # This is just an example; you'd need to provide conversion factors.
    
    # Extract information from the isotope object
    thickness = isotope.thickness
    atomic_mass = isotope.atomic_mass
    thickness_unit = isotope.thickness_unit
    density = isotope.density
    density_unit = isotope.density_unit
    xs_data = isotope.xs_data
    
    if thickness_unit != "cm":
        if thickness_unit == "mm":
            thickness /= 10.0
        else:
            raise ValueError("Unsupported thickness unit: {thickness_unit} for {isotope_name}")
    if density_unit != "g/cm3":
        raise ValueError("Unsupported density unit:{density_unit} for {isotope_name}")

    areal_density = thickness * density * AVOGADRO / atomic_mass / CM2_TO_BARN 
    
    # Create interpolation function for cross-section data
    energies_eV, cross_sections = zip(*xs_data)
    interpolate_xs_data = interp1d(energies_eV, cross_sections, kind='linear', fill_value="extrapolate")

    # create a list of tuples containing the energy and transmission data
    transmission = []
    interploated_cross_section = []
    
    for energy in energy_grid:
        # Get the cross-section at the given energy
        xs = interpolate_xs_data(energy)
        interploated_cross_section.append((energy, xs))
        
        # Calculate the transmission
        transmission.append((energy, np.exp(-xs * areal_density)))    

    return transmission


def parse_xs_file(file_location, isotope_name):
    """ Parse the cross-section file and return the data for the isotope.

    Args:
        file_location (string): File location of the cross-section data
        isotope_name (string): Name of the isotope to find in the file

    Raises:
        ValueError: If the isotope is not found in the file

    Returns:
        xs_data: List of tuples containing the energy and cross-section data
    """
    
    xs_data = []
    isotope_xs_found = False
    capture_data = False
    with open(file_location, 'r') as f:
        for line in f:
            # If we find the name of the isotope
            if isotope_name in line:
                isotope_xs_found = True
            # If we have found the isotope, then look for the "#data..." marker
            if isotope_xs_found:
                if "#data..." in line:
                    capture_data = True
                # If we find the "//" line, stop capturing data
                elif '//' in line:
                    capture_data = False
                    break
                # If capture_data is True and the line doesn't start with a '#', then it's the data
                elif capture_data and not line.startswith("#"):
                    energy_eV, xs = line.split()
                    xs_data.append((float(energy_eV)*1E6, float(xs))) # Convert energy from MeV to eV
                
                
    # If the loop completes and the isotope was not found
    if not isotope_xs_found:
        raise ValueError("Cross-section data for {isotope_name} not found in {file_location}".format(isotope_name=isotope_name, file_location=file_location))

    return xs_data



class Isotope:
    """Class to hold information about an isotope from a config file.
    """
    def __init__(self, name="Unknown", atomic_mass=0.0, thickness=0.0, thickness_unit="atoms/cm2", abundance=0.0, xs_file_location="Unknown", density=0.0, density_unit="g/cm3"):
        self.name = name
        self.atomic_mass = atomic_mass
        self.thickness = thickness
        self.thickness_unit = thickness_unit
        self.abundance = abundance
        self.xs_file_location = xs_file_location
        self.density = density
        self.density_unit = density_unit
        self.xs_data = []  # Array to hold xs data
    
    def load_xs_data(self):
        """Load cross-section data from file."""
        self.xs_data = parse_xs_file(self.xs_file_location, self.name)
        if not self.xs_data:
            raise ValueError(f"No data loaded for {self.name} from {self.xs_file_location}")
    
    def __repr__(self):
        xs_status = "XS data loaded successfully" if len(self.xs_data) != 0 else "XS data not loaded"
        return f"Isotope({self.name},{self.atomic_mass},{self.thickness} {self.thickness_unit}, {self.abundance}, {self.xs_file_location}, {self.density} {self.density_unit}, {xs_status})"

class Isotopes:
    """Class to hold information about all isotopes from a config file.
    """
    def __init__(self, config_file):
        self.isotopes = []
        config = configparser.ConfigParser()
        config.read(config_file)

        # Create a dummy Isotope instance to get the default values
        default_isotope = Isotope()

        for section in config.sections():
            # Check if the ignore flag is set for this isotope
            ignore = config.getboolean(section, 'ignore', fallback=False)
            if ignore:
                continue
            
            # Fetch each attribute with the default value from the dummy Isotope instance
            name = config.get(section, 'name', fallback=default_isotope.name)
            atomic_mass = pnd.get_mass_from_ame(name)
            thickness = config.getfloat(section, 'thickness', fallback=default_isotope.thickness)
            thickness_unit = config.get(section, 'thickness_unit', fallback=default_isotope.thickness_unit)
            abundance = config.getfloat(section, 'abundance', fallback=default_isotope.abundance)
            xs_file_location = config.get(section, 'xs_file_location', fallback=default_isotope.xs_file_location)
            density = config.getfloat(section, 'density', fallback=default_isotope.density)
            density_unit = config.get(section, 'density_unit', fallback=default_isotope.density_unit)

            # Create an Isotope instance and load the xs data
            isotope = Isotope(name, atomic_mass, thickness, thickness_unit, abundance, xs_file_location, density, density_unit)
            isotope.load_xs_data()  # Load xs data for the isotope
            
            # Add the isotope to the list of isotopes
            self.isotopes.append(isotope)
    
    # print the isotopes using __repr__. This is called when you do print(isotopes).  
    def __repr__(self):
        return "\n".join([str(isotope) for isotope in self.isotopes])
