import React, { useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Image as ImageIcon, Loader2 } from 'lucide-react';

interface FileUploadZoneProps {
    onFileSelect: (file: File) => void;
    isAnalyzing: boolean;
}

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({ onFileSelect, isAnalyzing }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [preview, setPreview] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    const handleFile = (file: File) => {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                setPreview(e.target?.result as string);
            };
            reader.readAsDataURL(file);
            onFileSelect(file);
        }
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <div className="w-full">
            <AnimatePresence mode="wait">
                {!isAnalyzing ? (
                    <motion.div
                        key="upload"
                        initial={{ opacity: 0, scale: 0.96 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.96 }}
                        transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
                        className={`
              relative overflow-hidden transition-all duration-300 cursor-pointer
              ${isDragging
                                ? 'apple-card-elevated bg-green-50 border-2 border-green-400 scale-[1.02]'
                                : 'apple-card bg-white border-2 border-transparent hover:border-gray-200'
                            }
            `}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={handleClick}
                        style={{ padding: '48px', minHeight: '320px' }}
                    >
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden"
                            accept="image/*"
                            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                        />

                        <div className="flex flex-col items-center justify-center text-center space-y-6">
                            {/* Icon */}
                            <div className={`
                w-20 h-20 rounded-3xl flex items-center justify-center transition-all duration-300
                ${isDragging ? 'bg-green-100 scale-110' : 'bg-gray-100'}
              `}>
                                <Upload className={`
                  w-10 h-10 transition-colors duration-300
                  ${isDragging ? 'text-green-600' : 'text-gray-400'}
                `} />
                            </div>

                            {/* Text */}
                            <div className="space-y-2">
                                <h3 className="text-xl font-semibold text-[#1d1d1f] tracking-tight">
                                    {isDragging ? 'Drop to analyze' : 'Upload nutrition label'}
                                </h3>
                                <p className="text-sm text-[#86868b] max-w-sm">
                                    Drag and drop an image, or click to browse
                                </p>
                                <p className="text-xs text-[#86868b] pt-2">
                                    Supports JPG, PNG, WebP
                                </p>
                            </div>

                            {/* Button */}
                            <button className="apple-button bg-[#06c] hover:bg-[#0077ed] text-white mt-4 shadow-md">
                                Choose File
                            </button>
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        key="analyzing"
                        initial={{ opacity: 0, scale: 0.96 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="apple-card-elevated overflow-hidden"
                        style={{ minHeight: '320px' }}
                    >
                        {/* Background with preview */}
                        {preview && (
                            <div
                                className="absolute inset-0 opacity-10 blur-2xl"
                                style={{
                                    backgroundImage: `url(${preview})`,
                                    backgroundSize: 'cover',
                                    backgroundPosition: 'center'
                                }}
                            />
                        )}

                        {/* Content */}
                        <div className="relative flex flex-col items-center justify-center h-80 p-12 text-center">
                            <div className="w-20 h-20 rounded-3xl bg-white/80 backdrop-blur-xl flex items-center justify-center mb-6">
                                <ImageIcon className="w-10 h-10 text-green-600" />
                            </div>

                            <h3 className="text-xl font-semibold text-[#1d1d1f] mb-3 tracking-tight">
                                Analyzing your label
                            </h3>

                            <div className="flex items-center space-x-2 text-[#86868b]">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span className="text-sm">Reading nutrition facts...</span>
                            </div>

                            {/* Progress bar */}
                            <div className="w-64 h-1 bg-gray-200 rounded-full mt-6 overflow-hidden">
                                <motion.div
                                    className="h-full bg-green-500 rounded-full"
                                    animate={{ x: ['-100%', '100%'] }}
                                    transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                                    style={{ width: '40%' }}
                                />
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
