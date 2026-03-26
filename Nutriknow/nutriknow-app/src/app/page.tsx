'use client';

import { useState } from 'react';
import AnalysisService from '@/services/analysisService';
import { AnalysisResult } from '@/components/AnalysisResult';
import { FileUploadZone } from '@/components/FileUploadZone';
import { NutritionAnalysis } from '@/types/nutrition';
import { AlertCircle, Sparkles } from 'lucide-react';

export default function Home() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<NutritionAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
    setIsAnalyzing(true);
    setError(null);
    setAnalysis(null);

    // Create object URL for the image
    const imageUrl = URL.createObjectURL(file);
    setUploadedImageUrl(imageUrl);

    try {
      const result = await AnalysisService.processImage(file);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze image');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f5f5f7]">
      {/* Apple-style Navigation Bar */}
      <nav className="sticky top-0 z-50 glass-effect border-b border-gray-200/50">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-[#1d1d1f]">
              NutriKnow
            </h1>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-16 space-y-16">

        {/* Hero Section - Apple Style */}
        {!analysis && (
          <div className="text-center space-y-6 max-w-3xl mx-auto">
            <h2 className="text-5xl md:text-6xl font-semibold tracking-tight text-[#1d1d1f] leading-tight">
              Know what you eat.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-500 to-emerald-600">
                Live better.
              </span>
            </h2>
            <p className="text-xl text-[#86868b] font-normal leading-relaxed max-w-2xl mx-auto">
              Upload a nutrition label to get instant AI-powered insights.
              Discover hidden sugars, understand additives, and make smarter food choices.
            </p>
          </div>
        )}

        {/* Upload Zone */}
        {!analysis && (
          <div className="max-w-2xl mx-auto">
            <FileUploadZone onFileSelect={handleFileSelect} isAnalyzing={isAnalyzing} />
          </div>
        )}

        {/* Error Message - Apple Style */}
        {error && (
          <div className="max-w-2xl mx-auto">
            <div className="apple-card p-5 flex items-start gap-4 bg-red-50">
              <div className="w-6 h-6 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                <AlertCircle className="w-4 h-4 text-red-600" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-[#1d1d1f] text-sm mb-1">Analysis Failed</h4>
                <p className="text-sm text-[#86868b]">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Results Dashboard */}
        {analysis && (
          <div className="apple-fade-in">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-3xl font-semibold text-[#1d1d1f] tracking-tight">Your Analysis</h3>
              <button
                onClick={() => {
                  setAnalysis(null);
                  setUploadedImageUrl(null);
                }}
                className="apple-button bg-[#f5f5f7] hover:bg-[#e8e8ed] text-[#1d1d1f] text-sm"
              >
                Analyze Another
              </button>
            </div>
            <AnalysisResult analysis={analysis} uploadedImageUrl={uploadedImageUrl} />
          </div>
        )}

        {/* Footer - Apple Style */}
        <footer className="pt-20 pb-8 border-t border-[#d2d2d7]">
          <p className="text-center text-sm text-[#86868b]">
            Made with care for your health
          </p>
        </footer>
      </div>
    </main>
  );
}
