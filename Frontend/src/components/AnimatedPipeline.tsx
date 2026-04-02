import React, { useState } from 'react';
import { motion } from 'framer-motion';

const NODES = [
  { id: 'data', label: 'Data', x: 10, y: 50, desc: 'Ingestion & Cleaning' },
  { id: 'features', label: 'Features', x: 25, y: 30, desc: 'Feature Engineering' },
  { id: 'model', label: 'Model', x: 40, y: 70, desc: 'XGBoost Prediction' },
  { id: 'xai', label: 'XAI', x: 55, y: 50, desc: 'Explainability Consensus' },
  { id: 'segments', label: 'Segments', x: 70, y: 30, desc: 'Degradation Tracking' },
  { id: 'drift', label: 'Drift', x: 80, y: 65, desc: 'PSI & KS-Test Signals' },
  { id: 'insights', label: 'Insights', x: 90, y: 40, desc: 'LLM Narrative Gen' },
  { id: 'actions', label: 'Actions', x: 100, y: 50, desc: 'RL Interventions' },
];

export function AnimatedPipeline() {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // SVG Path to connect nodes
  const pathData = `M 10 50 C 15 50, 20 30, 25 30 S 35 70, 40 70 S 50 50, 55 50 S 65 30, 70 30 S 75 65, 80 65 S 85 40, 90 40 S 95 50, 100 50`;

  return (
    <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden flex items-center justify-center opacity-30">
      <svg
        viewBox="0 0 110 100"
        className="w-full h-full max-h-[800px] pointer-events-auto"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.1" />
            <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.1" />
          </linearGradient>
          
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Base connection path */}
        <path
          d={pathData}
          fill="none"
          stroke="url(#lineGrad)"
          strokeWidth="0.5"
          className="opacity-50"
        />

        {/* Animated flow lines */}
        <motion.path
          d={pathData}
          fill="none"
          stroke="#8B5CF6"
          strokeWidth="0.8"
          strokeDasharray="4 8"
          initial={{ pathLength: 1, strokeDashoffset: 0 }}
          animate={{ strokeDashoffset: -120 }}
          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
          className="opacity-60"
        />

        {/* Nodes */}
        {NODES.map((node) => {
          const isHovered = hoveredNode === node.id;
          return (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              className="cursor-pointer transition-opacity duration-300"
              style={{ opacity: hoveredNode && !isHovered ? 0.2 : (isHovered ? 1 : 0.4) }}
            >
              <circle
                r="3"
                fill="#0F1629"
                stroke={isHovered ? '#3B82F6' : '#1E2A45'}
                strokeWidth="1"
                filter={isHovered ? 'url(#glow)' : ''}
              />
              <circle r="1" fill="#3B82F6" />
              
              {/* Internal SVG Icon geometry based on simple shapes */}
              <rect x="-1" y="-1" width="2" height="2" fill="none" stroke="#F1F5F9" strokeWidth="0.2" className="opacity-50" />

              {/* Tooltip visible on hover */}
              {isHovered && (
                <g transform="translate(0, -8)">
                  <rect
                    x="-15"
                    y="-6"
                    width="30"
                    height="5"
                    rx="1"
                    fill="#0A0D1A"
                    stroke="#1E2A45"
                    strokeWidth="0.2"
                  />
                  <text
                    x="0"
                    y="-2.5"
                    textAnchor="middle"
                    fill="#F1F5F9"
                    fontSize="1.5"
                    fontFamily="Inter, sans-serif"
                    fontWeight="500"
                  >
                    {node.label}
                  </text>
                  <text
                     x="0"
                     y="-1"
                     textAnchor="middle"
                     fill="#64748B"
                     fontSize="1"
                     fontFamily="Inter, sans-serif"
                  >
                    {node.desc}
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
