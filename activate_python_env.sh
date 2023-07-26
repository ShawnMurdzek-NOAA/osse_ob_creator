
module purge
module use -a /apps/contrib/miniconda3-noaa-gsl/modulefiles
module load miniconda3
conda activate /work2/noaa/wrfruc/murdzek/conda/my_py
export PYTHONPATH=$PYTHONPATH:/work2/noaa/wrfruc/murdzek/src/
