import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  downloadPdfReport,
  getAnalysisById,
  getAnalysisHistory,
  getGradCamExplanation,
  getLimeExplanation,
  getPrediction,
  logout,
} from "../api";

const classDescriptions = {
  "No Impairment": "The model sees this scan as most aligned with normal cognitive patterns.",
  "Very Mild Impairment": "The model detects subtle features associated with very early-stage impairment.",
  "Mild Impairment": "The model identifies signs consistent with noticeable cognitive decline.",
  "Moderate Impairment": "The model sees stronger features associated with advanced impairment.",
};

const classColors = ["#3ddc97", "#49a6ff", "#ffb648", "#ff6b6b"];

function Dashboard() {
  const navigate = useNavigate();
  const userData = JSON.parse(localStorage.getItem("neurolens_user") || "{}");

  const [workflowStep, setWorkflowStep] = useState(1);
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [prediction, setPrediction] = useState(null);
  const [explanationMethod, setExplanationMethod] = useState("gradcam");
  const [overlayOpacity, setOverlayOpacity] = useState(0.5);
  const [limeSamples, setLimeSamples] = useState(1000);
  const [explanationImages, setExplanationImages] = useState({ gradcam: "", lime: "" });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isGeneratingExplanation, setIsGeneratingExplanation] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isLoadingHistoryItem, setIsLoadingHistoryItem] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const records = await getAnalysisHistory();
      setHistory(records);
    } catch {
      setHistory([]);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const explanationImage = explanationImages[explanationMethod] || "";
  const explanationSrc = explanationImage ? `data:image/png;base64,${explanationImage}` : "";
  const generatedExplanationCount = Object.values(explanationImages).filter(Boolean).length;
  const predictedIndex = prediction ? prediction.classes.indexOf(prediction.label) : -1;
  const predictedColor = predictedIndex >= 0 ? classColors[predictedIndex] : "var(--text-main)";
  const confidencePercent = prediction ? `${(prediction.confidence * 100).toFixed(1)}%` : "--";
  const secondBestIndex =
    prediction
      ? prediction.probabilities
          .map((value, index) => ({ value, index }))
          .sort((a, b) => b.value - a.value)[1]?.index ?? -1
      : -1;
  const secondBestLabel = secondBestIndex >= 0 ? prediction.classes[secondBestIndex] : "--";
  const fileName = file?.name || prediction?.filename || "No scan uploaded yet";

  const handleFileChange = (event) => {
    const nextFile = event.target.files?.[0];
    if (!nextFile) return;

    if (previewUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }

    const nextPreviewUrl = URL.createObjectURL(nextFile);
    setFile(nextFile);
    setPreviewUrl(nextPreviewUrl);
    setPrediction(null);
    setExplanationImages({ gradcam: "", lime: "" });
    setError("");
    setWorkflowStep(1);
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError("Please upload an MRI image to begin.");
      return;
    }

    setIsAnalyzing(true);
    setError("");

    try {
      const result = await getPrediction(file);
      setPrediction(result);
      setWorkflowStep(2);
      await loadHistory();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateExplanation = async () => {
    if (!file && !previewUrl) {
      setError("Upload a scan before generating an explanation map.");
      return;
    }

    setIsGeneratingExplanation(true);
    setError("");

    try {
      const result =
        explanationMethod === "gradcam"
          ? await getGradCamExplanation(file, overlayOpacity)
          : await getLimeExplanation(file, limeSamples);

      setExplanationImages((current) => ({
        ...current,
        [explanationMethod]: result.image_base64,
      }));
      setWorkflowStep(3);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsGeneratingExplanation(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!prediction) return;
    setIsDownloadingPdf(true);
    try {
      const blob = await downloadPdfReport(prediction.analysis_id || prediction.id, explanationImages);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `NeuroLens_Report_${prediction.analysis_id}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError(`Failed to download report: ${downloadError.message}`);
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const restoreAnalysis = async (id) => {
    setIsLoadingHistoryItem(true);
    setIsHistoryOpen(false);
    try {
      const analysis = await getAnalysisById(id);
      setPreviewUrl(`data:${analysis.content_type};base64,${analysis.image_base64}`);
      setPrediction(analysis);
      setFile(null);
      setWorkflowStep(4);
      setExplanationImages({ gradcam: "", lime: "" });
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoadingHistoryItem(false);
    }
  };

  const nextStep = () => setWorkflowStep((step) => Math.min(step + 1, 4));
  const prevStep = () => setWorkflowStep((step) => Math.max(step - 1, 1));
  const startNewAnalysis = () => {
    if (previewUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    setFile(null);
    setPreviewUrl("");
    setPrediction(null);
    setExplanationImages({ gradcam: "", lime: "" });
    setError("");
    setWorkflowStep(1);
  };

  const renderStep = () => {
    switch (workflowStep) {
      case 1:
        return (
          <div className="wizard-content">
            <section className="dashboard-hero">
              <div>
                <span className="eyebrow">Clinical AI Workspace</span>
                <h2 className="hero-title">Turn an uploaded MRI into a guided, explainable diagnostic summary.</h2>
                <p className="hero-copy">
                  Upload a sagittal scan, inspect the model prediction, review the explanation map, and export a polished PDF report.
                </p>
              </div>
              <div className="hero-badges">
                <div className="hero-badge">
                  <strong>{history.length}</strong>
                  <span>Saved analyses</span>
                </div>
                <div className="hero-badge">
                  <strong>4-step</strong>
                  <span>Review workflow</span>
                </div>
                <div className="hero-badge">
                  <strong>PDF</strong>
                  <span>Export ready</span>
                </div>
              </div>
            </section>

            <div className="glass-panel intake-layout">
              <div className="intake-primary">
                <label className="upload-zone">
                  <div className="upload-icon">+</div>
                  <h3>Upload Patient MRI</h3>
                  <p className="upload-hint">Click to browse a JPG or PNG brain scan and start a guided analysis.</p>
                  <input type="file" accept="image/*" onChange={handleFileChange} />
                </label>

                <div className="micro-cards">
                  <div className="micro-card">
                    <span>Accepted Files</span>
                    <strong>JPG, PNG</strong>
                  </div>
                  <div className="micro-card">
                    <span>Explainability</span>
                    <strong>Grad-CAM, LIME</strong>
                  </div>
                </div>
              </div>

              <aside className="preview-card">
                <div className="preview-card-header">
                  <div>
                    <span className="eyebrow">Live Preview</span>
                    <h3>Scan intake panel</h3>
                  </div>
                  <span className="status-pill">{previewUrl ? "Ready" : "Waiting"}</span>
                </div>

                {previewUrl ? (
                  <>
                    <div className="scan-container preview-frame">
                      <img src={previewUrl} className="scan-mri" alt="Preview" />
                    </div>
                    <div className="file-meta">
                      <div>
                        <span>Selected file</span>
                        <strong>{fileName}</strong>
                      </div>
                      <div>
                        <span>Next action</span>
                        <strong>Run analysis</strong>
                      </div>
                    </div>
                    <button className="btn btn-primary btn-large" onClick={handleAnalyze} disabled={isAnalyzing}>
                      {isAnalyzing ? "Processing Analysis..." : "Finalize & Analyze"}
                    </button>
                  </>
                ) : (
                  <div className="empty-state-card">
                    <div className="empty-icon">MRI</div>
                    <p>Your uploaded scan will appear here with a quick-read summary before analysis begins.</p>
                  </div>
                )}
              </aside>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="wizard-content">
            <div className="glass-panel analysis-shell">
              <div className="analysis-grid">
                <div className="scan-container featured-scan">
                  <div className="scanning-overlay" />
                  <img src={previewUrl} className="scan-mri" alt="Current Scan" />
                  <div className="image-caption">Uploaded MRI scan</div>
                </div>

                <div className="result-card enhanced-card">
                  <div className="result-card-header">
                    <span className="prediction-label">Neural Model Prediction</span>
                    <span className="status-pill accent">AI summary</span>
                  </div>

                  <h2 className="prediction-value" style={{ color: predictedColor }}>
                    {prediction.label}
                  </h2>

                  <div className="context-card">
                    {classDescriptions[prediction.label]}
                  </div>

                  <div className="metric-grid">
                    <div className="metric-card">
                      <span>Confidence</span>
                      <strong>{confidencePercent}</strong>
                    </div>
                    <div className="metric-card">
                      <span>Runner-up</span>
                      <strong>{secondBestLabel}</strong>
                    </div>
                  </div>

                  <div className="probabilities">
                    {prediction.classes.map((cls, idx) => (
                      <div key={cls} className="probability-bar">
                        <div className="bar-label">
                          <span>{cls}</span>
                          <strong>{(prediction.probabilities[idx] * 100).toFixed(1)}%</strong>
                        </div>
                        <div className="bar-track">
                          <div
                            className="bar-fill"
                            style={{
                              width: `${prediction.probabilities[idx] * 100}%`,
                              background: `linear-gradient(90deg, ${classColors[idx]}, color-mix(in srgb, ${classColors[idx]} 55%, white))`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="info-banner">
                    <strong>Interpretation note</strong>
                    <span>The prediction indicates model preference, not a clinical diagnosis. Use the next step to inspect where the model focused.</span>
                  </div>

                  <div className="action-row">
                    <button className="btn btn-secondary" onClick={prevStep}>Back</button>
                    <button className="btn btn-primary" onClick={nextStep}>Generate Heatmaps</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="wizard-content">
            <div className="glass-panel studio-layout">
              <div className="studio-topbar">
                <div>
                  <span className="eyebrow">Explainability Studio</span>
                  <h3 className="panel-title">Inspect what guided the model decision.</h3>
                </div>
                <div className="legend">
                  <span className="legend-label">Legend</span>
                  <div className="legend-scale">
                    <span>Low influence</span>
                    <div className="legend-gradient" />
                    <span>High influence</span>
                  </div>
                </div>
              </div>

              <div className="studio-preview">
                <div className="scan-container">
                  <img src={previewUrl} className="scan-mri" alt="Original" />
                  <div className="image-caption">Original MRI</div>
                </div>
                <div className="scan-container">
                  {explanationSrc ? (
                    <img src={explanationSrc} className="scan-mri" alt="Explanation" />
                  ) : (
                    <div className="explanation-placeholder">
                      <div className="empty-icon">AI</div>
                      <p>Generate an explanation map to visualize the regions that influenced the prediction.</p>
                    </div>
                  )}
                  <div className="image-caption">{explanationMethod === "gradcam" ? "Grad-CAM model view" : "LIME feature importance"}</div>
                </div>
              </div>

              <div className="studio-controls">
                <div className="segmented-control">
                  <button className={`btn-tab ${explanationMethod === "gradcam" ? "active" : ""}`} onClick={() => setExplanationMethod("gradcam")}>
                    Grad-CAM
                  </button>
                  <button className={`btn-tab ${explanationMethod === "lime" ? "active" : ""}`} onClick={() => setExplanationMethod("lime")}>
                    LIME
                  </button>
                </div>

                {explanationMethod === "gradcam" ? (
                  <div className="control-card">
                    <span>Heat Intensity</span>
                    <div className="slider-wrap">
                      <input
                        type="range"
                        min="0.1"
                        max="0.9"
                        step="0.1"
                        value={overlayOpacity}
                        onChange={(e) => setOverlayOpacity(Number(e.target.value))}
                      />
                      <strong>{overlayOpacity.toFixed(1)}</strong>
                    </div>
                  </div>
                ) : (
                  <div className="control-card">
                    <span>LIME Samples</span>
                    <div className="slider-wrap">
                      <input
                        type="range"
                        min="200"
                        max="1500"
                        step="100"
                        value={limeSamples}
                        onChange={(e) => setLimeSamples(Number(e.target.value))}
                      />
                      <strong>{limeSamples}</strong>
                    </div>
                  </div>
                )}

                <button className="btn btn-primary" onClick={handleGenerateExplanation} disabled={isGeneratingExplanation}>
                  {isGeneratingExplanation ? "Computing..." : "Generate Analysis Map"}
                </button>
              </div>

              <div className="explanation-note">
                <strong>Reading the map</strong>
                <span>Warm colors mark stronger model influence for this prediction. Cooler colors indicate lower contribution.</span>
              </div>

              <div className="action-row">
                <button className="btn btn-secondary" onClick={prevStep}>Back to Prediction</button>
                <button className="btn btn-primary" onClick={nextStep} disabled={!generatedExplanationCount}>Finalize Report</button>
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="wizard-content">
            <div className="glass-panel results-shell">
              <div className="success-badge">✓</div>
              <h2 className="results-title">Analysis Completed</h2>
              <p className="results-copy">Your structured review is ready for export and archival.</p>

              <div className="summary-grid">
                 <div className="summary-card">
                   <span>Prediction</span>
                   <strong style={{ color: predictedColor }}>{prediction?.label || "--"}</strong>
                 </div>
                 <div className="summary-card">
                   <span>Confidence</span>
                   <strong>{confidencePercent}</strong>
                 </div>
                 <div className="summary-card">
                   <span>Explanation</span>
                   <strong>{generatedExplanationCount ? `${generatedExplanationCount} map(s)` : "Not attached"}</strong>
                 </div>
                <div className="summary-card">
                  <span>Analysis ID</span>
                  <strong>#{prediction?.analysis_id || prediction?.id || "--"}</strong>
                </div>
              </div>

              <div className="results-actions">
                <button className="btn btn-secondary" onClick={startNewAnalysis}>New Analysis</button>
                <button className="btn btn-secondary" onClick={() => setIsHistoryOpen(true)}>View Archives</button>
                <button className="btn btn-primary" onClick={handleDownloadPdf} disabled={isDownloadingPdf}>
                  {isDownloadingPdf ? "Exporting PDF..." : "Export Medical PDF"}
                </button>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <div className="app-container">
        <header className="header">
          <div className="brand-block">
            <h1 className="brand-title">NeuroLens AI</h1>
            <p className="brand-subtitle">Explainable AI for Predicting and Classifying Neurodegenerative Alzehmeris Disorders</p>
          </div>

          <div className="workflow-nav">
            <div className={`step-box ${workflowStep === 1 ? "active" : workflowStep > 1 ? "completed" : ""}`}>1. Intake</div>
            <div className="step-divider" />
            <div className={`step-box ${workflowStep === 2 ? "active" : workflowStep > 2 ? "completed" : ""}`}>2. Analysis</div>
            <div className="step-divider" />
            <div className={`step-box ${workflowStep === 3 ? "active" : workflowStep > 3 ? "completed" : ""}`}>3. Studio</div>
            <div className="step-divider" />
            <div className={`step-box ${workflowStep === 4 ? "active" : ""}`}>4. Results</div>
          </div>

<div className="user-cluster">
            <span className="username-display">{userData.username || "guest"}</span>
            <button className="btn-tab" onClick={handleLogout}>Logout</button>
          </div>
        </header>

        {error && <div className="error-msg">{error}</div>}
        {isLoadingHistoryItem && <div className="info-banner floating-banner"><strong>Loading archived analysis</strong><span>Preparing saved scan and report metadata.</span></div>}

        <main>{renderStep()}</main>

        <div className={`side-panel ${isHistoryOpen ? "open" : ""}`}>
          <div className="side-panel-header">
            <div>
              <span className="eyebrow">Archive</span>
              <h2>Analysis History</h2>
            </div>
            <button className="btn btn-secondary" onClick={() => setIsHistoryOpen(false)}>Close</button>
          </div>

          <div className="history-list">
            {history.length > 0 ? (
              history.map((entry) => (
                <div key={entry.id} className="history-item" onClick={() => restoreAnalysis(entry.id)}>
                  <div className="history-topline">
                    <strong>{entry.label}</strong>
                    <span className="history-id">#{entry.id}</span>
                  </div>
                  <div className="history-file">{entry.filename}</div>
                  <div className="history-meta">
                    <span>{(entry.confidence * 100).toFixed(1)}% confidence</span>
                    <span>{entry.created_at}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state-card">
                <div className="empty-icon">0</div>
                <p>No previous records found yet. Completed analyses will appear here automatically.</p>
              </div>
            )}
          </div>
        </div>

        {!isHistoryOpen && (
          <button className="btn btn-secondary history-trigger" onClick={() => setIsHistoryOpen(true)}>
            View History
          </button>
        )}

        <footer className="disclaimer">
          For research and educational use only. AI results require professional clinical verification.
        </footer>
      </div>
    </div>
  );
}

export default Dashboard;
