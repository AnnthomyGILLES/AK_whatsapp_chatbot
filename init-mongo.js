// Connect to the admin database
const adminDb = db.getSiblingDB("admin");

// Create the root user
adminDb.createUser({
  user: "ak_root",
  pwd: "s7LEOI5ugKmlXTPv",
  roles: [{ role: "root", db: "admin" }],
});

// Connect to the target database
const targetDb = db.getSiblingDB("mydatabase");

// Create other users in the target database
targetDb.createUser({
  user: "ak_flaskuser",
  pwd: "dQO0NmVMUr0U",
  roles: [{ role: "readWrite", db: "mydatabase" }],
});
