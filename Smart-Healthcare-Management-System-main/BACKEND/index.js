const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
require("dotenv").config();

// ============================================================
// IMPORT ROUTES
// ============================================================

const userRoutes = require("./Routes/UserRoutes");
const authRoutes = require("./Routes/authRoutes");
const appointmentRoute = require("./Routes/AppoinmentRoutes");
const rejectedAppointmentRoutes = require("./Routes/RejectAppoinmentRoutes");
const doctorRoute = require("./Routes/DoctorManagement/doctorRoute");
const stockRoute = require("./Routes/StockRoutes");
const forgotPasswordRoute = require("./Routes/ForgotPasswordRoutes");
const prescriptionRoute = require("./Routes/DoctorManagement/prescriptionRoute");
const doctorLeaveRoutes = require("./Routes/DoctorManagement/doctorLeaveRoutes");
const diagnosisRoute = require("./Routes/DoctorManagement/diagnosisRoute");
const noveltyRoutes = require("./Routes/NoveltyRoutes");
const analysisRoutes = require("./Routes/AnalysisRoutes");
const vitalsRoutes = require("./Routes/VitalsRoutes");
const medicalReportRoutes = require("./Routes/medicalReportRoutes");

// ============================================================
// EXPRESS APP
// ============================================================

const app = express();

// ============================================================
// CORS CONFIGURATION
// ============================================================

// Frontend URLs from Vercel environment variables
const configuredOrigins = [
  process.env.FRONTEND_URL,
  process.env.FRONTEND01,
  process.env.FRONTEND02,
]
  .filter(Boolean)
  .flatMap((value) => value.split(","))
  .map((value) => value.trim().replace(/\/$/, ""))
  .filter(Boolean);

// Local development URLs
const localOrigins = [
  "http://localhost:5173",
  "http://127.0.0.1:5173",
];

// Combine configured + local origins
const allowedOrigins = [
  ...new Set([
    ...configuredOrigins,
    ...localOrigins,
  ]),
];

console.log("========================================");
console.log("CORS CONFIGURATION");
console.log("========================================");
console.log("Configured frontend origins:");
console.log(allowedOrigins);
console.log("========================================");

// ============================================================
// CORS MIDDLEWARE
// ============================================================

app.use(
  cors({
    origin: function (origin, callback) {
      // --------------------------------------------------------
      // Allow requests without Origin
      // --------------------------------------------------------
      // Examples:
      // Postman
      // curl
      // server-to-server requests
      // --------------------------------------------------------

      if (!origin) {
        return callback(null, true);
      }

      const normalizedOrigin = origin
        .trim()
        .replace(/\/$/, "");

      // --------------------------------------------------------
      // Exact configured frontend URL
      // --------------------------------------------------------

      if (allowedOrigins.includes(normalizedOrigin)) {
        console.log("CORS allowed:", normalizedOrigin);
        return callback(null, true);
      }

      // --------------------------------------------------------
      // Allow Vercel preview/deployment URLs
      // --------------------------------------------------------
      // Example:
      // https://health-frontend-jnkwk387b-amishra2831-dels-projects.vercel.app
      //
      // This is useful because Vercel can generate different
      // deployment URLs.
      // --------------------------------------------------------

      try {
        const url = new URL(normalizedOrigin);

        if (
          url.protocol === "https:" &&
          url.hostname.endsWith(".vercel.app")
        ) {
          console.log(
            "CORS allowed Vercel origin:",
            normalizedOrigin
          );

          return callback(null, true);
        }
      } catch (error) {
        console.log(
          "Invalid origin received:",
          normalizedOrigin
        );
      }

      // --------------------------------------------------------
      // Block unknown origins
      // --------------------------------------------------------

      console.log(
        "CORS BLOCKED ORIGIN:",
        normalizedOrigin
      );

      return callback(
        new Error(
          `CORS blocked origin: ${normalizedOrigin}`
        )
      );
    },

    credentials: true,

    methods: [
      "GET",
      "POST",
      "PUT",
      "PATCH",
      "DELETE",
      "OPTIONS",
    ],

    allowedHeaders: [
      "Content-Type",
      "Authorization",
      "Accept",
      "Origin",
      "X-Requested-With",
    ],

    optionsSuccessStatus: 204,
  })
);

