// Import required modules
const express = require('express');
const https = require('https');
const fs = require('fs');
const app = require('./src/app'); // Your existing Express app

// SSL options
const sslOptions = {
  cert: fs.readFileSync('/etc/ssl/cloudflare/origin-certificate.pem'),
  key: fs.readFileSync('/etc/ssl/cloudflare/private-key.pem')
};

// Define ports
const HTTPS_PORT = 3443; // New HTTPS port

// Start HTTPS server
const httpsServer = https.createServer(sslOptions, app);
httpsServer.listen(HTTPS_PORT, () => {
  console.log(`HTTPS Server running on port ${HTTPS_PORT}`);
});