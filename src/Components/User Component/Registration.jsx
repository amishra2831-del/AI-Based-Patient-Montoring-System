import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import Swal from "sweetalert2";

import {
  Box,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Container,
  Grid,
  Paper,
  IconButton,
  InputAdornment,
} from "@mui/material";

import {
  Visibility,
  VisibilityOff,
  EmailOutlined,
  LockOutlined,
  PersonOutlined,
} from "@mui/icons-material";

// ============================================================
// API CONFIGURATION
// ============================================================

// Supports both:
// VITE_API_URL=https://your-backend.vercel.app
// VITE_API_URL=https://your-backend.vercel.app/api

const ENV_API_URL = import.meta.env.VITE_API_URL || "";

const API_BASE_URL = ENV_API_URL
  .trim()
  .replace(/\/+$/, "")
  .replace(/\/api$/, "");

const REGISTER_URL = `${API_BASE_URL}/api/auth/register`;

// ============================================================
// VALIDATION REGEX
// ============================================================

const EMAIL_REGEX =
  /^[A-Za-z0-9._%+-]+@(gmail\.com|icloud\.com|outlook\.com)$/i;

// At least:
// - 8 characters
// - 1 letter
// - 1 number
// - 1 special character
const PASSWORD_REGEX =
  /^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;

// Letters, spaces and hyphens only
const NAME_REGEX = /^[A-Za-z]+(?:[A-Za-z\s-]*[A-Za-z])?$/;

// ============================================================
// COMPONENT
// ============================================================

