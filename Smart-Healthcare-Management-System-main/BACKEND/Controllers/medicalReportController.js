const MedicalReport = require("../Models/MedicalReport"); // Adjust the path as necessary
const fs = require("fs");
const path = require("path");
const { UPLOAD_DIR } = require("../Middleware/upload");

exports.uploadReport = async (req, res) => {
  try {
    const newReport = new MedicalReport({
      userId: req.user.id,
      fileName: req.file.originalname,
      // Stored relative to the uploads root so the public download URL
      // stays <backend>/uploads/<filename> regardless of where the server
      // process runs or which filesystem is writable.
      filePath: `uploads/${req.file.filename}`,
      fileType: req.file.mimetype,
    });
    await newReport.save();
    res.status(201).json(newReport);
  } catch (err) {
    res.status(500).json({ message: "Upload failed", error: err.message });
  }
};

exports.getUserReports = async (req, res) => {
  try {
    const reports = await MedicalReport.find({ userId: req.user.id });
    res.status(200).json(reports);
  } catch (err) {
    res.status(500).json({ message: "Failed to fetch reports", error: err.message });
  }
};

exports.deleteReport = async (req, res) => {
  try {
    const report = await MedicalReport.findById(req.params.id);
    if (!report) return res.status(404).json({ message: "Report not found" });

    const absolutePath = path.join(
      UPLOAD_DIR,
      path.basename(report.filePath)
    );

    if (fs.existsSync(absolutePath)) {
      fs.unlinkSync(absolutePath);
    }

    await report.deleteOne();
    res.status(200).json({ message: "Report deleted" });
  } catch (err) {
    res.status(500).json({ message: "Failed to delete report", error: err.message });
  }
};