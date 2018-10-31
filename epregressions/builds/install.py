import os

from epregressions.builds.base import BaseBuildDirectoryStructure
from epregressions.platform import exe_extension


class EPlusInstallDirectory(BaseBuildDirectoryStructure):

    def __init__(self):
        super().__init__()
        self.source_directory = None

    def set_build_directory(self, build_directory):
        """
        This method takes a build directory, and updates any dependent member variables, in this case the source dir.
        This method *does* allow an invalid build_directory, as could happen during program initialization

        :param build_directory:
        :return:
        """
        self.build_directory = build_directory
        if not os.path.exists(self.build_directory):
            self.source_directory = 'unknown - invalid build directory?'
            return
        # For an E+ install, the source directory is kinda just the root repo
        self.source_directory = build_directory

    def verify(self):
        results = []
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        build_dir = self.build_directory
        exists = os.path.exists(build_dir)
        results.append(
            ["Case %s Build Directory Exists? ", build_dir, exists]
        )
        exists = os.path.exists(self.source_directory)
        results.append(
            ["Case %s Source Directory Exists? ", self.source_directory, exists]
        )
        test_files_dir = os.path.join(self.source_directory, 'ExampleFiles')
        exists = os.path.exists(test_files_dir)
        results.append(
            ["Case %s Test Files Directory Exists? ", test_files_dir, exists]
        )
        data_sets_dir = os.path.join(self.source_directory, 'DataSets')
        exists = os.path.exists(data_sets_dir)
        results.append(
            ["Case %s Data Sets Directory Exists? ", data_sets_dir, exists]
        )
        energy_plus_exe = os.path.join(
            self.build_directory, 'energyplus' + exe_extension
        )
        exists = os.path.exists(energy_plus_exe)
        results.append(
            ["Case %s EnergyPlus Binary Exists? ", energy_plus_exe, exists]
        )
        basement_exe = os.path.join(self.build_directory, 'PreProcess', 'GrndTempCalc', 'Basement' + exe_extension)
        exists = os.path.exists(basement_exe)
        results.append(
            ["Case %s Basement (Fortran) Binary Exists? ", basement_exe, exists]
        )
        return results

    def get_build_tree(self):
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        return {
            'build_dir': self.build_directory,
            'source_dir': self.source_directory,
            'energyplus': os.path.join(self.build_directory, 'energyplus' + exe_extension),
            'basement': os.path.join(self.build_directory, 'PreProcess', 'GrndTempCalc', 'Basement' + exe_extension),
            'idd_path': os.path.join(self.build_directory, 'Energy+.idd'),
            'slab': os.path.join(self.build_directory, 'PreProcess', 'GrndTempCalc', 'Slab' + exe_extension),
            'basementidd': os.path.join(self.build_directory, 'PreProcess', 'GrndTempCalc', 'BasementGHT.idd'),
            'slabidd': os.path.join(self.build_directory, 'PreProcess', 'GrndTempCalc', 'SlabGHT.idd'),
            'expandobjects': os.path.join(self.build_directory, 'ExpandObjects' + exe_extension),
            'epmacro': os.path.join(self.build_directory, 'EPMacro' + exe_extension),
            'readvars': os.path.join(self.build_directory, 'PostProcess', 'ReadVarsESO'),
            'parametric': os.path.join(
                self.build_directory, 'PreProcess', 'ParametricPreprocessor', 'ParametricPreprocessor' + exe_extension
            ),
            'test_files_dir': os.path.join(self.source_directory, 'ExampleFiles'),
            'weather_dir': os.path.join(self.source_directory, 'WeatherData'),
            'data_sets_dir': os.path.join(self.source_directory, 'DataSets')
        }