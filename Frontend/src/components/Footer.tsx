import React from 'react';
import { Github, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="bg-[#0A0D1A] pt-16 pb-8 border-t border-[#1E2A45]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Top Section - 4 Columns */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
          
          {/* Column 1: Brand */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <svg
                width="24"
                height="24"
                viewBox="0 0 32 32"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-[#3B82F6]"
              >
                <rect width="32" height="32" rx="8" fill="#3B82F6" fillOpacity="0.1" />
                <path
                  d="M6 16H11L14 8L18 24L21 16H26"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span className="text-xl font-bold tracking-tight text-[#F1F5F9]">
                ChurnSight
              </span>
            </div>
            <p className="text-sm text-[#64748B] leading-relaxed">
              Customer Data Into Retention Intelligence.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-[#0F1629] border border-[#1E2A45] rounded-md mt-2 w-max text-xs font-mono text-[#8B5CF6]">
              <span className="w-2 h-2 rounded-full bg-[#10B981]"></span>
              Built with Phase 1–8 pipeline
            </div>
          </div>

          {/* Column 2: Platform Links — uses real routes */}
          <div>
            <h4 className="text-[#F1F5F9] font-semibold mb-4 uppercase text-xs tracking-wider">Platform</h4>
            <ul className="space-y-3">
              <li><Link to="/demo" className="text-sm text-[#64748B] hover:text-[#3B82F6] transition-colors">Demo Workspace</Link></li>
              <li><Link to="/upload" className="text-sm text-[#64748B] hover:text-[#3B82F6] transition-colors">Upload Dataset</Link></li>
              <li><Link to="/demo/model" className="text-sm text-[#64748B] hover:text-[#3B82F6] transition-colors">Model & XAI</Link></li>
              <li><Link to="/demo/dashboard" className="text-sm text-[#64748B] hover:text-[#3B82F6] transition-colors">Dashboard</Link></li>
            </ul>
          </div>

          {/* Column 3: Tech Stack */}
          <div>
            <h4 className="text-[#F1F5F9] font-semibold mb-4 uppercase text-xs tracking-wider">Tech Stack</h4>
            <ul className="space-y-3 font-mono text-sm text-[#64748B]">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#3B82F6]" /> FastAPI
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#10B981]" /> XGBoost
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" /> SHAP
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#8B5CF6]" /> LangChain
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#EF4444]" /> PostgreSQL
              </li>
            </ul>
          </div>

          {/* Column 4: Dataset Info */}
          <div>
            <h4 className="text-[#F1F5F9] font-semibold mb-4 uppercase text-xs tracking-wider">Dataset Context</h4>
            <div className="bg-[#0F1629] border border-[#1E2A45] p-4 rounded-lg">
              <p className="text-sm text-[#64748B] leading-relaxed">
                Trained on a normalized internal dataset encompassing <strong className="text-[#F1F5F9]">500K synthetic SaaS customers</strong> over <strong className="text-[#F1F5F9]">12 trailing months</strong>.
              </p>
              <div className="mt-3 pt-3 border-t border-[#1E2A45] flex items-center justify-between text-xs text-[#64748B] font-mono">
                <span>Update Freq:</span>
                <span className="text-[#10B981]">Daily (CRON)</span>
              </div>
            </div>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-[#1E2A45] flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-[#64748B] font-mono">
            v2.0 &middot; March 2026
          </p>
          <div className="flex items-center gap-6">
            <a
              href="https://github.com/Faraazz05/churn-forensics"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-[#64748B] hover:text-[#3B82F6] transition-colors group"
            >
              <Github className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span>GitHub</span>
            </a>
            <a
              href="https://faraazz05.github.io"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-[#64748B] hover:text-[#8B5CF6] transition-colors group"
            >
              <Globe className="w-4 h-4 group-hover:scale-110 transition-transform" />
              <span>Portfolio</span>
            </a>
          </div>
          <p className="text-xs text-[#64748B]">
            Released under MIT License.
          </p>
        </div>

      </div>
    </footer>
  );
}
