import pathlib
from typing import List, Union, Dict

class LptFile:
    # utilities to read and parse an LPT output file

    def __init__(self,filename: str) -> None:
        """Reads a .lpt file

        Args:
            filename (str): SAMMY output file with .lpt extension
        """
        self._filename = filename
        
        LPT_SEARCH_PATTERNS = {
            "input_file":dict(
                start_text=" Name of input file",
                skipped_rows=1,
                line_format="line.split()[1]"),
            "par_file":dict(
                start_text=" Name of parameter file",
                skipped_rows=1,
                line_format="line.split()[1]"),
            "Emin":dict(
                start_text=" Emin and Emax",
                skipped_rows=0,
                line_format="float(line.split()[4])"),
            "Emax":dict(
                start_text=" Emin and Emax",
                skipped_rows=0,
                line_format="float(line.split()[5])"),
            "thickness":dict(
                start_text=" Target Thickness=",
                skipped_rows=0,
                line_format="float(line.split()[2])"),
            "varied_params":dict(
                start_text=" Number of varied parameters",
                skipped_rows=0,
                line_format="int(line.split()[5])"),
            "reduced_chi2":dict(
                start_text=" CUSTOMARY CHI SQUARED DIVIDED",
                skipped_rows=0,
                line_format="float(line.split()[7])"),
            "time_elapsed":dict(
                start_text="                              Total time",
                skipped_rows=0,
                line_format="float(line.split()[3])"),
            }
    
        self.LPT_SEARCH_PATTERNS = LPT_SEARCH_PATTERNS
            

    def stats(self) -> dict:
        """parse and collect statistical data from a SAMMY.LPT file
        
        Returns (dict): formatted statistical data from the run
        """        
        stats = {}
        # loop over all search patterns
        for pattern_key in self.LPT_SEARCH_PATTERNS:
            with open(self._filename,"r") as fid:
                for line in fid:
                    pattern = self.LPT_SEARCH_PATTERNS[pattern_key]    
                    if line.startswith(pattern["start_text"]):
                        # skip requested number of rows
                        [line:=next(fid) for row in range(pattern["skipped_rows"])]
                        # update the stats dictionary
                        try:
                            stats[pattern_key] = eval(pattern["line_format"])
                        except:
                            import warnings
                            warnings.warn(f"pattern key: {pattern_key} has returned wrong parsing result")

        return stats
    

    def register_new_stats(self,keyname: str, start_text: str, skipped_rows: str, line_format: str ) -> None:
        """
        Registers a search pattern for parsing statistical values from the .lpt file.

        Args:
            - keyname (str): The name of the requested parameter.
            - start_text (str): A string used for line.startswith search to identify relevant lines.
            - skipped_rows (int): The number of rows to skip from the 'start_text' during parsing.
            - line_format (str): Python code snippet used to parse the line for the requested value.
                                Typically, this would be a split method on the input `line` variable.

        Example:
        Register a search pattern for temperature values in the .lpt file:
        >>> from pleiades import sammyOutput
        >>> sammyOutput.register_search_pattern(keyname="temperature", start_text="  TEMPERATURE",
                                                skipped_rows=1, line_format="float(line.split()[0])")
        """
        self.LPT_SEARCH_PATTERNS[keyname] = dict(start_text=start_text,
                                                 skipped_rows=skipped_rows,
                                                 line_format=line_format)
        
    def register_normalization_stats(self) -> None:
        """
        register six normalization params to the `stats` method
        """
        self.register_new_stats("normalization","   NORMALIZATION", 1, "float(line[2:13])")
        self.register_new_stats("constant_bg","   NORMALIZATION", 1, "float(line[19:29])")
        self.register_new_stats("one_over_v_bg","   NORMALIZATION", 1, "float(line[36:47])")
        self.register_new_stats("sqrt_energy_bg","   NORMALIZATION", 1, "float(line[53:63])")
        self.register_new_stats("exponential_bg","    BCKG*EXP(.)", 1, "float(line[2:13])")
        self.register_new_stats("exp_decay_bg","    BCKG*EXP(.)", 1, "float(line[19:29])")

    def register_broadening_stats(self) -> None:
        """
        register five broadening params to the `stats` method
        """
        self.register_new_stats("temperature","  TEMPERATURE      THICKNESS", 1, "float(line[2:13])")
        self.register_new_stats("thickness","  TEMPERATURE      THICKNESS", 1, "float(line[19:29])")
        self.register_new_stats("flight_path_spread","    DELTA-L         DELTA-T-GAUS", 1, "float(line[2:13])")
        self.register_new_stats("deltag_fwhm","    DELTA-L         DELTA-T-GAUS", 1, "float(line[19:29])")
        self.register_new_stats("deltae_us","    DELTA-L         DELTA-T-GAUS", 1, "float(line[36:47])")


    def register_abundances_stats(self,isotopes:list =[]) -> None:
        """
        register final isotopic abundances

        Args:
            - isotopes (list): A list of isotope names, in the order added to the compound par file
                               in case of empty list, pleiades will try to read the first 5 isotopes and assign them with numbers 
        """
        if isotopes:
            for num,isotope in enumerate(isotopes):
                self.register_new_stats(f"weight_{isotope}"," Nuclide    Abundance", num+1, "float(line[12:18])")
        else:
            for num in range(5):
                self.register_new_stats(f"weight_{num}"," Nuclide    Abundance", num+1, "float(line[12:18])")            




    def commands(self) -> list:
        """parse and collect the alphanumeric command cards from a SAMMY.LPT file
        
            Returns (list): of alphanumeric commands used in SAMMY run
        """        
        with open(self._filename,"r") as fid:
            for line in fid:
                if line.startswith(" *********** Alphanumeric Control Information"):
                    line = next(fid)
                    cards = []
                    while not line.startswith(" **** end"):
                        if line.strip():
                            cards.append(line.replace("\n","").strip())
                        line = next(fid)
                        
        return cards
    


