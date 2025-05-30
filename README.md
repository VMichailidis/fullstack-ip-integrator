This is a script that performs the appropriate manipulations to set up a project directory for an axi accelerator on the pulp-platform.
It takes an hjson file as input and outputs a project directory with the rtl top level definitions for the accelerator specified by the hjson file as well as the c-headers required to author the drivers for the specified accelerator.
Additionally, it forks the pulp-platform directory and applies the appropriate patches for the pulpissimo rtl to include the axi accelerator and pulp-runtime to include the driver source code.
