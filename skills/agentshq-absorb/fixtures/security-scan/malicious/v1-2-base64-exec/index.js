// FIXTURE: v1-2 base64/decode-exec pattern — DO NOT RUN
// Pattern: Buffer.from(..., 'base64') + eval()
// Scan should flag: index.js:3 — Buffer.from.*base64 + eval chain — obfuscated payload delivery
//
// Actual malicious code would look like:
//   const payload = Buffer.from('cHJvY2Vzcy5leGl0KDEp', 'base64').toString();
//   eval(payload);
//
// The scan pattern to match: /Buffer\.from.*base64/  AND  /eval\s*\(/  within same file
