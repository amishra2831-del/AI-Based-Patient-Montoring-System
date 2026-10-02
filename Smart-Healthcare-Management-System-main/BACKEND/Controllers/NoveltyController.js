const AI_API_URL =
  process.env.AI_API_URL || "https://health-ai-rust-two.vercel.app";

exports.analyzeSymptoms = async (req, res) => {
  try {
    const { symptoms } = req.body || {};

    if (!Array.isArray(symptoms) || symptoms.length === 0) {
      return res.status(400).json({
        message: "A non-empty symptoms array is required."
      });
    }

    const response = await fetch(
      `${AI_API_URL}/api/novelty/analyze`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          symptoms
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        message: "AI symptom analysis failed.",
        error: data
      });
    }

    return res.json(data);

  } catch (error) {
    console.error("AI API error:", error);

    return res.status(500).json({
      message: "AI symptom analysis failed.",
      error: error.message
    });
  }
};