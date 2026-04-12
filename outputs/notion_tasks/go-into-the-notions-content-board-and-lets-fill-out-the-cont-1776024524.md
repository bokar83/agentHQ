I'm hitting the same 400 error we just debugged with the KPI refresh. The Notion API integration has a malformed request or permission issue.

**What's happening:**
- The query to your Notion tasks database is failing at the API level
- This is the same root cause as the agentsHQ alert, either the integration token needs refreshing or the database ID `249bcf1a302980739c26c61cad212477` has permission/access issues

**To fix this:**
1. Verify the Notion integration token is still valid and has database query permissions
2. Confirm the database ID hasn't changed
3. Check that the integration has access to that specific database

I can't pull your tasks until the Notion connection is restored. You'll need to either:
- Refresh the API token in your agentsHQ/integration settings
- Or manually check Notion directly for overdue LinkedIn/X content tasks while we sort the API issue