echo "Stopping Weather House Data Pipeline..."
cd "$(dirname "$0")/.."
docker-compose down -v
echo "All services stopped and removed."