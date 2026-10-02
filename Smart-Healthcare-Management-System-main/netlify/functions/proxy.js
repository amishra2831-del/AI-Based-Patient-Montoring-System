// netlify/functions/proxy.js
// Optional Serverless Function that proxies /api/* to the Express backend.
//
// The frontend talks to the backend directly through VITE_API_URL, so this
// function is only needed for setups that want same-origin API calls.
// Point it at a deployment by setting BACKEND_URL in the Netlify environment:
//
//   BACKEND_URL=https://<your-backend-domain>

const { createProxyMiddleware } = require("http-proxy-middleware");

const BACKEND_URL = (
  process.env.BACKEND_URL || "http://localhost:5000"
).replace(/\/$/, "");

const proxy = createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  pathRewrite: {
    "^/api": "",
  },
  // Serverless invocations end when the response is written, so make sure
  // pending requests are not reaped early.
  on: {
    proxyReq: (proxyReq, req, res) => {
      proxyReq.setHeader("x-forwarded-host", req.headers.host);
    },
    error: (err, req, res) => {
      console.error("Proxy error:", err.message);

      if (!res.headersSent && typeof res.status === "function") {
        res.status(502).json({
          success: false,
          message:
            "Backend unavailable. Set BACKEND_URL to the deployed backend origin.",
        });
      }
    },
  },
});

exports.handler = async function (event, context) {
  return proxy(event, context);
};