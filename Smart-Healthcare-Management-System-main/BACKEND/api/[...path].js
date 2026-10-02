// Vercel catch-all Serverless Function.
//
// Vercel maps a request path to the matching file inside /api, so without
// this file only /api and /api/index.js would exist and every real endpoint
// such as /api/auth/login would return 404.
//
// The [...path] dynamic route matches /api/** and receives the original
// request URL, which is what the Express app expects.
const app = require("../index.js");

module.exports = app;