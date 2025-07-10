
# Bash script to run the tests for osse_ob_creator

################################################################################
# User-specified options
################################################################################

machine='hercules'
prepbufr_decoder_path=/work2/noaa/wrfruc/murdzek/src/prepbufr_decoder/machine_bin/${machine}
datadir=/work2/noaa/wrfruc/murdzek/src/osse_ob_creator/tests/data

# Option to re-create test data
create_test_data=false

# Option to run linear_interp_test
run_linear_interp_test=true

# Option to run select_obs test
run_select_obs_test=true

# Option to run UAS test
run_uas_test=true


################################################################################
# General Setup
################################################################################

cd ../../
home=`pwd`
cd osse_ob_creator/tests


################################################################################
# Create Test Data
################################################################################

if ${create_test_data}; then

  echo
  echo '==============================='
  echo 'Creating Test Data'
  echo

  source ../activate_python_env.sh
  echo 'entering create_test_datasets.py...'
  python create_test_datasets.py
 
  echo 'converting observation CSV file to prepBUFR...' 
  csv_fname=`ls *prepbufr.csv`
  mkdir tmp
  cd tmp
  cp -r ${prepbufr_decoder_path}/bin/* .
  mv ../${csv_fname} ./prepbufr.csv
  echo ${csv_fname}
  echo ${csv_fname::-4}
  echo ${csv_fname::8}
  source ${prepbufr_decoder_path}/env/bufr_${machine}.env
  ./prepbufr_encode_csv.x
  mv ./prepbufr ../${csv_fname::-4}.tm00
  cd ..
  rm -r tmp

  mkdir data
  mkdir data/${csv_fname::8}
  mv ${csv_fname::-4}.tm00 ./data/
  mv *.nc ./data/${csv_fname::8}/

  echo
  echo 'Done creating test data'
  echo

fi


################################################################################
# Run Linear Interpolation Test
################################################################################

if ${run_linear_interp_test}; then
  
  echo
  echo '==============================='
  echo 'Running Linear Interpolation Test'
  echo

  if [ -d ./linear_interp_test ]; then
    echo 'removing old linear_interp_test directory'
    rm -rf ./linear_interp_test
  fi
  mkdir linear_interp_test 

  echo 
  echo 'creating input YAML file'
  cp linear_interp_test.yml ./linear_interp_test
  sed -i "s={HOMEDIR}=${home}=" ./linear_interp_test/linear_interp_test.yml
  sed -i "s={BUFRDIR}=${prepbufr_decoder_path}=" ./linear_interp_test/linear_interp_test.yml
  sed -i "s={DATADIR}=${datadir}=" ./linear_interp_test/linear_interp_test.yml

  cd ..
  source activate_python_env.sh
  echo
  echo 'calling create_syn_ob_jobs.py'
  python create_syn_ob_jobs.py ./tests/linear_interp_test/linear_interp_test.yml

  echo
  echo 'calling run_synthetic_ob_creator.py'
  job_line=$(python run_synthetic_ob_creator.py ./tests/linear_interp_test/linear_interp_test.yml | grep "submitted job")
  cd ./tests/
  if [[ `echo ${job_line} | wc -c` -lt 2 ]]; then
    echo 'no job submitted for linear interpolation test'
    linear_interp_test_pass=false
  else
    job_id=${job_line:16:8}  
    echo "Slurm jobID = ${job_id}"

    scomplete=`sacct --job ${job_id} | grep "COMPLETED" | wc -c`
    while [ ${scomplete} -lt 2 ]; do
      echo "waiting 1 minute for job to finish..."
      sleep 60
      scomplete=`sacct --job ${job_id} | grep "COMPLETED" | wc -c`
    done
    echo "Job done. Start verification"
    echo

    # First check to ensure that all output files exist
    err_linear_interp=0
    for s in ${subdirs}; do
      if [[ `ls -l linear_interp_test/${s} | wc -l` -lt 2 ]]; then
        echo "missing output file(s) in linear_interp_test/${s}"
        err_linear_interp=1
        linear_interp_test_pass=false
      fi
    done
    if [[ ${err_linear_interp} -eq 0 ]]; then
      echo "all output subdirectories are populated"
    fi

    # Perform verification using Python script
    if [[ ${err_linear_interp} -eq 0 ]]; then
      python check_linear_interp_test.py > ./linear_interp_test/test.log
      err_linear_interp=`tail -1 ./linear_interp_test/test.log`
      if [[ ${err_linear_interp} -eq 0 ]]; then
        echo "linear interpolation test passed"
        linear_interp_test_pass=true
      else
        echo "linear interpolation test failed, error code = ${err_linear_interp}"
        linear_interp_test_pass=false
      fi
    fi
  fi
fi


################################################################################
# Run Select Obs Test
################################################################################

if ${run_select_obs_test}; then
  
  echo
  echo '==============================='
  echo "Running Select Obs Test"
  echo

  if [ -d ./select_obs_test ]; then
    echo 'removing old select_obs_test directory'
    rm -rf ./select_obs_test
  fi
  mkdir select_obs_test 
 
  echo 
  echo 'creating input YAML file'
  cp select_obs_test.yml ./select_obs_test
  sed -i "s={HOMEDIR}=${home}=" ./select_obs_test/select_obs_test.yml
  sed -i "s={BUFRDIR}=${prepbufr_decoder_path}=" ./select_obs_test/select_obs_test.yml
  sed -i "s={DATADIR}=${datadir}=" ./select_obs_test/select_obs_test.yml

  cd ../
  source activate_python_env.sh
  echo
  echo 'calling create_syn_ob_jobs.py'
  python create_syn_ob_jobs.py ./tests/select_obs_test/select_obs_test.yml

  echo
  echo 'calling run_synthetic_ob_creator.py'
  job_line=$(python run_synthetic_ob_creator.py ./tests/select_obs_test/select_obs_test.yml | grep "submitted job")
  cd ./tests/
  if [[ `echo ${job_line} | wc -c` -lt 2 ]]; then
    echo "no job submitted for select_obs test"
    select_obs_test_pass=false
  else
    job_id=${job_line:16:8}  
    echo "Slurm jobID = ${job_id}"

    scomplete=`sacct --job ${job_id} | grep "COMPLETED" | wc -c`
    while [ ${scomplete} -lt 2 ]; do
      echo "waiting 15 s for job to finish..."
      sleep 15
      scomplete=`sacct --job ${job_id} | grep "COMPLETED" | wc -c`
    done
    echo "Job done. Start verification"
    echo
    
    # First check to ensure that all output files exist
    err_select_obs=0
    for s in ${subdirs}; do
      if [[ `ls -l select_obs_test/${s} | wc -l` -lt 2 ]]; then
        echo "missing output file(s) in select_obs_test/${s}"
        err_select_obs=1
        select_obs_test_pass=false
      fi
    done
    if [[ ${err_select_obs} -eq 0 ]]; then
      echo "all output subdirectories are populated"
    fi

    # Perform verification using Python script
    if [[ ${err_select_obs} -eq 0 ]]; then
      python check_select_obs_test.py > ./select_obs_test/test.log
      err_select_obs=`tail -1 ./select_obs_test/test.log`
      if [[ ${err_select_obs} -eq 0 ]]; then
        echo "select obs test passed"
        select_obs_test_pass=true
      else
        echo "select obs test failed, error code = ${err_select_obs}"
        select_obs_test_pass=false
      fi
    fi
  fi
fi


################################################################################
# Run UAS Test
################################################################################

if ${run_uas_test}; then
  
  echo
  echo '==============================='
  echo "Running UAS Test"
  echo

  if [ -d ./uas_test ]; then
    echo 'removing old uas_test directory'
    rm -rf ./uas_test
  fi
  mkdir uas_test 
 
  echo 
  echo 'creating input YAML file'
  cp uas_test.yml ./uas_test
  sed -i "s={HOMEDIR}=${home}=" ./uas_test/uas_test.yml
  sed -i "s={BUFRDIR}=${prepbufr_decoder_path}=" ./uas_test/uas_test.yml
  sed -i "s={DATADIR}=${datadir}=" ./uas_test/uas_test.yml

  cd ../
  source activate_python_env.sh
  echo
  echo 'calling create_syn_ob_jobs.py'
  python create_syn_ob_jobs.py ./tests/uas_test/uas_test.yml

  echo
  echo 'calling run_synthetic_ob_creator.py'
  job_line=$(python run_synthetic_ob_creator.py ./tests/uas_test/uas_test.yml | grep "submitted job")
  cd ./tests/
  if [[ `echo ${job_line} | wc -c` -lt 2 ]]; then
    echo "no job submitted for uas test"
    uas_test_pass=false
  else
    job_id=${job_line:16:8}  
    echo "Slurm jobID = ${job_id}"

    scomplete=`sacct --job ${job_id} | grep "COMPLETED" | wc -c`
    while [ ${scomplete} -lt 2 ]; do
      echo "waiting 1 min for job to finish..."
      sleep 60
      scomplete=`sacct --job ${job_id} | grep "COMPLETED" | wc -c`
    done
    echo "Job done. Start verification"
    echo
    
    # First check to ensure that all output files exist
    err_uas=0
    for s in ${subdirs}; do
      if [[ `ls -l uas_test/${s} | wc -l` -lt 2 ]]; then
        echo "missing output file(s) in uas_test/${s}"
        err_uas=1
        uas_test_pass=false
      fi
    done
    if [[ ${err_uas} -eq 0 ]]; then
      echo "all output subdirectories are populated"
    fi

    # Perform verification using Python script
    if [[ ${err_uas} -eq 0 ]]; then
      python check_uas_test.py > ./uas_test/test.log
      err_uas=`tail -1 ./uas_test/test.log`
      if [[ ${err_uas} -eq 0 ]]; then
        echo "UAS test passed"
        uas_test_pass=true
      else
        echo "UAS test failed, error code = ${err_uas}"
        uas_test_pass=false
      fi
    fi
  fi
fi


################################################################################
# Print Final Test Results
################################################################################

echo
echo '==============================='
echo 'Final Test Results'
echo

if ${run_linear_interp_test}; then
  echo "Pass Linear Interpolation Test? ${linear_interp_test_pass}"
fi
if ${run_select_obs_test}; then
  echo "Pass Select Obs Test? ${select_obs_test_pass}"
fi
if ${run_uas_test}; then
  echo "Pass UAS Test? ${uas_test_pass}"
fi
echo

