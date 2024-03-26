
# Detect machine
host=$(hostname)

if [[ ${host} == "Orion"* ]]; then
  echo "Machine: Orion"
  module purge
  module use -a /apps/contrib/miniconda3-noaa-gsl/modulefiles
  module load miniconda3
  conda activate /work2/noaa/wrfruc/murdzek/conda/my_py
  export PYTHONPATH=$PYTHONPATH:/work2/noaa/wrfruc/murdzek/src/
elif [[ ${host} == "hercules"* ]]; then
  echo "Machine: Hercules"
  module purge
  module load miniconda3/4.10.3
  source activate /work2/noaa/wrfruc/murdzek/conda/my_py_hercules
  export PYTHONPATH=$PYTHONPATH:/work2/noaa/wrfruc/murdzek/src/
else
  echo "unknown host: ${host}"
  return 1
fi
