import React from 'react';
import { X, ZoomIn, ZoomOut } from 'lucide-react';

interface ImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
  alt: string;
}

export default function ImageModal({ isOpen, onClose, imageUrl, alt }: ImageModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" onClick={onClose}>
      <div className="relative max-w-4xl max-h-[90vh] bg-[var(--card-bg)] p-2 rounded-xl shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="absolute -top-4 -right-4 p-2 bg-red-500 text-white rounded-full hover:bg-red-600">
          <X size={20} />
        </button>
        <img src={imageUrl} alt={alt} className="max-w-full max-h-[85vh] object-contain rounded-lg" referrerPolicy="no-referrer" />
      </div>
    </div>
  );
}
