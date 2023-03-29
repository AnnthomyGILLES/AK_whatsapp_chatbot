// Connect to the target database
const targetDb = db.getSiblingDB("mydatabase");

// Create other users in the target database
targetDb.createUser({
  user: "ak_flaskuser",
  pwd: "dQO0NmVMUr0U",
  roles: [{ role: "readWrite", db: "mydatabase" }],
});

// Create the "users" collection
targetDb.createCollection("users");

// Create a unique index on the "phone_number" field in the "users" collection
targetDb.users.createIndex({ phone_number: 1 }, { unique: true });