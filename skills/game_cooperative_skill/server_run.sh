set -e

bash cron/run_cron.sh 1

echo "Start server"
$@