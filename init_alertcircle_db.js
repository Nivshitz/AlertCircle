
// Switch to or create the database
use AlertCircleProject;

// === Collection: alerts_live ===
db.createCollection("alerts_live");

// TTL index on ingestion time (remove docs after 10 minutes)
db.alerts_live.createIndex(
  { ingestion_time_ttl: 1 },
  { expireAfterSeconds: 600 }
);

// Geospatial index on alert point
db.alerts_live.createIndex(
  { alert_point: "2dsphere" }
);

// Optional indexes for performance (useful for queries/filters)
db.alerts_live.createIndex({ notified_users: 1 });
db.alerts_live.createIndex({ event_time: 1 });
db.alerts_live.createIndex(
  { notified_users: 1, event_time: 1 }
);

// === Collection: latest_user_location ===
db.createCollection("latest_user_location");

// TTL index on insert time (remove after 5 minutes)
db.latest_user_location.createIndex(
  { insert_time_ttl: 1 },
  { expireAfterSeconds: 300 }
);

// Geospatial index for user location
db.latest_user_location.createIndex(
  { location: "2dsphere" }
);
