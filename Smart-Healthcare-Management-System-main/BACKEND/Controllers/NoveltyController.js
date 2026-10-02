// URL of the deployed FastAPI AI service.
// Configure it in the backend environment, for example:
//   AI_API_URL=https://<your-ai-service-domain>
const AI_API_URL = (process.env.AI_API_URL || "").replace(/\/$/, "");

const AI_REQUEST_TIMEOUT_MS = Number(
  process.env.AI_REQUEST_TIMEOUT_MS || 20000
);

exports.analyzeSymptoms = async (req, res) => {
  const { symptoms } = req.body || {};

  if (!Array.isArray(symptoms) || symptoms.length === 0) {
    return res.status(400).json({
      message: "A non-empty symptoms array is required."
    });
  }

  if (!AI_API_URL) {
    console.error(
      "AI_API_URL is not configured on the backend."
    );

    return res.status(503).json({
      message: "AI symptom analysis is not configured.",
      error: "Set AI_API_URL on the backend environment."
    });
  }

  try {
    const response = await fetch(
      `${AI_API_URL}/api/novelty/analyze`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          symptoms
        }),
        signal: AbortSignal.timeout(AI_REQUEST_TIMEOUT_MS)
      }
    );

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      return res.status(response.status).json({
        message: "AI symptom analysis failed.",
        error: data
      });
    }

    return res.json(data);

  } catch (error) {
    console.error("AI API error:", error.message);

    return res.status(502).json({
      message: "AI symptom analysis failed.",
      error: error.message
    });
  }
};