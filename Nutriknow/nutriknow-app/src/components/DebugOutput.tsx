"use client";
import { useState } from 'react';

interface DebugOutputProps {
  visionRawText?: string;
  explanationRawText?: string;
}

export function DebugOutput({ visionRawText, explanationRawText }: DebugOutputProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Only show in development
  if (process.env.NODE_ENV === 'production' || (!visionRawText && !explanationRawText)) {
    return null;
  }

  return (
    <div className="mt-8 border border-gray-200 rounded-lg p-4 bg-gray-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
      >
        <svg
          className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-90' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
        Debug Output
      </button>

      {isOpen && (
        <div className="mt-4 space-y-4">
          {visionRawText && (
            <div>
              <h4 className="font-medium text-sm text-gray-700 mb-2">Vision Model Raw Output:</h4>
              <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto">
                {visionRawText}
              </pre>
            </div>
          )}
          {explanationRawText && (
            <div>
              <h4 className="font-medium text-sm text-gray-700 mb-2">Explanation Model Raw Output:</h4>
              <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto">
                {explanationRawText}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}