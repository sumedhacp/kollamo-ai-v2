import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, MessageSquare, Youtube, BarChart3, Menu, X, Globe2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ApiStatusIndicator } from '@/components/ui/api-status';

export const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { path: '/', label: 'Home', icon: <Sparkles className="w-4 h-4" /> },
    { path: '/sandbox', label: 'Comment Sandbox', icon: <MessageSquare className="w-4 h-4" /> },
    { path: '/analyze', label: 'YouTube Analysis', icon: <Youtube className="w-4 h-4" /> },
    { path: '/dashboard', label: 'Audience Dashboard', icon: <BarChart3 className="w-4 h-4" /> },
  ];

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-brand-500 text-white shadow-sm shadow-brand-500/20 group-hover:scale-105 transition-transform">
              <Globe2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-lg text-slate-900 tracking-tight">Kollamo.ai</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                  MCA ML
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-none">Malayalam-English Sentiment & Intelligence</p>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={cn(
                  'flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors select-none',
                  isActive(link.path)
                    ? 'bg-brand-50 text-brand-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                )}
              >
                {link.icon}
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Quick CTA & API Status indicator */}
          <div className="hidden md:flex items-center gap-3">
            <ApiStatusIndicator />
            <Link
              to="/sandbox"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm font-medium rounded-lg text-white bg-slate-900 hover:bg-slate-800 transition-colors shadow-sm"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Try Sandbox
            </Link>
          </div>

          {/* Mobile menu trigger */}
          <div className="flex md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav Drawer */}
      {isOpen && (
        <div className="md:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setIsOpen(false)}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive(link.path)
                  ? 'bg-brand-50 text-brand-700 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              )}
            >
              {link.icon}
              {link.label}
            </Link>
          ))}
          <div className="pt-2 flex items-center justify-between gap-3">
            <ApiStatusIndicator />
            <Link
              to="/sandbox"
              onClick={() => setIsOpen(false)}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-lg text-white bg-slate-900 hover:bg-slate-800"
            >
              <MessageSquare className="w-4 h-4" />
              Try Sandbox
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
