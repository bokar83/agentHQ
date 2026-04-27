```html
<!DOCTYPE html>
<html lang="en">
<head>
 <meta charset="UTF-8">
 <meta name="viewport" content="width=device-width, initial-scale=1.0">
 <title>Content Board - Catalyst Works</title>
 <style>
 :root {
 --color-primary: #0066CC;
 --color-primary-dark: #004C99;
 --color-secondary: #6C757D;
 --color-success: #28A745;
 --color-warning: #FFC107;
 --color-info: #17A2B8;
 --color-white: #FFFFFF;
 --color-gray-50: #F8F9FA;
 --color-gray-100: #F1F3F5;
 --color-gray-200: #E9ECEF;
 --color-gray-300: #DEE2E6;
 --color-gray-400: #CED4DA;
 --color-gray-500: #ADB5BD;
 --color-gray-600: #6C757D;
 --color-gray-700: #495057;
 --color-gray-800: #343A40;
 --color-gray-900: #212529;
 --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
 --spacing-xs: 4px;
 --spacing-sm: 8px;
 --spacing-md: 16px;
 --spacing-lg: 24px;
 --spacing-xl: 32px;
 --spacing-2xl: 48px;
 --border-radius: 8px;
 --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
 --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
 --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
 }

 * {
 margin: 0;
 padding: 0;
 box-sizing: border-box;
 }

 body {
 font-family: var(--font-family);
 background-color: var(--color-gray-50);
 color: var(--color-gray-800);
 line-height: 1.6;
 min-height: 100vh;
 }

 .container {
 max-width: 1200px;
 margin: 0 auto;
 padding: var(--spacing-lg);
 }

 .header {
 background-color: var(--color-white);
 padding: var(--spacing-lg) var(--spacing-xl);
 border-bottom: 1px solid var(--color-gray-200);
 margin-bottom: var(--spacing-xl);
 box-shadow: var(--shadow-sm);
 }

 .header-content {
 display: flex;
 justify-content: space-between;
 align-items: center;
 flex-wrap: wrap;
 gap: var(--spacing-md);
 }

 .logo {
 font-size: 24px;
 font-weight: 700;
 color: var(--color-primary);
 display: flex;
 align-items: center;
 gap: var(--spacing-sm);
 }

 .logo-icon {
 width: 32px;
 height: 32px;
 background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
 border-radius: var(--border-radius);
 display: flex;
 align-items: center;
 justify-content: center;
 color: white;
 font-weight: bold;
 }

 .stats {
 display: flex;
 gap: var(--spacing-lg);
 flex-wrap: wrap;
 }

 .stat-item {
 display: flex;
 align-items: center;
 gap: var(--spacing-sm);
 padding: var(--spacing-sm) var(--spacing-md);
 background-color: var(--color-gray-100);
 border-radius: var(--border-radius);
 font-size: 14px;
 }

 .stat-value {
 font-weight: 700;
 color: var(--color-primary);
 }

 .main-content {
 display: grid;
 grid-template-columns: 1fr;
 gap: var(--spacing-lg);
 }

 @media (min-width: 768px) {
 .main-content {
 grid-template-columns: 1fr 350px;
 }
 }

 .posts-section {
 background-color: var(--color-white);
 border-radius: var(--border-radius);
 box-shadow: var(--shadow-md);
 overflow: hidden;
 }

 .section-header {
 padding: var(--spacing-lg);
 border-bottom: 1px solid var(--color-gray-200);
 display: flex;
 justify-content: space-between;
 align-items: center;
 flex-wrap: wrap;
 gap: var(--spacing-md);
 }

 .section-title {
 font-size: 20px;
 font-weight: 600;
 color: var(--color-gray-900);
 }

 .filter-controls {
 display: flex;
 gap: var(--spacing-sm);
 flex-wrap: wrap;
 }

 .filter-btn {
 padding: var(--spacing-sm) var(--spacing-md);
 border: 1px solid var(--color-gray-300);
 background-color: var(--color-white);
 border-radius: var(--border-radius);
 cursor: pointer;
 font-size: 14px;
 transition: all 0.2s ease;
 }

 .filter-btn:hover {
 background-color: var(--color-gray-100);
 }

 .filter-btn.active {
 background-color: var(--color-primary);
 color: var(--color-white);
 border-color: var(--color-primary);
 }

 .posts-list {
 padding: var(--spacing-md);
 display: flex;
 flex-direction: column;
 gap: var(--spacing-md);
 }

 .post-card {
 border: 1px solid var(--color-gray-200);
 border-radius: var(--border-radius);
 padding: var(--spacing-lg);
 background-color: var(--color-white);
 transition: all 0.2s ease;
 cursor: pointer;
 }

 .post-card:hover {
 box-shadow: var(--shadow-md);
 border-color: var(--color-primary);
 }

 .post-header {
 display: flex;
 justify-content: space-between;
 align-items: flex-start;
 margin-bottom: var(--spacing-md);
 flex-wrap: wrap;
 gap: var(--spacing-sm);
 }

 .post-title {
 font-size: 18px;
 font-weight: 600;
 color: var(--color-gray-900);
 margin-bottom: var(--spacing-xs);
 }

 .post-meta {
 display: flex;
 gap: var(--spacing-md);
 font-size: 13px;
 color: var(--color-gray-500);
 }

 .post-preview {
 color: var(--color-gray-600);
 font-size: 14px;
 line-height: 1.7;
 margin-bottom: var(--spacing-md);
 display: -webkit-box;
 -webkit-line-clamp: 3;
 -webkit-box-orient: vertical;
 overflow: hidden;
 }

 .post-actions {
 display: flex;
 gap: var(--spacing-sm);
 flex-wrap: wrap;
 }

 .btn {
 padding: var(--spacing-sm) var(--spacing-md);
 border: none;
 border-radius: var(--border-radius);
 font-size: 14px;
 font-weight: 500;
 cursor: pointer;
 transition: all 0.2s ease;
 display: inline-flex;
 align-items: center;
 gap: var(--spacing-xs);
 }

 .btn-primary {
 background-color: var(--color-primary);
 color: var(--color-white);
 }

 .btn-primary:hover {
 background-color: var(--color-primary-dark);
 }

 .btn-secondary {
 background-color: var(--color-gray-200);
 color: var(--color-gray-700);
 }

 .btn-secondary:hover {
 background-color: var(--color-gray-300);
 }

 .btn-success {
 background-color: var(--color-success);
 color: var(--color-white);
 }

 .btn-success:hover {
 background-color: #218838;
 }

 .btn-danger {
 background-color: #DC3545;
 color: var(--color-white);
 }

 .btn-danger:hover {
 background-color: #C82333;
 }

 .status-badge {
 display: inline-flex;
 align-items: center;
 padding: var(--spacing-xs) var(--spacing-sm);
 border-radius: 20px;
 font-size: 12px;
 font-weight: 600;
 text-transform: uppercase;
 }

 .status-pending {
 background-color: var(--color-warning);
 color: var(--color-gray-800);
 }

 .status-approved {
 background-color: var(--color-success);
 color: var(--color-white);
 }

 .status-rejected {
 background-color: var(--color-gray-500);
 color: var(--color-white);
 }

 .sidebar {
 background-color: var(--color-white);
 border-radius: var(--border-radius);
 box-shadow: var(--shadow-md);
 padding: var(--spacing-lg);
 height: fit-content;
 position: sticky;
 top: var(--spacing-lg);
 }

 .sidebar-title {
 font-size: 18px;
 font-weight: 600;
 margin-bottom: var(--spacing-md);
 padding-bottom: var(--spacing-sm);
 border-bottom: 2px solid var(--color-gray-200);
 }

 .approval-panel {
 display: flex;
 flex-direction: column;
 gap: var(--spacing-md);
 }

 .approval-item {
 padding: var(--spacing-md);
 background-color: var(--color-gray-50);
 border-radius: var(--border-radius);
 border-left: 4px solid var(--color-primary);
 }

 .approval-item-title {
 font-weight: 600;
 margin-bottom: var(--spacing-xs);
 font-size: 14px;
 }

 .approval-item-meta {
 font-size: 12px;
 color: var(--color-gray-500);
 margin-bottom: var(--spacing-sm);
 }

 .approval-actions {
 display: flex;
 gap: var(--spacing-sm);
 }

 .approval-actions .btn {
 flex: 1;
 justify-content: center;
 }

 .modal-overlay {
 position: fixed;
 top: 0;
 left: 0;
 right: 0;
 bottom: 0;
 background-color: rgba(0, 0, 0, 0.7);
 display: flex;
 align-items: center;
 justify-content: center;
 z-index: 1000;
 opacity: 0;
 visibility: hidden;
 transition: all 0.3s ease;
 }

 .modal-overlay.active {
 opacity: 1;
 visibility: visible;
 }

 .modal {
 background-color: var(--color-white);
 border-radius: var(--border-radius);
 max-width: 800px;
 width: 90%;
 max-height: 90vh;
 overflow-y: auto;
 transform: scale(0.9);
 transition: transform 0.3s ease;
 }

 .modal-overlay.active .modal {
 transform: scale(1);
 }

 .modal-header {
 padding: var(--spacing-lg);
 border-bottom: 1px solid var(--color-gray-200);
 display: flex;
 justify-content: space-between;
 align-items: flex-start;
 flex-wrap: wrap;
 gap: var(--spacing-md);
 }

 .modal-title {
 font-size: 24px;
 font-weight: 700;
 color: var(--color-gray-900);
 }

 .modal-close {
 background: none;
 border: none;
 font-size: 28px;
 cursor: pointer;
 color: var(--color-gray-400);
 padding: var(--spacing-xs);
 line-height: 1;
 }

 .modal-close:hover {
 color: var(--color-gray-600);
 }

 .modal-body {
 padding: var(--spacing-lg);
 }

 .modal-content {
 font-size: 16px;
 line-height: 1.8;
 color: var(--color-gray-700);
 white-space: pre-wrap;
 }

 .modal-footer {
 padding: var(--spacing-lg);
 border-top: 1px solid var(--color-gray-200);
 display: flex;
 justify-content: flex-end;
 gap: var(--spacing-md);
 background-color: var(--color-gray-50);
 border-radius: 0 0 var(--border-radius) var(--border-radius);
 }

 .empty-state {
 text-align: center;
 padding: var(--spacing-2xl);
 color: var(--color-gray-500);
 }

 .empty-state-icon {
 font-size: 48px;
 margin-bottom: var(--spacing-md);
 opacity: 0.5;
 }

 .empty-state-title {
 font-size: 20px;
 font-weight: 600;
 margin-bottom: var(--spacing-sm);
 color: var(--color-gray-700);
 }

 .empty-state-text {
 font-size: 14px;
 }

 .toast {
 position: fixed;
 bottom: var(--spacing-lg);
 right: var(--spacing-lg);
 padding: var(--spacing-md) var(--spacing-xl);
 background-color: var(--color-gray-800);
 color: var(--color-white);
 border-radius: var(--border-radius);
 box-shadow: var(--shadow-lg);
 transform: translateY(100px);
 opacity: 0;
 transition: all 0.3s ease;
 z-index: 1001;
 }

 .toast.show {
 transform: translateY(0);
 opacity: 1;
 }

 .toast.success {
 background-color: var(--color-success);
 }

 .toast.error {
 background-color: #DC3545;
 }

 .toast.info {
 background-color: var(--color-info);
 }

 @media (max-width: 767px) {
 .container {
 padding: var(--spacing-md);
 }

 .header {
 padding: var(--spacing-md);
 }

 .header-content {
 flex-direction: column;
 align-items: flex-start;
 }

 .stats {
 width: 100%;
 justify-content: space-between;
 }

 .section-header {
 flex-direction: column;
 align-items: flex-start;
 }

 .filter-controls {
 width: 100%;
 }

 .filter-btn {
 flex: 1;
 justify-content: center;
 }

 .modal {
 width: 95%;
 max-height: 95vh;
 }

 .modal-header {
 padding: var(--spacing-md);
 }

 .modal-body {
 padding: var(--spacing-md);
 }

 .modal-footer {
 padding: var(--spacing-md);
 flex-direction: column;
 }

 .modal-footer .btn {
 width: 100%;
 }

 .toast {
 left: var(--spacing-md);
 right: var(--spacing-md);
 bottom: var(--spacing-md);
 }
 }

 .notification-badge {
 position: relative;
 }

 .notification-badge::after {
 content: attr(data-count);
 position: absolute;
 top: -8px;
 right: -8px;
 background-color: #DC3545;
 color: white;
 font-size: 11px;
 font-weight: 700;
 padding: 2px 6px;
 border-radius: 10px;
 min-width: 18px;
 text-align: center;
 }

 .post-card.approved {
 border-left: 4px solid var(--color-success);
 }

 .post-card.rejected {
 border-left: 4px solid var(--color-gray-500);
 }

 .post-card.pending {
 border-left: 4px solid var(--color-warning);
 }

 .loading {
 display: flex;
 justify-content: center;
 align-items: center;
 padding: var(--spacing-2xl);
 }

 .loading-spinner {
 width: 40px;
 height: 40px;
 border: 4px solid var(--color-gray-200);
 border-top-color: var(--color-primary);
 border-radius: 50%;
 animation: spin 1s linear infinite;
 }

 @keyframes spin {
 to {
 transform: rotate(360deg);
 }
 }
 </style>
</head>
<body>
 <div class="header">
 <div class="header-content">
 <div class="logo">
 <div class="logo-icon">C</div>
 <span>Catalyst Works</span>
 </div>
 <div class="stats">
 <div class="stat-item">
 <span>Total Posts:</span>
 <span class="stat-value" id="total-posts">0</span>
 </div>
 <div class="stat-item">
 <span>Pending:</span>
 <span class="stat-value" id="pending-count">0</span>
 </div>
 <div class="stat-item">
 <span>Approved:</span>
 <span class="stat-value" id="approved-count">0</span>
 </div>
 <div class="stat-item">
 <span>Rejected:</span>
 <span class="stat-value" id="rejected-count">0</span>
 </div>
 </div>
 </div>
 </div>

 <div class="container">
 <div class="main-content">
 <div class="posts-section">
 <div class="section-header">
 <h2 class="section-title">Content Board</h2>
 <div class="filter-controls">
 <button class="filter-btn active" data-filter="all">All</button>
 <button class="filter-btn" data-filter="pending">Pending</button>
 <button class="filter-btn" data-filter="approved">Approved</button>
 <button class="filter-btn" data-filter="rejected">Rejected</button>
 </div>
 </div>
 <div class="posts-list" id="posts-list">
 <div class="loading">
 <div class="loading-spinner"></div>
 </div>
 </div>
 </div>

 <aside class="sidebar">
 <h3 class="sidebar-title">Quick Actions</h3>
 <div class="approval-panel" id="approval-panel">
 <div class="empty-state">
 <div class="empty-state-icon">📋</div>
 <div class="empty-state-title">No Pending Items</div>
 <div class="empty-state-text">All posts have been reviewed</div>
 </div>
 </div>
 </aside>
 </div>
 </div>

 <div class="modal-overlay" id="modal-overlay">
 <div class="modal">
 <div class="modal-header">
 <h3 class="modal-title" id="modal-title">Post Title</h3>
 <button class="modal-close" id="modal-close">&times;</button>
 </div>
 <div class="modal-body">
 <div class="modal-content" id="modal-content"></div>
 </div>
 <div class="modal-footer">
 <button class="btn btn-secondary" id="modal-close-btn">Close</button>
 <button class="btn btn-success" id="modal-approve-btn">Approve</button>
 <button class="btn btn-danger" id="modal-reject-btn">Reject</button>
 </div>
 </div>
 </div>

 <div class="toast" id="toast"></div>

 <script>
 // Sample data - In production, this would come from an API
 const samplePosts = [
 {
 id: 1,
 title: "The hidden factory is killing your margin",
 content: "Every business has a hidden factory - the invisible processes that consume resources without generating value. These include:\n\n• Excessive approval layers that slow decision-making\n• Redundant meetings that could be emails\n• Manual data entry that automation could handle\n• Over-engineered solutions to simple problems\n• Compliance overhead that doesn't add customer value\n\nThe key to unlocking margin is identifying and eliminating these hidden costs. Start by mapping your value stream and asking: does this activity directly create customer value?\n\nMost companies find that 20-30% of their activities fall into this category. Eliminating them can improve margins by 5-15% without any revenue growth.\n\nAction steps:\n1. Map your top 5 processes\n2. Identify waste in each\n3. Create elimination plans\n4. Track results monthly",
 author: "Sarah Chen",
 createdAt: "2024-01-15T10:30:00Z",
 status: "pending",
 category: "Strategy",
 tags: ["efficiency", "margins", "operations"]
 },
 {
 id: 2,
 title: "Q1 Customer Retention Strategy",
 content: "Our customer retention rate dropped 3% last quarter. Here's the comprehensive plan to reverse this trend:\n\n1. IDENTIFY AT-RISK CUSTOMERS\n - Implement predictive churn scoring\n - Flag customers with declining engagement\n - Create early warning system\n\n2. RE-ENGAGEMENT CAMPAIGNS\n - Personalized outreach for at-risk accounts\n - Value reinforcement messaging\n - Exclusive benefits for loyal customers\n\n3. PRODUCT IMPROVEMENTS\n - Address top 3 customer complaints\n - Accelerate feature roadmap\n - Improve onboarding experience\n\n4. SUCCESS PROGRAM\n - Dedicated success managers for enterprise\n - Quarterly business reviews\n - Customer advisory board\n\nExpected outcomes:\n- 5% improvement in retention\n- 15% increase in NPS\n- 20% reduction in churn calls",
 author: "Marcus Johnson",
 createdAt: "2024-01-14T14:20:00Z",
 status: "approved",
 category: "Customer Success",
 tags: ["retention", "strategy", "q1"]
 },
 {
 id: 3,
 title: "AI Integration Roadmap 2024",
 content: "Strategic roadmap for AI integration across our product suite:\n\nPHASE 1: FOUNDATION (Q1-Q2)\n• AI-powered search and recommendations\n• Chatbot for customer support\n• Automated content tagging\n\nPHASE 2: ENHANCEMENT (Q3)\n• Predictive analytics dashboard\n• Smart document processing\n• Automated reporting\n\nPHASE 3: TRANSFORMATION (Q4)\n• AI-driven product recommendations\n• Intelligent workflow automation\n• Personalized user experiences\n\nBUDGET ALLOCATION:\n• Infrastructure: 40%\n• Development: 35%\n• Training: 15%\n• Contingency: 10%\n\nSUCCESS METRICS:\n• 30% reduction in support tickets\n• 25% improvement in user engagement\n• 20% increase in conversion rates",
 author: "Emily Rodriguez",
 createdAt: "2024-01-13T09:15:00Z",
 status: "rejected",
 category: "Product",
 tags: ["ai", "roadmap", "innovation"]
 },
 {
 id: 4,
 title: "Team Structure Optimization",
 content: "Proposal to reorganize our engineering teams for better efficiency:\n\nCURRENT STATE:\n• 4 teams of 8 engineers each\n• Cross-team dependencies causing delays\n• Limited specialization\n\nPROPOSED STRUCTURE:\n• 6 domain-focused teams (4-5 engineers each)\n• Platform team for shared infrastructure\n• Embedded product liaisons\n\nBENEFITS:\n• 40% reduction in cross-team dependencies\n• Faster decision-making\n• Better domain expertise\n• Improved code ownership\n\nTRANSITION PLAN:\n• Week 1-2: Team formation\n• Week 3-4: Knowledge transfer\n• Week 5-8: Parallel run\n• Week 9+: Full transition\n\nRISK MITIGATION:\n• Maintain documentation standards\n• Regular sync meetings during transition\n• Buffer capacity for knowledge gaps",
 author: "David Park",
 createdAt: "2024-01-12T16:45:00Z",
 status: "pending",
 category: "Operations",
 tags: ["team", "structure", "efficiency"]
 },
 {
 id: 5,
 title: "Marketing Campaign Performance Review",
 content: "Q4 marketing campaign analysis and learnings:\n\nCAMPAIGN OVERVIEW:\n• Total spend: $125,000\n• Leads generated: 2,847\n• Cost per lead: $43.90\n• Conversion rate: 12.3%\n\nTOP PERFORMING CHANNELS:\n1. LinkedIn Ads - CPL: $38, CTR: 2.8%\n2. Content Marketing - CPL: $22, CTR: 4.1%\n3. Email Campaigns - CPL: $15, CTR: 5.2%\n\nKEY LEARNINGS:\n• Video content outperformed static by 3x\n• Personalized messaging increased conversion by 40%\n• A/B testing revealed optimal send times\n• Mobile-first approach critical for engagement\n\nRECOMMENDATIONS:\n• Increase video content budget by 50%\n• Implement dynamic content personalization\n• Expand email automation workflows\n• Invest in mobile optimization\n\nNEXT QUARTER FOCUS:\n• Account-based marketing pilot\n• Influencer partnership program\n• Customer advocacy initiative",
 author: "Lisa Thompson",
 createdAt: "2024-01-11T11:00:00Z",
 status: "approved",
 category: "Marketing",
 tags: ["campaign", "performance", "q4"]
 }
 ];

 // State management
 let posts = [...samplePosts];
 let currentFilter = 'all';
 let selectedPost = null;

 // DOM Elements
 const postsList = document.getElementById('posts-list');
 const approvalPanel = document.getElementById('approval-panel');
 const modalOverlay = document.getElementById('modal-overlay');
 const modalTitle = document.getElementById('modal-title');
 const modalContent = document.getElementById('modal-content');
 const modalClose = document.getElementById('modal-close');
 const modalCloseBtn = document.getElementById('modal-close-btn');
 const modalApproveBtn = document.getElementById('modal-approve-btn');
 const modalRejectBtn = document.getElementById('modal-reject-btn');
 const filterBtns = document.querySelectorAll('.filter-btn');
 const toast = document.getElementById('toast');
 const totalPostsEl = document.getElementById('total-posts');
 const pendingCountEl = document.getElementById('pending-count');
 const approvedCountEl = document.getElementById('approved-count');
 const rejectedCountEl = document.getElementById('rejected-count');

 // Initialize
 function init() {
 renderPosts();
 updateStats();
 setupEventListeners();
 }

 // Setup event listeners
 function setupEventListeners() {
 filterBtns.forEach(btn => {
 btn.addEventListener('click', () => {
 filterBtns.forEach(b => b.classList.remove('active'));
 btn.classList.add('active');
 currentFilter = btn.dataset.filter;
 renderPosts();
 });
 });

 modalClose.addEventListener('click', closeModal);
 modalCloseBtn.addEventListener('click', closeModal);
 modalApproveBtn.addEventListener('click', () => handleApproval('approved'));
 modalRejectBtn.addEventListener('click', () => handleApproval('rejected'));

 modalOverlay.addEventListener('click', (e) => {
 if (e.target === modalOverlay) closeModal();
 });

 document.addEventListener('keydown', (e) => {
 if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
 closeModal();
 }
 });
 }

 // Render posts
 function renderPosts() {
 const filteredPosts = posts.filter(post => {
 if (currentFilter === 'all') return true;
 return post.status === currentFilter;
 });

 if (filteredPosts.length === 0) {
 postsList.innerHTML = `
 <div class="empty-state">
 <div class="empty-state-icon">📭</div>
 <div class="empty-state-title">No Posts Found</div>
 <div class="empty-state-text">No posts match the current filter</div>
 </div>
 `;
 return;
 }

 postsList.innerHTML = filteredPosts.map(post => createPostCard(post)).join('');
 }

 // Create post card HTML
 function createPostCard(post) {
 const statusClass = post.status;
 const statusText = post.status.charAt(0).toUpperCase() + post.status.slice(1);
 const date = new Date(post.createdAt).toLocaleDateString('en-US', {
 year: 'numeric',
 month: 'short',
 day: 'numeric'
 });

 return `
 <div class="post-card ${statusClass}" data-post-id="${post.id}">
 <div class="post-header">
 <div>
 <h3 class="post-title">${post.title}</h3>
 <div class="post-meta">
 <span>👤 ${post.author}</span>
 <span>📅 ${date}</span>
 <span>📁 ${post.category}</span>
 </div>
 </div>
 <span class="status-badge status-${post.status}">${statusText}</span>
 </div>
 <p class="post-preview">${post.content.substring(0, 200)}...</p>
 <div class="post-actions">
 <button class="btn btn-primary" onclick="openPost(${post.id})">View Full Post</button>
 ${post.status === 'pending' ? `
 <button class="btn btn-success" onclick="handleQuickApproval(${post.id}, 'approved')">Approve</button>
 <button class="btn btn-danger" onclick="handleQuickApproval(${post.id}, 'rejected')">Reject</button>
 ` : ''}
 </div>
 </div>
 `;
 }

 // Update statistics
 function updateStats() {
 totalPostsEl.textContent = posts.length;
 pendingCountEl.textContent = posts.filter(p => p.status === 'pending').length;
 approvedCountEl.textContent = posts.filter(p => p.status === 'approved').length;
 rejectedCountEl.textContent = posts.filter(p => p.status === 'rejected').length;
 renderApprovalPanel();
 }

 // Render approval panel
 function renderApprovalPanel() {
 const pendingPosts = posts.filter(p => p.status === 'pending');

 if (pendingPosts.length === 0) {
 approvalPanel.innerHTML = `
 <div class="empty-state">
 <div class="empty-state-icon">✅</div>
 <div class="empty-state-title">All Caught Up!</div>
 <div class="empty-state-text">No pending posts to review</div>
 </div>
 `;
 return;
 }

 approvalPanel.innerHTML = pendingPosts.map(post => `
 <div class="approval-item">
 <div class="approval-item-title">${post.title}</div>
 <div class="approval-item-meta">
 By ${post.author} • ${new Date(post.createdAt).toLocaleDateString()}
 </div>
 <div class="approval-actions">
 <button class="btn btn-success" onclick="handleQuickApproval(${post.id}, 'approved')">Approve</button>
 <button class="btn btn-danger" onclick="handleQuickApproval(${post.id}, 'rejected')">Reject</button>
 </div>
 </div>
 `).join('');
 }

 // Open post modal
 function openPost(postId) {
 selectedPost = posts.find(p => p.id === postId);
 if (!selectedPost) return;

 modalTitle.textContent = selectedPost.title;
 modalContent.textContent = selectedPost.content;
 modalOverlay.classList.add('active');
 }

 // Close modal
 function closeModal() {
 modalOverlay.classList.remove('active');
 selectedPost = null;
 }

 // Handle approval
 function handleApproval(status) {
 if (!selectedPost) return;

 selectedPost.status = status;
 showToast(`Post "${selectedPost.title}" has been ${status}`, 'success');
 closeModal();
 renderPosts();
 updateStats();
 }

 // Quick approval from card
 function handleQuickApproval(postId, status) {
 const post = posts.find(p => p.id === postId);
 if (!post) return;

 post.status = status;
 showToast(`Post "${post.title}" has been ${status}`, 'success');
 renderPosts();
 updateStats();
 }

 // Show toast notification
 function showToast(message, type = 'info') {
 toast.textContent = message;
 toast.className = `toast ${type} show`;

 setTimeout(() => {
 toast.classList.remove('show');
 }, 3000);
 }

 // Initialize the app
 init();
 </script>
</body>
</html>
```