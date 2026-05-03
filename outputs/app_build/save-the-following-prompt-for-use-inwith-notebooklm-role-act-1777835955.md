```html
<!DOCTYPE html>
<html lang="en">
<head>
 <meta charset="UTF-8">
 <meta name="viewport" content="width=device-width, initial-scale=1.0">
 <title>Hidden Expertise Extractor - NotebookLM Tool</title>
 <script src="https://cdn.tailwindcss.com"></script>
 <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
 <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
 <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
 <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
 <style>
 * { font-family: 'Inter', sans-serif; }
 .extraction-card { transition: all 0.2s ease; }
 .extraction-card:hover { transform: translateY(-2px); }
 .field-group { border-left: 3px solid #3b82f6; padding-left: 1rem; }
 .loading-spinner { animation: spin 1s linear infinite; }
 @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
 </style>
</head>
<body class="bg-gray-50 min-h-screen">
 <div id="root"></div>
 
 <script type="text/babel">
 const { useState, useEffect } = React;

 const EXTRACTION_FIELDS = [
 { id: 'core_insight', label: 'Core Insight', type: 'textarea', required: true },
 { id: 'hidden_expertise', label: 'Hidden Expertise', type: 'textarea', required: true },
 { id: 'key_story', label: 'Key Story or Example', type: 'textarea', required: false },
 { id: 'decision_points', label: 'Decision Points', type: 'textarea', required: false },
 { id: 'pattern_recognition', label: 'Pattern Recognition', type: 'textarea', required: true },
 { id: 'red_flags', label: 'Red Flags or Warning Signs', type: 'textarea', required: false },
 { id: 'rules_of_thumb', label: 'Rules of Thumb', type: 'textarea', required: false },
 { id: 'mistakes_avoided', label: 'Mistakes Avoided', type: 'textarea', required: false },
 { id: 'contrarian_opinions', label: 'Contrarian Opinions', type: 'textarea', required: false },
 { id: 'frameworks', label: 'Frameworks or Named Models', type: 'textarea', required: false },
 { id: 'diagnostic_questions', label: 'Diagnostic Questions', type: 'textarea', required: false },
 { id: 'content_angles', label: 'Content Angles', type: 'textarea', required: false },
 { id: 'newsletter_ideas', label: 'Newsletter Ideas', type: 'textarea', required: false },
 { id: 'lead_magnet_ideas', label: 'Lead Magnet Ideas', type: 'textarea', required: false },
 { id: 'product_offer_ideas', label: 'Product or Offer Ideas', type: 'textarea', required: false },
 { id: 'quote_worthy', label: 'Best Quote-Worthy Lines', type: 'textarea', required: false },
 { id: 'tags_categories', label: 'Tags and Categories', type: 'textarea', required: false },
 { id: 'confidence_level', label: 'Confidence Level', type: 'select', required: true, options: ['High', 'Medium', 'Low', 'Needs Clarification'] },
 { id: 'recommended_next_use', label: 'Recommended Next Use', type: 'textarea', required: false }
 ];

 const App = () => {
 const [rawMaterial, setRawMaterial] = useState('');
 const [extractionResults, setExtractionResults] = useState({});
 const [isProcessing, setIsProcessing] = useState(false);
 const [showResults, setShowResults] = useState(false);
 const [emailTo, setEmailTo] = useState('');
 const [emailSent, setEmailSent] = useState(false);
 const [errors, setErrors] = useState({});

 const handleInputChange = (fieldId, value) => {
 setExtractionResults(prev => ({ ...prev, [fieldId]: value }));
 if (errors[fieldId]) {
 setErrors(prev => {
 const newErrors = { ...prev };
 delete newErrors[fieldId];
 return newErrors;
 });
 }
 };

 const validateForm = () => {
 const newErrors = {};
 EXTRACTION_FIELDS.forEach(field => {
 if (field.required && !extractionResults[field.id]?.trim()) {
 newErrors[field.id] = `${field.label} is required`;
 }
 });
 setErrors(newErrors);
 return Object.keys(newErrors).length === 0;
 };

 const simulateProcessing = () => {
 setIsProcessing(true);
 setTimeout(() => {
 const mockResults = {
 core_insight: 'AI consultants fail when they prioritize technology over delivery outcomes.',
 hidden_expertise: 'The real differentiator is not AI knowledge but understanding client business processes.',
 key_story: 'A consultant spent 3 months building an AI solution that solved no actual business problem.',
 decision_points: 'Choose between quick wins vs. long-term transformation projects.',
 pattern_recognition: 'Successful AI implementations follow a 3-phase pattern: assess, pilot, scale.',
 red_flags: 'Clients expecting immediate ROI without process changes.',
 rules_of_thumb: 'Start with 20% of the problem to prove value before expanding.',
 mistakes_avoided: 'Avoid building custom AI when off-the-shelf solutions work.',
 contrarian_opinions: 'Most AI training is unnecessary; focus on prompt engineering instead.',
 frameworks: 'The AI Delivery Maturity Model (ADMM) framework.',
 diagnostic_questions: 'What business metric will this AI improve?',
 content_angles: 'Why 90% of AI projects fail at delivery.',
 newsletter_ideas: 'Case study: How we saved $50K with better AI implementation.',
 lead_magnet_ideas: 'AI Implementation Checklist for Non-Technical Founders.',
 product_offer_ideas: 'AI Readiness Assessment Tool ($497).',
 quote_worthy: 'Technology is easy; delivery is hard.',
 tags_categories: 'AI, Consulting, Delivery, Business Strategy',
 confidence_level: 'High',
 recommended_next_use: 'Use for client discovery calls and proposal development.'
 };
 setExtractionResults(mockResults);
 setIsProcessing(false);
 setShowResults(true);
 }, 2000);
 };

 const handleEmail = () => {
 if (!emailTo || !emailTo.includes('@')) {
 alert('Please enter a valid email address');
 return;
 }
 setEmailSent(true);
 setTimeout(() => setEmailSent(false), 3000);
 };

 const handleExport = () => {
 const exportData = {
 timestamp: new Date().toISOString(),
 rawMaterial,
 extractionResults
 };
 const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
 const url = URL.createObjectURL(blob);
 const a = document.createElement('a');
 a.href = url;
 a.download = `extraction-${Date.now()}.json`;
 a.click();
 URL.revokeObjectURL(url);
 };

 const handlePrint = () => {
 window.print();
 };

 const getRequiredCount = () => {
 return EXTRACTION_FIELDS.filter(f => f.required && extractionResults[f.id]?.trim()).length;
 };

 return (
 <div className="max-w-7xl mx-auto px-4 py-8">
 <header className="mb-8">
 <h1 className="text-3xl font-bold text-gray-900 mb-2">Hidden Expertise Extractor</h1>
 <p className="text-gray-600">Transform raw material into actionable insights for your newsletter</p>
 </header>

 <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
 <div className="space-y-6">
 <div className="bg-white rounded-lg shadow-md p-6">
 <h2 className="text-xl font-semibold mb-4">Input Raw Material</h2>
 <textarea
 className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
 placeholder="Paste transcript, notes, interview, voice memo, client call, messy idea, news, or competitive intelligence here..."
 value={rawMaterial}
 onChange={(e) => setRawMaterial(e.target.value)}
 />
 <div className="mt-4 flex justify-between items-center">
 <span className="text-sm text-gray-500">
 {rawMaterial.length} characters
 </span>
 <button
 onClick={simulateProcessing}
 disabled={isProcessing || !rawMaterial.trim()}
 className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
 >
 {isProcessing ? (
 <span className="flex items-center gap-2">
 <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full loading-spinner"></div>
 Processing...
 </span>
 ) : (
 'Extract Insights'
 )}
 </button>
 </div>
 </div>

 {showResults && (
 <div className="bg-white rounded-lg shadow-md p-6">
 <h2 className="text-xl font-semibold mb-4">Email Results</h2>
 <div className="space-y-4">
 <input
 type="email"
 placeholder="Enter recipient email"
 value={emailTo}
 onChange={(e) => setEmailTo(e.target.value)}
 className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
 />
 <div className="flex gap-3">
 <button
 onClick={handleEmail}
 className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
 >
 {emailSent ? '✓ Sent!' : 'Email Results'}
 </button>
 <button
 onClick={handleExport}
 className="flex-1 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
 >
 Export JSON
 </button>
 <button
 onClick={handlePrint}
 className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
 >
 Print
 </button>
 </div>
 </div>
 </div>
 )}
 </div>

 <div className="space-y-6">
 {showResults && (
 <div className="bg-white rounded-lg shadow-md p-6">
 <div className="flex justify-between items-center mb-6">
 <h2 className="text-xl font-semibold">Extraction Results</h2>
 <span className="text-sm text-gray-500">
 {getRequiredCount()}/{EXTRACTION_FIELDS.filter(f => f.required).length} required fields complete
 </span>
 </div>

 <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto pr-4">
 {EXTRACTION_FIELDS.map((field) => (
 <div key={field.id} className="field-group">
 <label className="block text-sm font-medium text-gray-700 mb-1">
 {field.label}
 {field.required && <span className="text-red-500 ml-1">*</span>}
 </label>
 {field.type === 'select' ? (
 <select
 value={extractionResults[field.id] || ''}
 onChange={(e) => handleInputChange(field.id, e.target.value)}
 className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 ${errors[field.id] ? 'border-red-500' : 'border-gray-300'}`}
 >
 <option value="">Select...</option>
 {field.options?.map(opt => (
 <option key={opt} value={opt}>{opt}</option>
 ))}
 </select>
 ) : (
 <textarea
 value={extractionResults[field.id] || ''}
 onChange={(e) => handleInputChange(field.id, e.target.value)}
 rows={3}
 className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 resize-none ${errors[field.id] ? 'border-red-500' : 'border-gray-300'}`}
 />
 )}
 {errors[field.id] && (
 <p className="text-red-500 text-xs mt-1">{errors[field.id]}</p>
 )}
 </div>
 ))}
 </div>
 </div>
 )}
 </div>
 </div>

 {showResults && (
 <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
 <h3 className="font-semibold text-blue-900 mb-2">✨ Extraction Complete!</h3>
 <p className="text-blue-800 text-sm">
 You've extracted {Object.keys(extractionResults).length} insights from your raw material. 
 Review the results, fill in any missing fields, then email or export as needed.
 </p>
 </div>
 )}
 </div>
 );
 };

 ReactDOM.createRoot(document.getElementById('root')).render(<App />);
 </script>
</body>
</html>
```