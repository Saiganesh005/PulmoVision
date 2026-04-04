import React, { useState } from 'react';
import { Upload, X, Microscope } from 'lucide-react';

interface TestingPageProps {
  setUploadedImage: (img: string | null) => void;
  setActivePage: (page: string) => void;
}

export default function TestingPage({ setUploadedImage, setActivePage }: TestingPageProps) {
  const [preview, setPreview] = useState<string | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleScan = () => {
    if (preview) {
      setUploadedImage(preview);
      setActivePage('Analysis');
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-[var(--text-color)]">Testing Module</h1>
      <div className="border-2 border-dashed border-[var(--primary-color)] rounded-2xl p-8 text-center bg-[var(--bg-color)]">
        {!preview ? (
          <label className="cursor-pointer flex flex-col items-center gap-4">
            <div className="p-6 bg-[var(--primary-color)]/10 rounded-full">
              <Upload size={48} className="text-[var(--primary-color)]" />
            </div>
            <span className="font-bold text-[var(--text-color)]">Upload X-ray Image</span>
            <input type="file" className="hidden" accept="image/*" onChange={handleFileUpload} />
          </label>
        ) : (
          <div className="space-y-4">
            <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-xl border-2 border-[var(--primary-color)]" />
            <div className="flex justify-center gap-4">
              <button onClick={() => setPreview(null)} className="px-4 py-2 bg-red-500 text-white rounded-lg font-bold">Remove</button>
              <button onClick={handleScan} className="px-4 py-2 bg-[var(--primary-color)] text-[var(--bg-color)] rounded-lg font-bold flex items-center gap-2">
                <Microscope size={18} /> Scan Image
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
