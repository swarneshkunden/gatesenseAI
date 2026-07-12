import React, { useState, useEffect } from 'react';
import {
  Activity,
  ShieldAlert,
  Languages,
  Megaphone,
  Settings2,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  RefreshCw,
  Volume2,
  ArrowRight,
  FileSpreadsheet,
  Play,
  UserCheck
} from 'lucide-react';

interface Zone {
  zone_id: string;
  occupancy_rate: number;
  throughput_rate: number;
  status: string;
}

interface AnalysisResult {
  alerts: string[];
  instructions: string;
  is_mock?: boolean;
}

interface TranslationResult {
  detected_language: string;
  fan_text_en: string;
  urgency_analysis: string;
  suggested_response_en: string;
  suggested_response_fan_lang: string;
  is_mock?: boolean;
}

interface ScriptResult {
  scenario: string;
  broadcast_scripts: Record<string, string>;
  is_mock?: boolean;
}

const BACKEND_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const SCENARIOS = [
  {
    title: "Gate D Saturation - Redirect to C",
    text: "Gate D has reached maximum capacity. All arriving fans are being rerouted to Gate C, which is currently clear."
  },
  {
    title: "Gate B Closure",
    text: "Gate B is temporarily closed due to operations inspection. Please use Gate A for stadium entry."
  },
  {
    title: "Weather Storm Alert",
    text: "Heavy rainfall is approaching. Please enter the covered concourses immediately. Stand clear of wet stairs."
  },
  {
    title: "Metro Post-Match Exit Flow",
    text: "The main metro station is crowded. Shuttle buses to Central Station are departing from Transit Hub A every 3 minutes."
  }
];

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'translation' | 'broadcast' | 'simulator'>('dashboard');
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // AI Reasoning State
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [analyzeThreshold, setAnalyzeThreshold] = useState<number>(80);

  // Translation State
  const [fanText, setFanText] = useState<string>('');
  const [fanLanguage, setFanLanguage] = useState<string>('Auto');
  const [fanOrigin, setFanOrigin] = useState<string>('Unknown');
  const [urgencyLevel, setUrgencyLevel] = useState<string>('casual');
  const [stressLevel, setStressLevel] = useState<string>('calm');
  const [translationResult, setTranslationResult] = useState<TranslationResult | null>(null);

  // Broadcast Script State
  const [customScenario, setCustomScenario] = useState<string>('');
  const [selectedGates, setSelectedGates] = useState<string[]>(['Gate D']);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>(['Spanish']);
  const [scriptResult, setScriptResult] = useState<ScriptResult | null>(null);

  // CSV Drag and Drop Simulation State
  const [dragActive, setDragActive] = useState<boolean>(false);

  // Fetch zones on startup
  useEffect(() => {
    fetchZones();
  }, []);

  const fetchZones = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const response = await fetch(`${BACKEND_URL}/api/crowd/zones`);
      if (!response.ok) {
        throw new Error('Failed to fetch crowd zones.');
      }
      const data = await response.json();
      setZones(data.zones);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error connecting to backend API.');
    } finally {
      setLoading(false);
    }
  };

  // Trigger Gemini Crowd Reasoning
  const runCrowdAnalysis = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const response = await fetch(`${BACKEND_URL}/api/crowd/analyze?threshold=${analyzeThreshold}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to run crowd analysis.');
      }
      const data = await response.json();
      setAnalysis(data.analysis);
      showTemporarySuccess('AI Operations reasoning updated!');
    } catch (err: any) {
      setErrorMsg(err.message || 'Error invoking Gemini service.');
    } finally {
      setLoading(false);
    }
  };

  // Submit Translation Form
  const handleTranslate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fanText.trim()) return;

    setLoading(true);
    setErrorMsg(null);
    setTranslationResult(null);
    try {
      const response = await fetch(`${BACKEND_URL}/api/translation/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: fanText,
          fan_language: fanLanguage,
          fan_origin: fanOrigin,
          urgency_level: urgencyLevel,
          stress_level: stressLevel,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Translation API request failed.');
      }

      const data = await response.json();
      setTranslationResult(data.result);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error processing translation.');
    } finally {
      setLoading(false);
    }
  };

  // Submit Broadcast Script Form
  const handleGenerateScript = async (scenarioText: string) => {
    setLoading(true);
    setErrorMsg(null);
    setScriptResult(null);
    try {
      const response = await fetch(`${BACKEND_URL}/api/translation/broadcast-script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario: scenarioText,
          target_gates: selectedGates,
          languages: selectedLanguages,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Script generation failed.');
      }

      const data = await response.json();
      setScriptResult(data.result);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error generating script.');
    } finally {
      setLoading(false);
    }
  };

  // Manual Zone Simulator Updates
  const handleSliderChange = async (zone_id: string, value: number, throughput: number) => {
    const nextStatus = value >= 85.0 ? 'Critical' : value >= 75.0 ? 'Crowded' : 'Normal';

    setZones(prevZones => prevZones.map(zone =>
      zone.zone_id === zone_id ? { ...zone, occupancy_rate: value, status: nextStatus } : zone
    ));

    try {
      await fetch(`${BACKEND_URL}/api/crowd/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          zone_id,
          occupancy_rate: value,
          throughput_rate: throughput
        }),
      });
    } catch (err) {
      console.error('Failed to update zone in backend', err);
    }
  };

  // CSV Drag and Drop Upload logic
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadCSVFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await uploadCSVFile(e.target.files[0]);
    }
  };

  const uploadCSVFile = async (file: File) => {
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    // Simple extension check
    if (!file.name.endsWith('.csv')) {
      setErrorMsg('Client Error: Please upload a valid CSV (.csv) file.');
      setLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${BACKEND_URL}/api/crowd/upload-csv`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || data.detail || 'CSV upload failed.');
      }

      setZones(data.zones);
      setSuccessMsg(`Loaded configuration from ${file.name} successfully!`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to upload CSV configuration.');
    } finally {
      setLoading(false);
    }
  };

  const showTemporarySuccess = (msg: string) => {
    setSuccessMsg(msg);
    window.setTimeout(() => setSuccessMsg(null), 4000);
  };

  const toggleGateSelection = (gate: string) => {
    setSelectedGates(prev =>
      prev.includes(gate) ? prev.filter(g => g !== gate) : [...prev, gate]
    );
  };

  const toggleLanguageSelection = (lang: string) => {
    setSelectedLanguages(prev =>
      prev.includes(lang) ? prev.filter(l => l !== lang) : [...prev, lang]
    );
  };

  return (
    <div className="app-container">
      {/* Top Banner and Navigation */}
      <header className="header">
        <div className="logo-section">
          <div className="logo-icon">V</div>
          <div className="logo-text">
            <h1>GatesenseAI</h1>
            <span>Stadium Operations AI Coordinator</span>
          </div>
        </div>

        <nav className="tabs-nav">
          <button
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={18} />
            Operations Map
          </button>
          <button
            className={`tab-btn ${activeTab === 'translation' ? 'active' : ''}`}
            onClick={() => setActiveTab('translation')}
          >
            <Languages size={18} />
            Translation Assistant
          </button>
          <button
            className={`tab-btn ${activeTab === 'broadcast' ? 'active' : ''}`}
            onClick={() => setActiveTab('broadcast')}
          >
            <Megaphone size={18} />
            Megaphone Scripts
          </button>
          <button
            className={`tab-btn ${activeTab === 'simulator' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('simulator');
              fetchZones();
            }}
          >
            <Settings2 size={18} />
            Data Simulator
          </button>
        </nav>
      </header>

      {/* Global Notification Banners */}
      {errorMsg && (
        <div className="glass-card fade-in" style={{ padding: '1rem', display: 'flex', gap: '0.75rem', borderLeft: '4px solid var(--status-critical)', background: 'var(--status-critical-bg)' }}>
          <AlertCircle style={{ color: 'var(--status-critical)', flexShrink: 0 }} />
          <div>
            <h4 style={{ color: 'var(--status-critical)' }}>System Alert</h4>
            <p style={{ fontSize: '0.9rem', opacity: 0.9 }}>{errorMsg}</p>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="glass-card fade-in" style={{ padding: '1rem', display: 'flex', gap: '0.75rem', borderLeft: '4px solid var(--status-normal)', background: 'var(--status-normal-bg)' }}>
          <CheckCircle2 style={{ color: 'var(--status-normal)', flexShrink: 0 }} />
          <div>
            <h4 style={{ color: 'var(--status-normal)' }}>Success</h4>
            <p style={{ fontSize: '0.9rem', opacity: 0.9 }}>{successMsg}</p>
          </div>
        </div>
      )}

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.04)', padding: '0.5rem 1rem', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <RefreshCw size={16} className="pulse-indicator" style={{ animation: 'spin 1.5s linear infinite' }} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent)' }}>Querying Server Operations...</span>
          </div>
        </div>
      )}

      {/* Main Tab Contents */}
      <main className="dashboard-grid">
        
        {activeTab === 'dashboard' && (
          <>
            {/* Visual Stadium Zone Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'between', alignItems: 'center' }}>
                <h2 style={{ fontSize: '1.4rem' }}>Live Crowd Density</h2>
                <button className="btn-secondary" onClick={fetchZones} style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                  <RefreshCw size={14} /> Refresh Data
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
                {zones.map((zone) => {
                  const isCritical = zone.occupancy_rate >= 80;
                  const isWarning = zone.occupancy_rate >= 70 && zone.occupancy_rate < 80;
                  
                  let statusColor = 'var(--status-normal)';
                  let statusBg = 'var(--status-normal-bg)';
                  if (isCritical) {
                    statusColor = 'var(--status-critical)';
                    statusBg = 'var(--status-critical-bg)';
                  } else if (isWarning) {
                    statusColor = 'var(--status-warning)';
                    statusBg = 'var(--status-warning-bg)';
                  }

                  return (
                    <div key={zone.zone_id} className={`glass-card fade-in`} style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1rem', borderTop: `4px solid ${statusColor}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <h3 style={{ fontSize: '1.1rem', opacity: 0.95 }}>{zone.zone_id}</h3>
                        <span style={{ 
                          fontSize: '0.75rem', 
                          fontWeight: 700, 
                          color: statusColor, 
                          background: statusBg, 
                          padding: '0.2rem 0.5rem', 
                          borderRadius: '8px', 
                          textTransform: 'uppercase' 
                        }} className={isCritical ? 'pulse-indicator' : ''}>
                          {zone.status}
                        </span>
                      </div>
                      
                      {/* Radial Gauge Simulation */}
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.85rem' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>Occupancy</span>
                          <span style={{ fontWeight: 700, color: statusColor }}>{zone.occupancy_rate}%</span>
                        </div>
                        <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ 
                            width: `${zone.occupancy_rate}%`, 
                            height: '100%', 
                            background: `linear-gradient(90deg, ${statusColor} 0%, rgba(255,255,255,0.4) 100%)`,
                            borderRadius: '4px'
                          }} />
                        </div>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', background: 'rgba(255,255,255,0.02)', padding: '0.5rem', borderRadius: '8px' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Flow Rate:</span>
                        <span style={{ fontWeight: 600 }}>{zone.throughput_rate} / min</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* AI Control Center Panel */}
            <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', borderLeft: '4px solid var(--primary)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ background: 'var(--primary-glow)', padding: '0.5rem', borderRadius: '12px', border: '1px solid var(--primary)' }}>
                  <ShieldAlert style={{ color: 'var(--primary)' }} />
                </div>
                <div>
                  <h2 style={{ fontSize: '1.3rem' }}>AI Coordination Feed</h2>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Gemini Decision Support System</p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '12px', border: '1px solid var(--panel-border)' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Alert Trigger Threshold:</span>
                <input 
                  type="range" 
                  min="50" 
                  max="95" 
                  value={analyzeThreshold} 
                  onChange={(e) => setAnalyzeThreshold(parseInt(e.target.value))}
                  style={{ flex: 1, accentColor: 'var(--primary)' }}
                />
                <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary)' }}>{analyzeThreshold}%</span>
              </div>

              <button className="btn-primary" onClick={runCrowdAnalysis} disabled={zones.length === 0}>
                <Activity size={18} /> Analyze Stadium Capacity
              </button>

              <div style={{ flex: 1, minHeight: '240px', background: 'rgba(5, 8, 22, 0.6)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '12px', padding: '1.25rem', overflowY: 'auto' }}>
                {analysis ? (
                  <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--accent)', fontWeight: 600 }}>Active Warnings</span>
                      {analysis.is_mock && <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>(Simulation Mode)</span>}
                    </div>
                    {analysis.alerts.length > 0 ? (
                      <ul style={{ paddingLeft: '1.25rem', color: 'var(--status-critical)', display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.9rem' }}>
                        {analysis.alerts.map((alert, idx) => (
                          <li key={idx} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <AlertTriangle size={14} />
                            {alert}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p style={{ color: 'var(--status-normal)', fontSize: '0.9rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <CheckCircle2 size={16} /> No zones currently exceed the threshold.
                      </p>
                    )}

                    <div style={{ marginTop: '0.5rem' }}>
                      <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--accent)', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>Volunteer Instructions</span>
                      <p style={{ fontSize: '0.95rem', lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                        {analysis.instructions}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', gap: '0.5rem' }}>
                    <ShieldAlert size={36} style={{ strokeWidth: 1.5, opacity: 0.5 }} />
                    <p style={{ fontSize: '0.9rem' }}>Operations feed ready. Click "Analyze" to run Gemini reasoning over the active zones data.</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {activeTab === 'translation' && (
          <>
            {/* Translation Input Panel */}
            <form onSubmit={handleTranslate} className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <Languages size={24} style={{ color: 'var(--accent)' }} />
                <h2 style={{ fontSize: '1.3rem' }}>Translation Assistant</h2>
              </div>

              <div className="input-group">
                <label>Direct Fan Statement / Voice-to-Text Input</label>
                <textarea
                  className="textarea-field"
                  placeholder="e.g. Me siento muy mal, me duele el pecho, ¿dónde está la ambulancia? / Help! I lost my child at Gate B!"
                  rows={4}
                  value={fanText}
                  onChange={(e) => setFanText(e.target.value)}
                  maxLength={2000}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group">
                  <label>Declared Language</label>
                  <select className="select-field" value={fanLanguage} onChange={(e) => setFanLanguage(e.target.value)}>
                    <option value="Auto">Auto Detect</option>
                    <option value="Spanish">Spanish</option>
                    <option value="French">French</option>
                    <option value="Portuguese">Portuguese</option>
                    <option value="Arabic">Arabic</option>
                    <option value="Japanese">Japanese</option>
                    <option value="German">German</option>
                  </select>
                </div>
                <div className="input-group">
                  <label>Fan Origin (Country)</label>
                  <input
                    type="text"
                    className="input-field"
                    placeholder="e.g. Argentina"
                    value={fanOrigin}
                    onChange={(e) => setFanOrigin(e.target.value)}
                    maxLength={50}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group">
                  <label>Urgency Profile</label>
                  <select className="select-field" value={urgencyLevel} onChange={(e) => setUrgencyLevel(e.target.value)}>
                    <option value="casual">Casual (Directions, Info)</option>
                    <option value="important">Important (Ticketing, Logistics)</option>
                    <option value="urgent">Urgent (Heat exhaustion, Lost item)</option>
                    <option value="emergency">Emergency (Injury, Medical, Fire)</option>
                  </select>
                </div>
                <div className="input-group">
                  <label>Stress Indicator</label>
                  <select className="select-field" value={stressLevel} onChange={(e) => setStressLevel(e.target.value)}>
                    <option value="calm">Calm / Normal</option>
                    <option value="anxious">Anxious / Stressed</option>
                    <option value="panicked">Panicked / Hysterical</option>
                  </select>
                </div>
              </div>

              <button type="submit" className="btn-primary" style={{ marginTop: '0.5rem' }}>
                Analyze & Translate Query <ArrowRight size={16} />
              </button>
            </form>

            {/* Translation Output Card */}
            <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', borderLeft: '4px solid var(--accent)' }}>
              <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '0.5rem' }}>GatesenseAI Feed</h3>
              
              {translationResult ? (
                <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  
                  {/* Language and Urgency analysis bar */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <span style={{ background: 'rgba(6, 182, 212, 0.1)', color: 'var(--accent)', border: '1px solid rgba(6, 182, 212, 0.2)', fontSize: '0.8rem', padding: '0.25rem 0.5rem', borderRadius: '8px', fontWeight: 600 }}>
                      Detected: {translationResult.detected_language}
                    </span>
                    <span style={{ 
                      background: urgencyLevel === 'emergency' ? 'var(--status-critical-bg)' : 'rgba(255,255,255,0.04)', 
                      color: urgencyLevel === 'emergency' ? 'var(--status-critical)' : 'var(--text-secondary)', 
                      border: '1px solid rgba(255,255,255,0.08)', 
                      fontSize: '0.8rem', 
                      padding: '0.25rem 0.5rem', 
                      borderRadius: '8px', 
                      fontWeight: 600 
                    }}>
                      Profile: {translationResult.urgency_analysis}
                    </span>
                  </div>

                  {/* Fan text translation */}
                  <div>
                    <h4 style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Translated Statement (English)</h4>
                    <p style={{ background: 'rgba(0,0,0,0.2)', padding: '0.75rem', borderRadius: '8px', fontSize: '1rem', border: '1px solid rgba(255,255,255,0.03)' }}>
                      "{translationResult.fan_text_en}"
                    </p>
                  </div>

                  {/* Volunteer Script Response */}
                  <div style={{ background: 'var(--primary-glow)', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: '12px', padding: '1rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                      <UserCheck size={16} /> Suggested Copilot Response (For You)
                    </div>
                    <p style={{ fontSize: '1rem', fontWeight: 500, lineHeight: 1.5 }}>
                      {translationResult.suggested_response_en}
                    </p>
                  </div>

                  {/* Fan display box (Show to fan card) */}
                  <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1.5px dashed var(--status-normal)', borderRadius: '12px', padding: '1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: 'var(--status-normal)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Volume2 size={16} /> Show / Read to Fan ({translationResult.detected_language})
                      </span>
                    </div>
                    <p style={{ fontSize: '1.15rem', fontStyle: 'italic', fontWeight: 600, color: 'white', lineHeight: 1.6 }}>
                      "{translationResult.suggested_response_fan_lang}"
                    </p>
                  </div>

                </div>
              ) : (
                <div style={{ height: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', gap: '0.5rem' }}>
                  <Languages size={40} style={{ strokeWidth: 1.5, opacity: 0.5 }} />
                  <p style={{ fontSize: '0.9rem' }}>Ready for fan inquiry. Enter the query on the left to analyze sentiment, assess emergency triggers, and generate multi-language assistance scripts.</p>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'broadcast' && (
          <>
            {/* Megaphone Setup Panel */}
            <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Megaphone size={24} style={{ color: 'var(--primary)' }} />
                <h2 style={{ fontSize: '1.3rem' }}>Broadcast Script Generator</h2>
              </div>

              {/* Scenarios Templates */}
              <div>
                <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.5rem' }}>Select Scenario Template</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {SCENARIOS.map((sc, idx) => (
                    <div 
                      key={idx} 
                      onClick={() => setCustomScenario(sc.text)}
                      style={{ 
                        padding: '0.75rem', 
                        borderRadius: '8px', 
                        background: customScenario === sc.text ? 'var(--primary-glow)' : 'rgba(255,255,255,0.02)', 
                        border: customScenario === sc.text ? '1px solid var(--primary)' : '1px solid var(--panel-border)', 
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      <h4 style={{ fontSize: '0.9rem', color: customScenario === sc.text ? 'white' : 'var(--text-secondary)' }}>{sc.title}</h4>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{sc.text}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="input-group">
                <label>Or Enter Custom Announcement Scenario</label>
                <textarea
                  className="textarea-field"
                  placeholder="Enter details on what crowds need to do, where they should go, etc."
                  rows={3}
                  value={customScenario}
                  onChange={(e) => setCustomScenario(e.target.value)}
                  maxLength={1000}
                />
              </div>

              {/* Gate multi select */}
              <div className="input-group">
                <label>Target Gates / Corridors</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {['Gate A', 'Gate B', 'Gate C', 'Gate D', 'Corridor 1', 'Corridor 2'].map(gate => (
                    <button
                      key={gate}
                      type="button"
                      onClick={() => toggleGateSelection(gate)}
                      style={{
                        padding: '0.35rem 0.75rem',
                        borderRadius: '8px',
                        border: '1px solid',
                        borderColor: selectedGates.includes(gate) ? 'var(--accent)' : 'var(--panel-border)',
                        background: selectedGates.includes(gate) ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
                        color: selectedGates.includes(gate) ? 'white' : 'var(--text-secondary)',
                        fontSize: '0.85rem',
                        cursor: 'pointer'
                      }}
                    >
                      {gate}
                    </button>
                  ))}
                </div>
              </div>

              {/* Language selection multi select */}
              <div className="input-group">
                <label>Languages Required</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {['Spanish', 'French', 'Portuguese', 'Arabic', 'Japanese', 'German'].map(lang => (
                    <button
                      key={lang}
                      type="button"
                      onClick={() => toggleLanguageSelection(lang)}
                      style={{
                        padding: '0.35rem 0.75rem',
                        borderRadius: '8px',
                        border: '1px solid',
                        borderColor: selectedLanguages.includes(lang) ? 'var(--primary)' : 'var(--panel-border)',
                        background: selectedLanguages.includes(lang) ? 'var(--primary-glow)' : 'transparent',
                        color: selectedLanguages.includes(lang) ? 'white' : 'var(--text-secondary)',
                        fontSize: '0.85rem',
                        cursor: 'pointer'
                      }}
                    >
                      {lang}
                    </button>
                  ))}
                </div>
              </div>

              <button 
                className="btn-primary" 
                onClick={() => handleGenerateScript(customScenario)}
                disabled={!customScenario.trim() || selectedGates.length === 0 || selectedLanguages.length === 0}
              >
                <Play size={16} /> Generate Megaphone Scripts
              </button>
            </div>

            {/* Megaphone Output scripts card */}
            <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem', borderLeft: '4px solid var(--primary)' }}>
              <h3 style={{ fontSize: '1.2rem', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '0.5rem' }}>Megaphone Output Feed</h3>
              
              {scriptResult ? (
                <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto', maxHeight: '550px' }}>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--panel-border)' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block' }}>Base Scenario Instruction</span>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{scriptResult.scenario}</p>
                  </div>

                  {Object.entries(scriptResult.broadcast_scripts).map(([lang, script]) => (
                    <div key={lang} className="glass-card" style={{ padding: '1rem', background: 'rgba(15, 23, 42, 0.4)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase' }}>{lang}</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Megaphone Broadcast Script</span>
                      </div>
                      <p style={{ fontSize: '1.1rem', fontWeight: 600, color: 'white', lineHeight: 1.5, fontStyle: 'italic' }}>
                        "{script}"
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ height: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', textAlign: 'center', gap: '0.5rem' }}>
                  <Megaphone size={40} style={{ strokeWidth: 1.5, opacity: 0.5 }} />
                  <p style={{ fontSize: '0.9rem' }}>Scripts feed ready. Select a scenario template or input custom parameters to generate broadcast statements.</p>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'simulator' && (
          <div className="full-grid" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
              
              {/* Manual Control sliders */}
              <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.3rem' }}>Dynamic Stadium Control Sliders</h2>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    Manually update the stadium metrics to trigger bottleneck alerts and test the GenAI reasoning engine.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
                  {zones.map((zone) => (
                    <div key={zone.zone_id} style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--panel-border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>{zone.zone_id}</h4>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: zone.occupancy_rate >= 80 ? 'var(--status-critical)' : zone.occupancy_rate >= 70 ? 'var(--status-warning)' : 'var(--status-normal)' }}>
                          {zone.occupancy_rate}%
                        </span>
                      </div>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', width: '60px' }}>Occupancy</span>
                          <input 
                            type="range" 
                            min="0" 
                            max="100" 
                            value={zone.occupancy_rate} 
                            onChange={(e) => handleSliderChange(zone.zone_id, parseFloat(e.target.value), zone.throughput_rate)}
                            style={{ flex: 1, accentColor: 'var(--accent)' }}
                          />
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', width: '60px' }}>Flow Rate</span>
                          <input 
                            type="range" 
                            min="0" 
                            max="500" 
                            value={zone.throughput_rate} 
                            onChange={(e) => handleSliderChange(zone.zone_id, zone.occupancy_rate, parseFloat(e.target.value))}
                            style={{ flex: 1, accentColor: 'var(--primary)' }}
                          />
                          <span style={{ fontSize: '0.75rem', width: '40px', textAlign: 'right' }}>{Math.round(zone.throughput_rate)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CSV Upload component */}
              <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.3rem' }}>Upload Simulation Config (CSV)</h2>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    Upload a custom CSV configuration. This configuration will override all active zone metrics. File is safely processed in memory on the server.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
                  {/* Drag and Drop Box */}
                  <div 
                    onDragEnter={handleDrag}
                    onDragOver={handleDrag}
                    onDragLeave={handleDrag}
                    onDrop={handleDrop}
                    style={{
                      border: dragActive ? '2px dashed var(--accent)' : '2px dashed var(--panel-border)',
                      background: dragActive ? 'rgba(6, 182, 212, 0.05)' : 'rgba(0,0,0,0.1)',
                      borderRadius: '16px',
                      padding: '2.5rem',
                      textAlign: 'center',
                      cursor: 'pointer',
                      position: 'relative',
                      transition: 'all 0.2s'
                    }}
                  >
                    <input 
                      type="file" 
                      id="csv-file-input" 
                      accept=".csv" 
                      onChange={handleFileInput} 
                      style={{ display: 'none' }} 
                    />
                    <label htmlFor="csv-file-input" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                      <UploadCloud size={44} style={{ color: dragActive ? 'var(--accent)' : 'var(--text-muted)' }} />
                      <div>
                        <span style={{ fontWeight: 600, color: 'white' }}>Drag & drop your CSV file here</span>
                        <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.85rem', marginTop: '0.25rem' }}>or click to browse from files</span>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Max file size: 100 KB (.csv format only)</span>
                    </label>
                  </div>

                  {/* CSV Template Reference */}
                  <div style={{ background: 'rgba(5, 8, 22, 0.4)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--panel-border)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--accent)' }}>
                      <FileSpreadsheet size={16} />
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, textTransform: 'uppercase' }}>Sample CSV Structure</span>
                    </div>
                    <pre style={{ 
                      background: 'rgba(0,0,0,0.3)', 
                      padding: '0.75rem', 
                      borderRadius: '8px', 
                      fontFamily: 'monospace', 
                      fontSize: '0.85rem', 
                      color: 'var(--text-secondary)',
                      overflowX: 'auto'
                    }}>
{`zone_id,occupancy_rate,throughput_rate
Gate A,95.0,350.0
Gate B,40.0,110.0
Gate C,30.0,90.0
Gate D,92.0,380.0
Corridor 1 (A-B),98.0,290.0
Corridor 2 (C-D),45.0,120.0`}
                    </pre>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}
      </main>

      {/* Footer Info */}
      <footer style={{ marginTop: 'auto', paddingTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.04)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        <p>© 2026 FIFA World Cup - Smart Stadium Operations Hub</p>
        <p>GatesenseAI • Powered by Google Gemini AI & FastAPI</p>
      </footer>
    </div>
  );
}

export default App;
