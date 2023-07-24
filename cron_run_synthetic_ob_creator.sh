
# Activate Python environment
source ./activate_python_env.sh

echo '' >> cron.log
date >> cron.log
python run_synthetic_ob_creator.py synthetic_ob_creator_param.yml >> cron.log
