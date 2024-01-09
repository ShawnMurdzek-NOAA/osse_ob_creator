
# Activate Python environment
source ../../activate_python_env.sh

echo '' >> cron.log
date >> cron.log
python run_rotate_winds.py rotate_winds.yml >> cron.log
