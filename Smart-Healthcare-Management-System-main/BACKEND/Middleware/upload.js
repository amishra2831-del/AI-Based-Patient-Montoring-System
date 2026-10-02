const multer = require("multer");
const fs = require("fs");
const path = require("path");

// Resolve the upload directory from this file's location instead of the
// process working directory, so uploads work no matter where the server
// is started from.
//
// Serverless platforms (Vercel, Netlify, AWS Lambda) mount the project as
// read-only and only allow writes to /tmp, so the writable temp directory
// is used there. Set UPLOAD_DIR to control the location explicitly.
const isServerless = Boolean(
  process.env.VERCEL ||
    process.env.AWS_LAMBDA_FUNCTION_NAME ||
    process.env.NETLIFY
);

const UPLOAD_DIR =
  process.env.UPLOAD_DIR ||
  (isServerless
    ? path.join("/tmp", "uploads")
    : path.join(__dirname, "..", "uploads"));

try {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
} catch (err) {
  console.error(
    `Could not create upload directory (${UPLOAD_DIR}):`,
    err.message
  );
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    try {
      fs.mkdirSync(UPLOAD_DIR, { recursive: true });
      cb(null, UPLOAD_DIR);
    } catch (err) {
      cb(err);
    }
  },
  filename: (req, file, cb) =>
    cb(null, Date.now() + "-" + file.originalname.replace(/\s+/g, "_")),
});

const fileFilter = (req, file, cb) => {
  const allowedTypes = ["application/pdf", "image/jpeg", "image/png"];
  allowedTypes.includes(file.mimetype) ? cb(null, true) : cb(new Error("Invalid file type"));
};

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter,
});

module.exports = upload;
module.exports.UPLOAD_DIR = UPLOAD_DIR;
module.exports.upload = upload;