// ============================================================
// BODY PARSERS
// ============================================================

app.use(
  express.json({
    limit: "10mb",
  })
);

app.use(
  express.urlencoded({
    extended: true,
    limit: "10mb",
  })
);

// ============================================================
// ROOT ROUTE
// ============================================================

app.get("/", (req, res) => {
  res.status(200).json({
    status: "ok",
    service: "medi-flow-backend",
    environment: process.env.NODE_ENV || "development",
    message: "Backend API is running successfully",
  });
});

// ============================================================
// HEALTH CHECK
// ============================================================

app.get("/health", (req, res) => {
  res.status(200).json({
    status: "ok",
    service: "medi-flow-backend",
    mongodb:
      mongoose.connection.readyState === 1
        ? "connected"
        : "disconnected",
  });
});

// ============================================================
// API ROUTES
// ============================================================

// Authentication
// POST /api/auth/register
// POST /api/auth/login
app.use("/api/auth", authRoutes);

// User Management
app.use("/api/users", userRoutes);

// Appointments
app.use("/api/appoinment", appointmentRoute);

// Rejected Appointments
app.use(
  "/api/rejected-appointments",
  rejectedAppointmentRoutes
);

// Doctor Management
app.use("/api/doctor", doctorRoute);

// Stock Management
app.use("/api/stock", stockRoute);

// Prescription
app.use(
  "/api/prescription",
  prescriptionRoute
);

// Prescriptions - plural route
app.use(
  "/api/prescriptions",
  prescriptionRoute
);

// Doctor Leave
app.use(
  "/api/doctorLeave",
  doctorLeaveRoutes
);

// Diagnosis
app.use(
  "/api/diagnosis",
  diagnosisRoute
);

// Forgot Password
app.use(
  "/api/auth/forgot-password",
  forgotPasswordRoute
);

// Novelty / Symptom Analysis
app.use(
  "/api/novelty",
  noveltyRoutes
);

// Analysis
app.use(
  "/api/analysis",
  analysisRoutes
);

// Vitals
app.use(
  "/api/vitals",
  vitalsRoutes
);

// Medical Reports
app.use(
  "/api/reports",
  medicalReportRoutes
);

// ============================================================
// STATIC UPLOADS
// ============================================================

const path = require("path");

app.use(
  "/uploads",
  express.static(
    path.join(__dirname, "uploads")
  )
);

// ============================================================
// API 404 HANDLER
// ============================================================

app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: "API endpoint not found",
    method: req.method,
    path: req.originalUrl,
  });
});

// ============================================================
// ERROR HANDLER
// ============================================================

app.use((err, req, res, next) => {
  console.error(
    "Backend error:",
    err.message
  );

  // CORS error
  if (
    err.message &&
    err.message.startsWith("CORS blocked origin")
  ) {
    return res.status(403).json({
      success: false,
      message: err.message,
    });
  }

  // General server error
  return res.status(500).json({
    success: false,
    message: "Internal server error",
  });
});

// ============================================================
// MONGODB CONNECTION
// ============================================================

const mongoURI = process.env.MONGO_URI || "";

if (mongoURI) {
  mongoose
    .connect(mongoURI)
    .then(() => {
      console.log("========================================");
      console.log("Connected to MongoDB");
      console.log("========================================");

      if (process.env.NODE_ENV !== "production") {
        const PORT = Number(process.env.PORT) || 5000;
        app.listen(PORT, () => {
          console.log(`Server running on port ${PORT}`);
        });
      }
    })
    .catch((err) => {
      console.error("Database connection error:", err.message);
    });
} else {
  console.log("========================================");
  console.log("MONGO_URI not set - running without database");
  console.log("========================================");

  if (process.env.NODE_ENV !== "production") {
    const PORT = Number(process.env.PORT) || 5000;
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT} (no DB)`);
    });
  }
}

// ============================================================
// EXPORT APP
// ============================================================

module.exports = app;