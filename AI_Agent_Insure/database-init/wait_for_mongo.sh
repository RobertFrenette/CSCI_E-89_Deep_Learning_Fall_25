#!/bin/bash
# Wait for MongoDB to be ready
MONGO_HOST=${1:-mongodb}
MONGO_PORT=${2:-27017}
TRIES=${3:-20}
SLEEP=${4:-3}

for i in $(seq 1 $TRIES); do
  if mongo --host "$MONGO_HOST" --port "$MONGO_PORT" --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    echo "MongoDB is ready!"
    exit 0
  fi
  echo "Waiting for MongoDB ($MONGO_HOST:$MONGO_PORT)... ($i/$TRIES)"
  sleep $SLEEP
done

echo "MongoDB is still not ready after $((TRIES*SLEEP)) seconds."
exit 1
