import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, BookOpen, Layers } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Col */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-slate-900 tracking-tight">Kollamo.ai</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium border border-slate-200">
                Academic MCA Research
              </span>
            </div>
            <p className="text-sm text-slate-600 max-w-md">
              Malayalam-English sentiment analysis and audience intelligence engine engineered for regional Dravidian social web interactions, code-mixed comments, and Manglish expressions.
            </p>
            <div className="flex items-center gap-3 text-xs text-slate-500 pt-2">
              <span className="inline-flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Google MuRIL Powered
              </span>
              <span>•</span>
              <span className="inline-flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-brand-600" />
                Official YouTube Data API v3
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <div>
            <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-3">Platform</h4>
            <ul className="space-y-2 text-sm text-slate-600">
              <li>
                <Link to="/" className="hover:text-brand-600 transition-colors">Home</Link>
              </li>
              <li>
                <Link to="/sandbox" className="hover:text-brand-600 transition-colors">Comment Sandbox</Link>
              </li>
              <li>
                <Link to="/analyze" className="hover:text-brand-600 transition-colors">YouTube Analysis</Link>
              </li>
              <li>
                <Link to="/dashboard" className="hover:text-brand-600 transition-colors">Audience Dashboard</Link>
              </li>
            </ul>
          </div>

          {/* Academic Notice */}
          <div>
            <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-3">Academic Note</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Developed as part of the MCA degree project. Ingests comments via YouTube Data API v3 within rate limits. Model outputs represent probabilistic sentiment estimates.
            </p>
            <div className="mt-3">
              <a
                href="https://huggingface.co/google/muril-base-cased"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-medium"
              >
                <BookOpen className="w-3.5 h-3.5" />
                MuRIL Documentation
              </a>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© {new Date().getFullYear()} Kollamo.ai. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <span>Version 0.2.0</span>
            <span>•</span>
            <span>WCAG 2.1 AA Compliant</span>
            <span>•</span>
            <span>Zero Fake Sentiment Guarantee</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
