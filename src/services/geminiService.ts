import { GoogleGenAI, GenerateContentResponse } from "@google/genai";

const API_KEY = process.env.GEMINI_API_KEY || "";
const ai = new GoogleGenAI({ apiKey: API_KEY });

/**
 * Handles Gemini API errors and returns a user-friendly message.
 */
function handleGeminiError(error: any): string {
  console.error("Gemini API Error:", error);

  if (!API_KEY) {
    return "Gemini API key is missing. Please check your environment variables.";
  }

  const message = error?.message?.toLowerCase() || "";

  if (message.includes("quota") || message.includes("429")) {
    return "API quota exceeded. Please try again later or upgrade your plan.";
  }

  if (message.includes("api key") || message.includes("401") || message.includes("403")) {
    return "Invalid or unauthorized API key. Please verify your credentials.";
  }

  if (message.includes("network") || message.includes("fetch")) {
    return "Network error. Please check your internet connection.";
  }

  if (message.includes("safety") || message.includes("blocked")) {
    return "The request was blocked by safety filters. Please try a different prompt.";
  }

  return `Gemini AI Error: ${error?.message || "An unexpected error occurred."}`;
}

export async function analyzeImage(base64Image: string, prompt: string) {
  try {
    // Extract mime type and clean base64 if it's a data URL
    let mimeType = "image/jpeg";
    let cleanBase64 = base64Image;

    if (base64Image.startsWith("data:")) {
      const match = base64Image.match(/^data:([^;]+);base64,(.*)$/);
      if (match) {
        mimeType = match[1];
        cleanBase64 = match[2];
      }
    } else if (base64Image.includes(",")) {
      // Fallback for partial data URLs
      const parts = base64Image.split(",");
      cleanBase64 = parts[1];
      const mimeMatch = parts[0].match(/:(.*?);/);
      if (mimeMatch) mimeType = mimeMatch[1];
    }

    const imagePart = {
      inlineData: {
        mimeType: mimeType,
        data: cleanBase64,
      },
    };
    const textPart = { text: prompt };
    
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: "gemini-flash-latest",
      contents: { parts: [imagePart, textPart] },
    });
    
    if (!response.text) {
      throw new Error("Empty response from Gemini AI.");
    }
    
    return response.text;
  } catch (error) {
    throw new Error(handleGeminiError(error));
  }
}

export async function getFastResponse(prompt: string) {
  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: "gemini-flash-latest",
      contents: { parts: [{ text: prompt }] },
    });
    
    if (!response.text) {
      throw new Error("Empty response from Gemini AI.");
    }
    
    return response.text;
  } catch (error) {
    throw new Error(handleGeminiError(error));
  }
}

export async function getComplexResponse(prompt: string) {
  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: "gemini-3.1-pro-preview",
      contents: { parts: [{ text: prompt }] },
    });
    
    if (!response.text) {
      throw new Error("Empty response from Gemini AI.");
    }
    
    return response.text;
  } catch (error) {
    throw new Error(handleGeminiError(error));
  }
}

export async function searchDatasetsWithAI(userRequest: string) {
  try {
    const prompt = `
      You are an expert in medical data science. Based on the user's request, suggest the best Kaggle dataset IDs for medical imaging.
      User Request: "${userRequest}"
      
      Return a JSON array of objects with the following structure:
      [
        {
          "id": "username/dataset-name",
          "reason": "Brief explanation why this is a good match",
          "estimatedSize": "e.g. 2GB",
          "confidence": 0.95
        }
      ]
      
      Only suggest real, high-quality Kaggle datasets. If you are unsure, suggest popular ones like 'nih-chest-xrays/data' or 'paultimothymooney/chest-xray-pneumonia'.
      Respond ONLY with the JSON array.
    `;

    const response: GenerateContentResponse = await ai.models.generateContent({
      model: "gemini-flash-latest",
      contents: { parts: [{ text: prompt }] },
      config: {
        responseMimeType: "application/json"
      }
    });

    if (!response.text) {
      throw new Error("Empty response from Gemini AI.");
    }

    return JSON.parse(response.text);
  } catch (error) {
    console.error("AI Search Error:", error);
    throw new Error(handleGeminiError(error));
  }
}
