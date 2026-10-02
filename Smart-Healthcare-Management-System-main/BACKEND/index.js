const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
require("dotenv").config(); // Load environment variables

// Import Routes
const userRoutes = require("./Routes/UserRoutes"); // User Management Routes
const authRoutes = require("./Routes/authRoutes"); // Authentication Routes
const appointmentRoute = require("./Routes/AppoinmentRoutes"); // Appointment Route
const rejectedAppointmentRoutes = require("./Routes/RejectAppoinmentRoutes");
const doctorRoute = require("./Routes/DoctorManagement/doctorRoute"); // Doctor Route
const stockRoute = require("./Routes/StockRoutes"); // Stock Route
const forgotPasswordRoute = require("./Routes/ForgotPasswordRoutes"); // Forgot Password Routes
const prescriptionRoute = require("./Routes/DoctorManagement/prescriptionRoute"); // Prescription Route
const doctorLeaveRoutes = require("./Routes/DoctorManagement/doctorLeaveRoutes"); // Doctor Leave Route
const diagnosisRoute = require("./Routes/DoctorManagement/diagnosisRoute"); // Diagnosis Route
const noveltyRoutes = require("./Routes/NoveltyRoutes"); // Import Novelty Routes

const app = express(); // initialize express application
const analysisRoutes = require("./Routes/AnalysisRoutes");
const vitalsRoutes = require("./Routes/VitalsRoutes");

// Middleware
const allowedOrigins = [
  process.env.FRONTEND01,
  process.env.FRONTEND02,
  "http://localhost:5173",
  "http://127.0.0.1:5173",
].filter(Boolean);

app.use(cors({
  origin: function (origin, callback) {
    // Allow non-browser clients and configured frontends; Vercel preview domains are allowed
    if (!origin || allowedOrigins.includes(origin) || process.env.NODE_ENV === "production") {
      return callback(null, true);
    }
    return callback(null, true);
  },
  credentials: true
}));
app.use(express.json());

app.get("/", (req, res) => {
  res.json({
    status: "ok",
    service: "medi-flow-backend",
    environment: process.env.NODE_ENV || "development",
  });
});

// API Routes
app.use("/api/auth", authRoutes); // Routes for Login/Register
app.use("/api/users", userRoutes); // Routes for User CRUD
app.use("/api/appoinment", appointmentRoute); // Routes for Appointment Management
app.use("/api/rejected-appointments", rejectedAppointmentRoutes);
app.use("/api/doctor", doctorRoute); // Routes for Doctor Management
app.use("/api/stock", stockRoute); // Routes for Stock Management
app.use("/api/prescription", prescriptionRoute); // Routes for Prescription Management
app.use("/api/prescriptions", require("./Routes/DoctorManagement/prescriptionRoute")); // Register prescription routes
app.use("/api/doctorLeave", doctorLeaveRoutes); // Routes for Doctor Leave Management
app.use("/api/diagnosis", diagnosisRoute); // Routes for Diagnosis Management

// Forgot Password Routes
app.use("/api/auth/forgot-password", forgotPasswordRoute); // Routes for Forgot Password functionality

// Use Novelty Routes for analyzing symptoms
app.use("/api/novelty", noveltyRoutes); // This links the API to the Novelty Routes
app.use("/api/analysis", analysisRoutes);
app.use("/api/vitals", vitalsRoutes);

//Medical Report Routes
const medicalReportRoutes = require("./Routes/medicalReportRoutes");
app.use("/api/reports", medicalReportRoutes);

const path = require("path");
app.use("/uploads", express.static(path.join(__dirname, "uploads")));


// Database Connection
mongoose
  .connect(process.env.MONGO_URI || "mongodb://127.0.0.1:27017/mediflow")
  .then(() => {
    console.log("Connected to MongoDB");
    console.log("Database URL:", process.env.MONGO_URI || "mongodb://127.0.0.1:27017/mediflow");
    // Only start the server locally. Vercel manages the HTTP lifecycle.
    if (process.env.NODE_ENV !== "production") {
      const PORT = Number(process.env.PORT) || 5000;
      app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
      });
    }
  })
  .catch((err) => console.error("Database connection error:", err));

module.exports = app;

