db.auth("ak_root", "s7LEOI5ugKmlXTPv");

db = db.getSiblingDB("mydatabase");

db.createUser({
  user: "ak_flaskuser",
  pwd: "dQO0NmVMUr0U",
  roles: [
    {
      role: "userAdminAnyDatabase",
      db: "admin",
    },
  ],
});