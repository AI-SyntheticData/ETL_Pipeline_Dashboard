#!/usr/bin/env python3
"""
Human Review and Feedback System
Captures user feedback and review decisions on AML alerts
"""

from datetime import datetime
import json
import os


class FeedbackManager:
    """Manages human feedback and review decisions"""

    def __init__(self, feedback_dir='feedback'):
        self.feedback_dir = feedback_dir
        os.makedirs(feedback_dir, exist_ok=True)
        self.feedback_records = []

    def record_feedback(self, account_id, reviewer_email, reviewer_role,
                       decision, confidence_adjustment=None, comments=None,
                       action_taken=None, risk_override=None):
        """Record feedback from a human reviewer"""

        feedback = {
            'feedback_id': f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.feedback_records)}",
            'timestamp': datetime.now().isoformat(),
            'account_id': account_id,
            'reviewer': {
                'email': reviewer_email,
                'role': reviewer_role
            },
            'decision': decision,  # e.g., 'APPROVE', 'REJECT', 'ESCALATE', 'NEEDS_MORE_INFO'
            'confidence_adjustment': confidence_adjustment,  # e.g., +10, -20
            'risk_override': risk_override,  # e.g., 'HIGH' to 'LOW'
            'action_taken': action_taken,  # e.g., 'SAR_FILED', 'ACCOUNT_FROZEN', 'CLEARED'
            'comments': comments,
            'ip_address': None  # Would be populated in web app
        }

        self.feedback_records.append(feedback)
        return feedback

    def save_feedback(self, batch_id=None):
        """Save feedback records to file"""
        if not batch_id:
            batch_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        filename = f"feedback_{batch_id}.json"
        filepath = os.path.join(self.feedback_dir, filename)

        # Load existing feedback if file exists
        existing_feedback = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_feedback = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_feedback = []

        # Merge existing with new feedback
        all_feedback = existing_feedback + self.feedback_records

        # Save all feedback
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(all_feedback, f, indent=2)

        print(f"✓ Feedback saved to: {filepath}")

        # Clear the current records since they're now saved
        self.feedback_records = []

        return filepath

    def load_feedback(self, batch_id):
        """Load feedback records from file"""
        filename = f"feedback_{batch_id}.json"
        filepath = os.path.join(self.feedback_dir, filename)

        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                self.feedback_records = json.load(f)
            return self.feedback_records
        return []

    def get_feedback_for_account(self, account_id):
        """Get all feedback for a specific account"""
        return [f for f in self.feedback_records if f['account_id'] == account_id]

    def get_feedback_summary(self):
        """Get summary statistics of feedback"""
        if not self.feedback_records:
            return None

        decisions = {}
        actions = {}
        by_role = {}

        for feedback in self.feedback_records:
            # Count decisions
            decision = feedback['decision']
            decisions[decision] = decisions.get(decision, 0) + 1

            # Count actions
            action = feedback.get('action_taken')
            if action:
                actions[action] = actions.get(action, 0) + 1

            # Count by role
            role = feedback['reviewer']['role']
            by_role[role] = by_role.get(role, 0) + 1

        return {
            'total_reviews': len(self.feedback_records),
            'decisions': decisions,
            'actions_taken': actions,
            'reviews_by_role': by_role,
            'latest_review': self.feedback_records[-1]['timestamp'] if self.feedback_records else None
        }