function Registration() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [errors, setErrors] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [loading, setLoading] = useState(false);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // ============================================================
  // VALIDATE ONE FIELD
  // ============================================================

  const validateField = (name, value, currentFormData = formData) => {
    let error = "";

    switch (name) {
      // --------------------------------------------------------
      // NAME
      // --------------------------------------------------------

      case "name": {
        const trimmedName = value.trim();

        if (!trimmedName) {
          error = "Name is required";
        } else if (trimmedName.length < 2) {
          error = "Name must contain at least 2 characters";
        } else if (!NAME_REGEX.test(trimmedName)) {
          error = "Name can contain only letters, spaces and hyphens";
        }

        break;
      }

      // --------------------------------------------------------
      // EMAIL
      // --------------------------------------------------------

      case "email": {
        const email = value.trim();

        if (!email) {
          error = "Email is required";
        } else if (!EMAIL_REGEX.test(email)) {
          error =
            "Please enter a valid Gmail, iCloud or Outlook email address";
        }

        break;
      }

      // --------------------------------------------------------
      // PASSWORD
      // --------------------------------------------------------

      case "password": {
        if (!value) {
          error = "Password is required";
        } else if (value.length < 8) {
          error = "Password must contain at least 8 characters";
        } else if (!/[A-Za-z]/.test(value)) {
          error = "Password must contain at least one letter";
        } else if (!/\d/.test(value)) {
          error = "Password must contain at least one number";
        } else if (!/[^A-Za-z0-9]/.test(value)) {
          error = "Password must contain at least one special character";
        }

        break;
      }

      // --------------------------------------------------------
      // CONFIRM PASSWORD
      // --------------------------------------------------------

      case "confirmPassword": {
        if (!value) {
          error = "Please confirm your password";
        } else if (value !== currentFormData.password) {
          error = "Passwords do not match";
        }

        break;
      }

      default:
        break;
    }

    return error;
  };

  // ============================================================
  // VALIDATE COMPLETE FORM
  // ============================================================

  const validateForm = (data = formData) => {
    const newErrors = {
      name: validateField("name", data.name, data),
      email: validateField("email", data.email, data),
      password: validateField("password", data.password, data),
      confirmPassword: validateField(
        "confirmPassword",
        data.confirmPassword,
        data
      ),
    };

    setErrors(newErrors);

    return !Object.values(newErrors).some((error) => error !== "");
  };

  // ============================================================
  // HANDLE INPUT CHANGE
  // ============================================================

  const handleChange = (e) => {
    const { name, value } = e.target;

    const updatedFormData = {
      ...formData,
      [name]: value,
    };

    setFormData(updatedFormData);

    // Validate current field using UPDATED form data
    const fieldError = validateField(name, value, updatedFormData);

    setErrors((prev) => ({
      ...prev,
      [name]: fieldError,

      // If password changes, revalidate confirm password
      ...(name === "password"
        ? {
            confirmPassword: validateField(
              "confirmPassword",
              updatedFormData.confirmPassword,
              updatedFormData
            ),
          }
        : {}),
    }));
  };

  // ============================================================
  // HANDLE REGISTRATION
  // ============================================================

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prevent multiple clicks
    if (loading) {
      return;
    }

    // Validate using CURRENT form values
    const isValid = validateForm(formData);

    if (!isValid) {
      Swal.fire({
        icon: "warning",
        title: "Check your details",
        text: "Please correct the highlighted fields.",
        confirmButtonColor: "#1976d2",
      });

      return;
    }

    // Safety check
    if (!API_BASE_URL) {
      Swal.fire({
        icon: "error",
        title: "API URL is missing",
        text: "VITE_API_URL is not configured in the frontend environment variables.",
        confirmButtonColor: "#d32f2f",
      });

      return;
    }

    setLoading(true);

    const name = formData.name.trim();
    const email = formData.email.trim().toLowerCase();
    const password = formData.password;

    console.log("=================================");
    console.log("Registration request");
    console.log("API URL:", REGISTER_URL);
    console.log("Name:", name);
    console.log("Email:", email);
    console.log("=================================");

    try {
      const response = await axios.post(
        REGISTER_URL,
        {
          name,
          email,
          password,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },

          // Registration normally does not require cookies,
          // but this is compatible with a credentials-enabled backend.
          withCredentials: true,

          timeout: 15000,
        }
      );

      console.log("Registration response:", response.data);

      await Swal.fire({
        toast: true,
        position: "top-end",
        icon: "success",
        title: "🎉 Registration Successful",
        text: "Your account has been created.",
        showConfirmButton: false,
        timer: 2500,
        timerProgressBar: true,
        background: "#e6ffed",
        color: "#1e4620",
      });

      // Clear form
      setFormData({
        name: "",
        email: "",
        password: "",
        confirmPassword: "",
      });

      setErrors({
        name: "",
        email: "",
        password: "",
        confirmPassword: "",
      });

      navigate("/login");
    } catch (error) {
      console.error("Registration error:", error);

      // --------------------------------------------------------
      // SERVER RESPONSE
      // --------------------------------------------------------

      if (error.response) {
        console.error("Status:", error.response.status);
        console.error("Response:", error.response.data);

        const serverMessage =
          error.response.data?.message ||
          error.response.data?.error ||
          error.response.data?.msg;

        let message = serverMessage || "Registration failed.";

        if (error.response.status === 400) {
          message =
            serverMessage ||
            "The registration data is invalid or the email may already exist.";
        }

        if (error.response.status === 409) {
          message =
            serverMessage ||
            "An account with this email already exists.";
        }

        if (error.response.status === 404) {
          message =
            "Registration endpoint was not found. Check the backend API URL and route.";
        }

        if (error.response.status >= 500) {
          message =
            serverMessage ||
            "The backend server encountered an error. Check the backend logs.";
        }

        Swal.fire({
          icon: "error",
          title: "Registration Failed",
          text: message,
          confirmButtonColor: "#d32f2f",
        });

        return;
      }

      // --------------------------------------------------------
      // NETWORK ERROR
      // --------------------------------------------------------

      if (error.request) {
        console.error("No response received from backend.");

        Swal.fire({
          icon: "error",
          title: "Cannot connect to server",
          text:
            "The frontend could not reach the backend. Check VITE_API_URL, backend deployment, and CORS settings.",
          confirmButtonColor: "#d32f2f",
        });

        return;
      }

      // --------------------------------------------------------
      // OTHER ERROR
      // --------------------------------------------------------

      Swal.fire({
        icon: "error",
        title: "Registration Failed",
        text: error.message || "Something went wrong.",
        confirmButtonColor: "#d32f2f",
      });
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <Grid
          container
          spacing={4}
          alignItems="center"
          justifyContent="center"
        >
          {/* ==================================================
              LOGO SECTION
          ================================================== */}

          <Grid
            item
            xs={12}
            md={6}
            sx={{
              display: { xs: "none", md: "flex" },
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Box
              component="img"
              src="/Logo.png"
              alt="Medi Flow Logo"
              sx={{
                width: "auto",
                maxWidth: "80%",
                height: 200,
                objectFit: "contain",
              }}
            />
          </Grid>

          {/* ==================================================
              REGISTRATION FORM
          ================================================== */}

          <Grid item xs={12} md={6}>
            <Paper
              elevation={6}
              sx={{
                p: 4,
                borderRadius: 3,
                width: "100%",
                maxWidth: 420,
                mx: "auto",
                boxSizing: "border-box",
              }}
            >
              <Typography
                component="h1"
                variant="h4"
                sx={{
                  fontWeight: 700,
                  mb: 3,
                  textAlign: "center",
                  color: "#1976d2",
                }}
              >
                Create Account
              </Typography>

              <Box
                component="form"
                onSubmit={handleSubmit}
                noValidate
                sx={{ width: "100%" }}
              >
                {/* ==================================================
                    NAME
                ================================================== */}

                <TextField
                  fullWidth
                  margin="normal"
                  label="Full Name"
                  name="name"
                  placeholder="Enter your full name"
                  value={formData.name}
                  onChange={handleChange}
                  error={Boolean(errors.name)}
                  helperText={errors.name}
                  autoComplete="name"
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonOutlined color="action" />
                      </InputAdornment>
                    ),
                  }}
                />

                {/* ==================================================
                    EMAIL
                ================================================== */}

                <TextField
                  fullWidth
                  margin="normal"
                  label="Email"
                  name="email"
                  type="email"
                  placeholder="example@gmail.com"
                  value={formData.email}
                  onChange={handleChange}
                  error={Boolean(errors.email)}
                  helperText={errors.email}
                  autoComplete="email"
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <EmailOutlined color="action" />
                      </InputAdornment>
                    ),
                  }}
                />

                {/* ==================================================
                    PASSWORD
                ================================================== */}

                <TextField
                  fullWidth
                  margin="normal"
                  label="Password"
                  name="password"
                  placeholder="Minimum 8 characters with letter, number & symbol"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={handleChange}
                  error={Boolean(errors.password)}
                  helperText={
                    errors.password ||
                    "Use at least 8 characters, including a letter, number and symbol."
                  }
                  autoComplete="new-password"
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockOutlined color="action" />
                      </InputAdornment>
                    ),

                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          type="button"
                          onClick={() =>
                            setShowPassword((previous) => !previous)
                          }
                          edge="end"
                          disabled={loading}
                          aria-label={
                            showPassword
                              ? "Hide password"
                              : "Show password"
                          }
                        >
                          {showPassword ? (
                            <VisibilityOff />
                          ) : (
                            <Visibility />
                          )}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />

                {/* ==================================================
                    CONFIRM PASSWORD
                ================================================== */}

                <TextField
                  fullWidth
                  margin="normal"
                  label="Confirm Password"
                  name="confirmPassword"
                  placeholder="Re-enter your password"
                  type={showConfirmPassword ? "text" : "password"}
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  error={Boolean(errors.confirmPassword)}
                  helperText={errors.confirmPassword}
                  autoComplete="new-password"
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockOutlined color="action" />
                      </InputAdornment>
                    ),

                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          type="button"
                          onClick={() =>
                            setShowConfirmPassword((previous) => !previous)
                          }
                          edge="end"
                          disabled={loading}
                          aria-label={
                            showConfirmPassword
                              ? "Hide confirm password"
                              : "Show confirm password"
                          }
                        >
                          {showConfirmPassword ? (
                            <VisibilityOff />
                          ) : (
                            <Visibility />
                          )}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />

                {/* ==================================================
                    SUBMIT
                ================================================== */}

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  disabled={loading}
                  sx={{
                    mt: 3,
                    mb: 2,
                    minHeight: 48,
                    backgroundColor: "#1976d2",
                    "&:hover": {
                      backgroundColor: "#1565c0",
                    },
                  }}
                >
                  {loading ? (
                    <CircularProgress
                      size={24}
                      sx={{ color: "#fff" }}
                    />
                  ) : (
                    "Sign Up"
                  )}
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default Registration;