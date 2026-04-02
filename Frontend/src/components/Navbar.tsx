import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface NavbarProps {
  onDemoClick: () => void;
  onAnalysisClick: () => void;
}

export function Navbar({ onDemoClick, onAnalysisClick }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 60);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 w-full z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-[#0A0D1A]/85 backdrop-blur-md border-b border-[#1E2A45] py-3'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <svg
              width="32"
              height="32"
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

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-6">
            <a
              href="#docs"
              className="text-sm font-medium text-[#64748B] hover:text-[#F1F5F9] transition-colors"
            >
              Documentation
            </a>
            <a
              href="#github"
              className="text-sm font-medium text-[#64748B] hover:text-[#F1F5F9] transition-colors"
            >
              GitHub
            </a>
            <div className="flex items-center gap-3 ml-2">
              <button
                onClick={onAnalysisClick}
                className="px-4 py-2 text-sm font-medium text-[#8B5CF6] border border-[#8B5CF6]/50 rounded-lg hover:bg-[#8B5CF6]/10 transition-colors"
              >
                Start Analysis
              </button>
              <button
                onClick={onDemoClick}
                className="px-4 py-2 text-sm font-medium text-[#F1F5F9] bg-[#3B82F6] rounded-lg hover:bg-[#2563EB] hover:scale-105 transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)]"
              >
                View Demo
              </button>
            </div>
          </div>

          {/* Mobile Menu Toggle */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-[#64748B] hover:text-[#F1F5F9] focus:outline-none"
              aria-label="Toggle menu"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md:hidden absolute top-full left-0 w-full bg-[#0F1629] border-b border-[#1E2A45] shadow-xl"
          >
            <div className="flex flex-col px-4 py-6 gap-4">
              <a href="#docs" className="text-sm font-medium text-[#64748B] hover:text-[#F1F5F9]">
                Documentation
              </a>
              <a href="#github" className="text-sm font-medium text-[#64748B] hover:text-[#F1F5F9]">
                GitHub
              </a>
              <div className="h-px w-full bg-[#1E2A45] my-2" />
              <button
                onClick={onAnalysisClick}
                className="w-full text-center px-4 py-2 text-sm font-medium text-[#8B5CF6] border border-[#8B5CF6]/50 rounded-lg"
              >
                Start Analysis
              </button>
              <button
                onClick={onDemoClick}
                className="w-full text-center px-4 py-2 text-sm font-medium text-[#F1F5F9] bg-[#3B82F6] rounded-lg shadow-[0_0_20px_rgba(59,130,246,0.2)]"
              >
                View Demo
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
