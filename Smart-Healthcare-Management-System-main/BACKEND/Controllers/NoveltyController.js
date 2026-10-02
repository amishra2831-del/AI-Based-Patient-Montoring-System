const { spawn } = require("child_process");
const path = require("path");

exports.analyzeSymptoms = (req, res) => {
  const { symptoms } = req.body || {};

  if (!Array.isArray(symptoms) || symptoms.length === 0) {
    return res.status(400).json({ message: "A non-empty symptoms array is required." });
  }

  const scriptPath = path.join(__dirname, "../ai-model/model.py");
  const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";
  const python = spawn(pythonCommand, [scriptPath, JSON.stringify(symptoms)], {
    cwd: path.join(__dirname, "../ai-model"),
  });

  let result = "";
  let errorOutput = "";

  python.stdout.on("data", (data) => {
    result += data.toString();
  });

  python.stderr.on("data", (data) => {
    errorOutput += data.toString();
    console.error(`stderr: ${data}`);
  });

  python.on("close", (code) => {
    if (code !== 0) {
      return res.status(500).json({
        message: "AI symptom analysis failed.",
        error: errorOutput.trim() || `Python exited with code ${code}`,
      });
    }

    return res.json({ prediction: result.trim() || "No prediction returned." });
  });
};
