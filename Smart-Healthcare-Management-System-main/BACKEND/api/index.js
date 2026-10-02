// Entry point for the /api root path on Vercel.
//
// The catch-all api/[...path].js handles /api/**. When this file is invoked
// for the bare /api path the Express app would not match its "/" route, so
// the URL is normalised to "/" before delegating.
const app = require("../index.js");

module.exports = (req, res) => {
  if (req.url === "/api" || req.url === "/api/") {
    req.url = "/";
  }

  return app(req, res);
};