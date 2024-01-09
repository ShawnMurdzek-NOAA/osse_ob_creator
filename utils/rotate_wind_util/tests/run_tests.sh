
# Bash script to run the tests for osse_ob_creator/utils/rotate_wind_util

################################################################################
# User-specified options
################################################################################



################################################################################
# Compare Earth-Relative Winds Computed Using wgrib2 and UPP
################################################################################
 
source ../../../activate_python_env.sh
echo
echo 'calling check_wgrib2_wind_rotation.py'
python check_wgrib2_wind_rotation.py test.yml

