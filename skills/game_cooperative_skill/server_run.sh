set -e

bash cron/run_cron.sh 

echo "Start server"
$@