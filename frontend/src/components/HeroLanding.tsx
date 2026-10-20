import React from 'react';
import { ArrowDown, Gauge, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react';

interface HeroLandingProps {
  onExploreClick: () => void;
}

export const HeroLanding: React.FC<HeroLandingProps> = ({ onExploreClick }) => {
  return (
    <section className="bg-nero text-san pt-12 pb-16 px-4 sm:px-6 lg:px-8 border-b border-nero-700 relative overflow-hidden">
      {/* Decorative background grid */}
      <div className="absolute inset-0 opacity-5 pointer-events-none bg-[radial-gradient(#FD5323_1px,transparent_1px)] [background-size:16px_16px]"></div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Eyebrow */}
        <div className="inline-flex items-center space-x-2 bg-nero-800 border border-nero-700 px-3 py-1.5 rounded-full text-xs font-mono text-orange mb-6">
          <span className="w-2 h-2 rounded-full bg-orange animate-ping"></span>
          <span>ROUTEDESK MLOPS V1.1 • DUAL-HEAD INFERENCE ENGINE</span>
        </div>

        {/* Headline */}
        <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white max-w-4xl font-sans leading-[1.1]">
          Autonomous IT Support Routing with Zero-Risk Human Triage.
        </h1>

        {/* Subhead */}
        <p className="mt-5 text-base sm:text-lg text-muted-dark max-w-2xl font-sans leading-relaxed">
          Classify resolver teams, SLA urgency, and priority in under 30 milliseconds.
          High-confidence tickets route instantly; multi-issue or ambiguous tickets divert to service desk triage with automated retraining loops.
        </p>

        {/* CTAs */}
        <div className="mt-8 flex flex-wrap gap-4 items-center">
          <button
            type="button"
            onClick={onExploreClick}
            className="bg-orange hover:bg-orange/90 text-nero font-bold font-sans px-6 py-3 rounded-card text-sm flex items-center space-x-2 shadow-lg transition-all"
          >
            <span>Test Live Ticket Intake</span>
            <ArrowDown className="w-4 h-4" />
          </button>
          <div className="text-xs text-muted-dark font-mono flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-status-success"></span>
            <span>Production Champion: <strong className="text-white">v1-baseline</strong> (Active)</span>
          </div>
        </div>

        {/* Key Metrics Strip */}
        <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 border-t border-nero-700 pt-8">
          <div className="bg-nero-800/80 p-4 rounded-card border border-nero-700">
            <div className="flex items-center space-x-2 text-xs font-mono text-orange mb-1">
              <ShieldCheck className="w-4 h-4" />
              <span>Auto Accuracy</span>
            </div>
            <span className="text-2xl sm:text-3xl font-bold text-white font-mono">95.8%</span>
            <span className="text-[11px] text-muted-dark block mt-1">Exceeds 90% SLA Target</span>
          </div>

          <div className="bg-nero-800/80 p-4 rounded-card border border-nero-700">
            <div className="flex items-center space-x-2 text-xs font-mono text-orange mb-1">
              <TrendingUp className="w-4 h-4" />
              <span>Automation Rate</span>
            </div>
            <span className="text-2xl sm:text-3xl font-bold text-white font-mono">61.1%</span>
            <span className="text-[11px] text-muted-dark block mt-1">At optimal threshold τ*=0.69</span>
          </div>

          <div className="bg-nero-800/80 p-4 rounded-card border border-nero-700">
            <div className="flex items-center space-x-2 text-xs font-mono text-orange mb-1">
              <Sparkles className="w-4 h-4" />
              <span>Net Agent Savings</span>
            </div>
            <span className="text-2xl sm:text-3xl font-bold text-white font-mono">120.7</span>
            <span className="text-[11px] text-muted-dark block mt-1">Hours saved / month</span>
          </div>

          <div className="bg-nero-800/80 p-4 rounded-card border border-nero-700">
            <div className="flex items-center space-x-2 text-xs font-mono text-orange mb-1">
              <Gauge className="w-4 h-4" />
              <span>P95 API Latency</span>
            </div>
            <span className="text-2xl sm:text-3xl font-bold text-white font-mono">29.2 ms</span>
            <span className="text-[11px] text-muted-dark block mt-1">Under 300ms budget</span>
          </div>
        </div>
      </div>
    </section>
  );
};