def add_feedback_to_dashboard(dashboard_html):
    """Add feedback collection UI to dashboard HTML"""

    feedback_ui = """
    <style>
        .feedback-section {
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .feedback-form {
            display: grid;
            gap: 15px;
            max-width: 600px;
        }
        .feedback-form label {
            font-weight: bold;
            display: block;
            margin-bottom: 5px;
        }
        .feedback-form select,
        .feedback-form textarea,
        .feedback-form input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }
        .feedback-form textarea {
            min-height: 100px;
            resize: vertical;
        }
        .feedback-form button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        .feedback-form button:hover {
            background: #0056b3;
        }
        .feedback-history {
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 4px;
        }
        .feedback-item {
            border-left: 4px solid #007bff;
            padding: 10px;
            margin: 10px 0;
            background: #f8f9fa;
        }
        .feedback-item strong {
            color: #007bff;
        }
    </style>
    
    <div class="feedback-section">
        <h3>👤 Human Review & Feedback</h3>
        <p>Provide your expert review and feedback on this analysis</p>
        
        <form class="feedback-form" id="feedbackForm">
            <div>
                <label for="decision">Review Decision:</label>
                <select id="decision" name="decision" required>
                    <option value="">-- Select Decision --</option>
                    <option value="APPROVE">✅ Approve - No Issues</option>
                    <option value="ESCALATE">⚠️ Escalate - Needs Investigation</option>
                    <option value="SAR_REQUIRED">🚨 SAR Required</option>
                    <option value="FALSE_POSITIVE">❌ False Positive</option>
                    <option value="NEEDS_MORE_INFO">ℹ️ Needs More Information</option>
                </select>
            </div>
            
            <div>
                <label for="action">Action Taken:</label>
                <select id="action" name="action">
                    <option value="">-- Select Action --</option>
                    <option value="SAR_FILED">SAR Filed</option>
                    <option value="ACCOUNT_FROZEN">Account Frozen</option>
                    <option value="CLEARED">Cleared/No Action</option>
                    <option value="ENHANCED_MONITORING">Enhanced Monitoring</option>
                    <option value="CUSTOMER_CONTACTED">Customer Contacted</option>
                    <option value="DOCUMENTS_REQUESTED">Documents Requested</option>
                </select>
            </div>
            
            <div>
                <label for="riskOverride">Risk Level Override (optional):</label>
                <select id="riskOverride" name="riskOverride">
                    <option value="">-- Keep Current Risk Level --</option>
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                </select>
            </div>
            
            <div>
                <label for="comments">Comments/Notes:</label>
                <textarea id="comments" name="comments" placeholder="Provide detailed reasoning for your decision..."></textarea>
            </div>
            
            <button type="submit">Submit Review</button>
        </form>
        
        <div class="feedback-history" id="feedbackHistory" style="display:none;">
            <h4>📝 Previous Reviews</h4>
            <div id="feedbackList"></div>
        </div>
    </div>
    
    <script>
        // Get current user role from page title or meta tag
        function getCurrentUserRole() {
            // Extract role from dashboard title (e.g., "Accessible ETL Pipeline UI dashboard - Compliance Officer")
            const title = document.title;
            if (title.includes('Compliance Officer')) return 'Compliance Officer';
            if (title.includes('Risk Analyst')) return 'Risk Analyst';
            if (title.includes('Regulatory Officer')) return 'Regulatory Officer';
            if (title.includes('Administrator')) return 'Administrator';
            return 'Unknown';
        }
        
        // Get role-specific localStorage key
        function getFeedbackStorageKey() {
            const role = getCurrentUserRole();
            return `feedbackHistory_${role.replace(/\s+/g, '_')}`;
        }
        
        // Feedback form submission handler
        document.getElementById('feedbackForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const currentRole = getCurrentUserRole();
            const formData = {
                account_id: 'DASHBOARD_VIEW',  // Could be extracted from page context
                decision: document.getElementById('decision').value,
                action: document.getElementById('action').value,
                riskOverride: document.getElementById('riskOverride').value,
                comments: document.getElementById('comments').value
            };
            
            try {
                // Submit to backend API
                const response = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Save to role-specific localStorage for display
                    const storageKey = getFeedbackStorageKey();
                    let feedbackHistory = JSON.parse(localStorage.getItem(storageKey) || '[]');
                    feedbackHistory.push({
                        ...formData,
                        timestamp: new Date().toISOString(),
                        feedback_id: result.feedback_id,
                        role: currentRole
                    });
                    localStorage.setItem(storageKey, JSON.stringify(feedbackHistory));
                    
                    // Show success message
                    alert('✅ Feedback submitted successfully!\\nFeedback ID: ' + result.feedback_id + '\\nRole: ' + currentRole);
                    
                    // Reset form
                    this.reset();
                    
                    // Reload feedback history
                    loadFeedbackHistory();
                } else {
                    alert('❌ Error: ' + result.message);
                }
            } catch (error) {
                console.error('Error submitting feedback:', error);
                alert('❌ Failed to submit feedback. Please try again.');
            }
        });
        
        // Load and display feedback history (role-specific)
        function loadFeedbackHistory() {
            const storageKey = getFeedbackStorageKey();
            const currentRole = getCurrentUserRole();
            const feedbackHistory = JSON.parse(localStorage.getItem(storageKey) || '[]');
            const historyDiv = document.getElementById('feedbackHistory');
            const listDiv = document.getElementById('feedbackList');
            
            if (feedbackHistory.length > 0) {
                historyDiv.style.display = 'block';
                listDiv.innerHTML = `
                    <div style="background: #e3f2fd; padding: 8px; border-radius: 4px; margin-bottom: 10px;">
                        <strong>Showing feedback for: ${currentRole}</strong>
                    </div>
                ` + feedbackHistory.map((fb, idx) => `
                    <div class="feedback-item">
                        <strong>${fb.decision}</strong> - ${new Date(fb.timestamp).toLocaleString()}
                        ${fb.action ? `<br>Action: ${fb.action}` : ''}
                        ${fb.riskOverride ? `<br>Risk Override: ${fb.riskOverride}` : ''}
                        ${fb.comments ? `<br>Comments: ${fb.comments}` : ''}
                        ${fb.feedback_id ? `<br><small>ID: ${fb.feedback_id}</small>` : ''}
                    </div>
                `).reverse().join('');
            } else {
                historyDiv.style.display = 'none';
            }
        }
        
        // Load on page load
        loadFeedbackHistory();
    </script>
    """

    # Insert before closing body tag
    if '</body>' in dashboard_html:
        dashboard_html = dashboard_html.replace('</body>', feedback_ui + '</body>')
    else:
        dashboard_html += feedback_ui

    return dashboard_html


if __name__ == '__main__':
    # Example usage
    manager = FeedbackManager()

    # Record some sample feedback
    manager.record_feedback(
        account_id='ACC10001',
        reviewer_email='compliance@aml.com',
        reviewer_role='Compliance Officer',
        decision='ESCALATE',
        action_taken='SAR_FILED',
        comments='Multiple structuring patterns detected. Filed SAR with FinCEN.'
    )

    manager.record_feedback(
        account_id='ACC10002',
        reviewer_email='risk@aml.com',
        reviewer_role='Risk Analyst',
        decision='FALSE_POSITIVE',
        risk_override='LOW',
        comments='Customer provided valid documentation for large transactions.'
    )

    # Save feedback
    manager.save_feedback('20260102_demo')

    # Print summary
    summary = manager.get_feedback_summary()
    print("\nFeedback Summary:")
    print(json.dumps(summary, indent=2))

