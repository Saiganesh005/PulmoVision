import React, { useState } from 'react';
import { GoogleGenAI } from "@google/genai";
import { Sparkles, RefreshCw, ImageIcon } from 'lucide-react';

declare global {
  interface Window {
    aistudio: {
      hasSelectedApiKey: () => Promise<boolean>;
      openSelectKey: () => Promise<void>;
    };
  }
}

export default function ImageGenerator() {
  const [prompt, setPrompt] = useState('');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const aspectRatios = ['1:1', '2:3', '3:2', '3:4', '4:3', '9:16', '16:9', '21:9'];

  const handleGenerate = async () => {
    if (!prompt) return;
    
    // Check if API key is selected
    if (!(await window.aistudio.hasSelectedApiKey())) {
      await window.aistudio.openSelectKey();
      // Assume key selection was successful
    }

    setIsGenerating(true);
    setError(null);
    setGeneratedImage(null);

    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });
      const response = await ai.models.generateContent({
        model: 'gemini-3-pro-image-preview',
        contents: { parts: [{ text: prompt }] },
        config: {
          imageConfig: { aspectRatio },
        },
      });

      let foundImage = false;
      for (const part of response.candidates[0].content.parts) {
        if (part.inlineData) {
          setGeneratedImage(`data:image/png;base64,${part.inlineData.data}`);
          foundImage = true;
          break;
        }
      }
      if (!foundImage) {
        setError("No image generated.");
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to generate image.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6 p-6 bg-[var(--card-bg)] rounded-2xl border border-[var(--primary-color)]/20">
      <h3 className="text-lg font-bold flex items-center gap-2">
        <Sparkles className="text-[var(--primary-color)]" />
        AI Image Generator
      </h3>
      
      <div className="space-y-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to generate..."
          className="w-full p-3 rounded-xl bg-[var(--bg-color)] border border-[var(--primary-color)]/20 focus:border-[var(--primary-color)] outline-none transition-all text-sm"
          rows={3}
        />
        
        <div className="flex items-center gap-4">
          <label className="text-sm font-bold text-[var(--secondary-text)]">Aspect Ratio:</label>
          <select 
            value={aspectRatio}
            onChange={(e) => setAspectRatio(e.target.value)}
            className="p-2 rounded-lg bg-[var(--bg-color)] border border-[var(--primary-color)]/20 outline-none"
          >
            {aspectRatios.map(ar => <option key={ar} value={ar}>{ar}</option>)}
          </select>
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt}
          className="w-full py-3 bg-[var(--primary-color)] text-[var(--bg-color)] rounded-xl font-bold hover:opacity-90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isGenerating ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} />}
          {isGenerating ? 'Generating...' : 'Generate Image'}
        </button>
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {generatedImage && (
        <div className="mt-6">
          <img src={generatedImage} alt="Generated" className="w-full rounded-xl border-2 border-[var(--primary-color)] shadow-lg" />
        </div>
      )}
    </div>
  );
}
