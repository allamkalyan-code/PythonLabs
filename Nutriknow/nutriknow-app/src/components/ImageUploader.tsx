"use client";
import React, { useState } from 'react';
import Image from 'next/image';

interface ImageUploaderProps {
  onImageUpload: (file: File) => void;
  isProcessing: boolean;
}

/**
 * Component for handling image upload and capture
 */
export const ImageUploader: React.FC<ImageUploaderProps> = ({ onImageUpload, isProcessing }) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onImageUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onImageUpload(e.target.files[0]);
    }
  };

  return (
    <label
      className={`w-full max-w-xl p-8 border-2 border-dashed rounded-lg text-center cursor-pointer block
        ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
        ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <div className="space-y-4">
        <div className="flex justify-center">
          <Image
            src="/upload-icon.svg"
            alt="Upload"
            width={64}
            height={64}
            className="opacity-50"
          />
        </div>
        <p className="text-lg">
          Drag and drop your nutrition label image here, or
          <span className="mx-2 text-blue-500 hover:text-blue-600 font-medium">
            browse
          </span>
        </p>
        <input
          type="file"
          className="hidden"
          accept="image/*"
          onChange={handleFileChange}
          disabled={isProcessing}
        />
        <p className="text-sm text-gray-500">
          Supports JPG, PNG - Max file size 5MB
        </p>
        {isProcessing && (
          <div className="mt-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-600">Processing image...</p>
          </div>
        )}
      </div>
    </label>
  );
};