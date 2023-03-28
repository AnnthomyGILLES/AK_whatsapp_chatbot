#!/bin/bash

cat <<EOF > /docker-entrypoint-initdb.d/init-mongo.js
db.auth("$MONGO_INITDB_ROOT_USERNAME", "$MONGO_INITDB_ROOT_PASSWORD");

db = db.getSiblingDB("$MONGO_INITDB_DATABASE");

db.createUser({
  user: "MONGODB_USERNAME",
  pwd: "MONGODB_PASSWORD",
  roles: [
    {
      role: "readWrite",
      db: "$MONGO_INITDB_DATABASE",
    },
  ],
});
EOF
