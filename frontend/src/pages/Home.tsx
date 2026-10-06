import React from 'react';
import { Link } from 'react-router-dom';
import {
  MessageSquare,
  Youtube,
  BarChart3,
  Globe,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  FileText,
  Languages,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export const Home: React.FC = () => {
  return (
    <div className="space-y-20 pb-20">
      {/* 1. Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-12 md:pt-24 md:pb-20 border-b border-slate-200/60 bg-gradient-to-b from-white via-slate-50/50 to-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 border border-brand-200 text-brand-700 text-xs font-medium mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            <span>MCA Academic Research — Malayalam & Code-Mixed NLP</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
            Understand What Malayalam Audiences <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-indigo-500">Really Think</span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto font-normal leading-relaxed">
            Kollamo.ai turns raw Malayalam, Manglish, and code-mixed YouTube comments into clear sentiment insights and audience intelligence.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/sandbox">
              <Button size="lg" className="w-full sm:w-auto shadow-md">
                Try Comment Sandbox
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Link to="/analyze">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                <Youtube className="w-4 h-4 mr-2 text-rose-600" />
                Analyze a YouTube Video
              </Button>
            </Link>
          </div>

          {/* Quick trust metrics */}
          <div className="mt-12 pt-8 border-t border-slate-200/60 max-w-3xl mx-auto flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Malayalam Script (മലയാളം)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Manglish / Romanized Text</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>English & Code-Mixing</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Official YouTube API</span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. The Problem Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <Badge variant="secondary" className="mb-3">The Challenge</Badge>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
            Why Standard Sentiment Tools Fail on Regional Comments
          </h2>
          <p className="mt-3 text-slate-600 text-base">
            Standard sentiment tools assume pure English or formal text. But real Indian social media conversations are informal, highly code-mixed, and multi-script.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-slate-200">
            <CardContent className="pt-6">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 text-brand-600 flex items-center justify-center font-bold text-base mb-4">
                01
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Manglish & Spelling Variations</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Malayalam written in English letters lacks standard spelling (e.g., <em>adipoli</em>, <em>adhypoli</em>, <em>adypoly</em>). Generic NLP models misclassify these as typos or nonsense words.
              </p>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardContent className="pt-6">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 text-brand-600 flex items-center justify-center font-bold text-base mb-4">
                02
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Intense Code-Mixing</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Audiences blend English nouns with Malayalam verbs in the same sentence (e.g., <em>"Climax scene mass aayirunnu pakshe direction bore aayi"</em>), carrying both positive and negative polarity.
              </p>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardContent className="pt-6">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 text-brand-600 flex items-center justify-center font-bold text-base mb-4">
                03
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">High Volume & Slang</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Popular videos receive thousands of comments in hours. Analyzing audience reaction manually is impossible, and regional slang changes constantly.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* 3. Supported Languages */}
      <section className="bg-slate-100/70 py-16 border-y border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <Badge variant="secondary" className="mb-3">Linguistic Reach</Badge>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
              Supported Linguistic Forms
            </h2>
            <p className="mt-3 text-slate-600">
              Trained to parse and understand diverse scripts and linguistic blends seamlessly.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center gap-2 text-brand-600 mb-3">
                <Globe className="w-5 h-5" />
                <span className="font-semibold text-slate-900">Malayalam Script</span>
              </div>
              <p className="text-xs text-slate-500 mb-3">Native script with full morphological variation</p>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700 italic">
                "ഈ പടം തിയേറ്ററിൽ തന്നെ കാണണം, ഗംഭീര മേക്കിങ്!"
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center gap-2 text-brand-600 mb-3">
                <Languages className="w-5 h-5" />
                <span className="font-semibold text-slate-900">Manglish</span>
              </div>
              <p className="text-xs text-slate-500 mb-3">Romanized colloquial Malayalam</p>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700 italic">
                "Padam kidilam aayirunnu, must watch item!"
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center gap-2 text-brand-600 mb-3">
                <Sparkles className="w-5 h-5" />
                <span className="font-semibold text-slate-900">Code-Mixed</span>
              </div>
              <p className="text-xs text-slate-500 mb-3">Malayalam & English co-occurring clauses</p>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700 italic">
                "First half super entertaining, pakshe climax predictable aayi."
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center gap-2 text-brand-600 mb-3">
                <Globe className="w-5 h-5" />
                <span className="font-semibold text-slate-900">Standard English</span>
              </div>
              <p className="text-xs text-slate-500 mb-3">Global reactions and reviews</p>
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700 italic">
                "Outstanding performance by the entire cast!"
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Three-Step Workflow */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <Badge variant="secondary" className="mb-3">Simple Process</Badge>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
            How Kollamo.ai Works
          </h2>
          <p className="mt-3 text-slate-600">
            From single comment testing to batch YouTube audience intelligence in three straightforward steps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          <div className="flex flex-col items-center text-center p-6 bg-white rounded-2xl border border-slate-200 shadow-sm">
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-5 shadow-inner">
              <Youtube className="w-7 h-7 text-rose-600" />
            </div>
            <span className="text-xs font-bold text-brand-600 uppercase tracking-wider mb-1">Step 1</span>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Enter Video or Text</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Paste any YouTube video link or test single comments in our interactive sandbox. Choose sample sizes up to thousands of comments.
            </p>
          </div>

          <div className="flex flex-col items-center text-center p-6 bg-white rounded-2xl border border-slate-200 shadow-sm">
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-5 shadow-inner">
              <ShieldCheck className="w-7 h-7 text-brand-600" />
            </div>
            <span className="text-xs font-bold text-brand-600 uppercase tracking-wider mb-1">Step 2</span>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">MuRIL Classification</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Google MuRIL processes the text through neural embeddings, classifying comments into 5 sentiment categories without crude keyword lists.
            </p>
          </div>

          <div className="flex flex-col items-center text-center p-6 bg-white rounded-2xl border border-slate-200 shadow-sm">
            <div className="w-14 h-14 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center mb-5 shadow-inner">
              <BarChart3 className="w-7 h-7 text-emerald-600" />
            </div>
            <span className="text-xs font-bold text-brand-600 uppercase tracking-wider mb-1">Step 3</span>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Audience Intelligence & PDF</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Explore interactive sentiment distribution, like-engagement ratios, English translations, and download an executive PDF report.
            </p>
          </div>
        </div>
      </section>

      {/* 5. Call to Action */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl bg-gradient-to-r from-slate-900 to-brand-950 p-8 sm:p-12 text-center text-white shadow-xl">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Ready to Analyze Malayalam Comments?
          </h2>
          <p className="mt-4 text-base sm:text-lg text-slate-300 max-w-xl mx-auto">
            Test a comment right now in the sandbox or trigger video analysis to discover real audience sentiment.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/sandbox">
              <Button size="lg" className="w-full sm:w-auto bg-white text-slate-900 hover:bg-slate-100">
                <MessageSquare className="w-4 h-4 mr-2 text-brand-600" />
                Go to Sandbox
              </Button>
            </Link>
            <Link to="/analyze">
              <Button size="lg" variant="outline" className="w-full sm:w-auto text-white border-slate-700 hover:bg-slate-800">
                <FileText className="w-4 h-4 mr-2" />
                Explore Video Ingestion
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
