// DRAFT n8n workflow code for the n8n MCP create_workflow_from_code tool.
// Pre-staged 2026-04-30 (rev 3 after reading n8n://workflow-sdk/reference).
// Validate via mcp__claude_ai_n8n__validate_workflow before creating.
//
// Pattern: hybrid of two existing workflows
//   - "Inbound Lead / Calendly -> agentsHQ" (VmikWwt8kIR3rXoy): the
//     Set-then-HttpRequest shape that posts to /inbound-lead with X-API-Key
//   - "catalystworks.consulting Contact Form" (IeSWirZ2W5DW1qvH): the
//     webhook trigger pattern
//
// Differences from those templates:
//   - responseMode: 'responseNode' (sync; browser holds connection)
//   - Adds Respond to Webhook node so the browser receives the score JSON
//   - Posts to /score-request, not /inbound-lead

import { workflow, node, trigger, newCredential, expr } from '@n8n/workflow-sdk';

const orcApiKey = newCredential('agentsHQ Orchestrator API Key');

const scoreWebhook = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Score Request Webhook',
    parameters: {
      httpMethod: 'POST',
      path: 'geolisted-score',
      responseMode: 'responseNode',
      options: {
        allowedOrigins: 'https://geolisted.co',
      },
    },
    position: [240, 304],
  },
  output: [{
    body: {
      name: 'Jane Doe',
      business: 'Bright Smiles Pediatric Dentistry',
      email: 'jane@example.com',
      city: 'Provo, UT',
      niche: 'pediatric dentist',
      website_url: 'https://example.com',
    },
  }],
});

const shapePayload = node({
  type: 'n8n-nodes-base.set',
  version: 3.4,
  config: {
    name: 'Shape Score Payload',
    parameters: {
      mode: 'manual',
      assignments: {
        assignments: [
          { id: '1', name: 'name', value: expr('{{ $json.body.name }}'), type: 'string' },
          { id: '2', name: 'business', value: expr('{{ $json.body.business }}'), type: 'string' },
          { id: '3', name: 'email', value: expr('{{ $json.body.email }}'), type: 'string' },
          { id: '4', name: 'city', value: expr('{{ $json.body.city }}'), type: 'string' },
          { id: '5', name: 'niche', value: expr('{{ $json.body.niche }}'), type: 'string' },
          { id: '6', name: 'website_url', value: expr('{{ $json.body.website_url || "" }}'), type: 'string' },
          { id: '7', name: 'source', value: 'geolisted.co - Score Request', type: 'string' },
        ],
      },
    },
    position: [544, 304],
  },
  output: [{
    name: 'Jane Doe',
    business: 'Bright Smiles Pediatric Dentistry',
    email: 'jane@example.com',
    city: 'Provo, UT',
    niche: 'pediatric dentist',
    website_url: 'https://example.com',
    source: 'geolisted.co - Score Request',
  }],
});

const postToOrchestrator = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: 'POST to agentsHQ /score-request',
    parameters: {
      method: 'POST',
      url: 'http://orc-crewai:8000/score-request',
      authentication: 'genericCredentialType',
      genericAuthType: 'httpHeaderAuth',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify($json) }}'),
      options: {
        timeout: 90000,
      },
    },
    credentials: { httpHeaderAuth: orcApiKey },
    position: [848, 304],
  },
  output: [{
    score: 25,
    breakdown: { chatgpt: false, perplexity: false, robots_ok: true, maps_present: false },
    quick_wins: [
      'Strengthen Google Maps presence',
      'Add structured data to your site',
      'Build topical authority content',
    ],
    business: 'Bright Smiles Pediatric Dentistry',
    city: 'Provo, UT',
    niche: 'pediatric dentist',
    lead_id: '12345',
    email_status: 'drafted',
  }],
});

const respondToBrowser = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Return Score to Browser',
    parameters: {
      respondWith: 'json',
      responseBody: expr('{{ JSON.stringify($json) }}'),
      options: {
        responseCode: 200,
        responseHeaders: {
          entries: [
            { name: 'Access-Control-Allow-Origin', value: 'https://geolisted.co' },
          ],
        },
      },
    },
    position: [1152, 304],
  },
  output: [{
    score: 25,
    breakdown: { chatgpt: false, perplexity: false, robots_ok: true, maps_present: false },
    quick_wins: ['Strengthen Google Maps presence'],
    business: 'Bright Smiles Pediatric Dentistry',
  }],
});

export default workflow('geolisted-score', 'geolisted.co Score Request → agentsHQ')
  .add(scoreWebhook)
  .to(shapePayload)
  .to(postToOrchestrator)
  .to(respondToBrowser);
