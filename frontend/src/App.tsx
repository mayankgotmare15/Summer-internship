import { useRef, useState } from 'react';
import { HeroLanding } from './components/HeroLanding';
import { HumanReviewQueue } from './components/HumanReviewQueue';
import { Navbar } from './components/Navbar';
import { PredictionPanel } from './components/PredictionPanel';
import { RaiseTicketForm } from './components/RaiseTicketForm';
import { demoLogin } from './services/api';
import type { PredictionOut, UserProfile } from './types';

const INITIAL_USER: UserProfile = {
  id: 'usr-demo-req',
  email: 'requester@example.com',
  name: 'Aarav Patel (Requester)',
  role: 'requester',
  department: 'Product & Engineering',
  is_demo: true,
};

export function App() {
  const [currentUser, setCurrentUser] = useState<UserProfile>(INITIAL_USER);
  const [activeTab, setActiveTab] = useState<'intake' | 'triage' | 'health'>('intake');
  const [prediction, setPrediction] = useState<PredictionOut | null>(null);
  const [loading, setLoading] = useState(false);

  const intakeRef = useRef<HTMLDivElement>(null);

  const handleRoleSelect = async (role: string) => {
    try {
      const user = await demoLogin(role);
      setCurrentUser(user);
      if (role === 'agent') {
        setActiveTab('triage');
      } else {
        setActiveTab('intake');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const scrollToExplore = () => {
    intakeRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-san/30 text-ink flex flex-col font-sans">
      {/* Navbar with Role Switcher */}
      <Navbar
        currentUser={currentUser}
        onSelectRole={handleRoleSelect}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Hero Section */}
      <HeroLanding onExploreClick={scrollToExplore} />

      {/* Main Content Workspace */}
      <main ref={intakeRef} id="intake-workspace" className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {activeTab === 'intake' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-line-light pb-4">
              <div>
                <h2 className="text-xl font-bold text-ink">Interactive Ticket Intake &amp; Classification</h2>
                <p className="text-xs text-muted-light">
                  Active Persona: <strong className="text-ink">{currentUser.name}</strong> • Role: <span className="uppercase font-mono font-bold text-orange">{currentUser.role}</span>
                </p>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono text-muted-light">
                <span className="w-2 h-2 rounded-full bg-status-success"></span>
                <span>Inference API Connected</span>
              </div>
            </div>

            {/* Split Grid: Raise Form Left, Live Prediction Right */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              <div className="lg:col-span-7">
                <RaiseTicketForm
                  onPredictionChange={setPrediction}
                  onLoadingChange={setLoading}
                />
              </div>

              <div className="lg:col-span-5 sticky top-20">
                <PredictionPanel prediction={prediction} loading={loading} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'triage' && (
          <div className="bg-paper border border-line-light rounded-panel p-6 shadow-card">
            <HumanReviewQueue />
          </div>
        )}
      </main>

      {/* Production Footer */}
      <footer className="bg-nero text-san border-t border-nero-700 py-8 px-4 text-xs font-mono text-center space-y-2 mt-auto">
        <p className="text-muted-dark">
          RouteDesk IT Support Auto-Routing System • 1-Month MLOps Production Stack
        </p>
        <div className="flex justify-center space-x-6 text-orange">
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="hover:underline">
            FastAPI Swagger Docs (8000)
          </a>
          <span>•</span>
          <a href="http://localhost:8501" target="_blank" rel="noreferrer" className="hover:underline">
            Streamlit ML Admin Console (8501)
          </a>
          <span>•</span>
          <span>Docker Bake: champion:v1-baseline</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
