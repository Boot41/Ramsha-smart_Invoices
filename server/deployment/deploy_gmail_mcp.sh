#!/bin/bash

# Deploy Gmail MCP Server to Google Cloud Run
# This script sets up and deploys the Gmail MCP server

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-arcane-storm-443513-r8}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="gmail-mcp-server"
IMAGE_NAME="gcr.io/$PROJECT_ID/gmail-mcp-server"

echo "🚀 Deploying Gmail MCP Server to Cloud Run..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Create Gmail OAuth secrets (if not exist)
echo "🔐 Setting up OAuth secrets..."
if ! gcloud secrets describe gmail-oauth-secrets >/dev/null 2>&1; then
    echo "Creating gmail-oauth-secrets..."
    
    # Create temporary secret file
    cat > /tmp/gmail_secrets.json << EOF
{
    "client_id": "${GOOGLE_CLIENT_ID}",
    "client_secret": "${GOOGLE_CLIENT_SECRET}"
}
EOF
    
    # Create the secret
    gcloud secrets create gmail-oauth-secrets --data-file=/tmp/gmail_secrets.json
    
    # Clean up temp file
    rm /tmp/gmail_secrets.json
    
    echo "✅ Gmail OAuth secrets created"
else
    echo "✅ Gmail OAuth secrets already exist"
fi

# Clone and build Gmail MCP server
echo "🏗️ Building Gmail MCP Server..."

# Create a temporary directory for building
BUILD_DIR="/tmp/gmail-mcp-build"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# Clone the Gmail MCP server repository
echo "Cloning Gmail MCP Server repository..."
git clone https://github.com/GongRzhe/Gmail-MCP-Server.git .

# Create Dockerfile if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo "Creating Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM node:18-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Set environment variable for port
ENV PORT=8080

# Start the application
CMD ["npm", "start"]
EOF
fi

# Ensure package.json exists and has start script
if [ ! -f package.json ]; then
    echo "Creating package.json..."
    cat > package.json << 'EOF'
{
  "name": "gmail-mcp-server",
  "version": "1.0.0",
  "description": "Gmail MCP Server for sending emails",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "googleapis": "^126.0.0",
    "cors": "^2.8.5"
  }
}
EOF
fi

# Create basic MCP server implementation if index.js doesn't exist
if [ ! -f index.js ]; then
    echo "Creating basic MCP server implementation..."
    cat > index.js << 'EOF'
const express = require('express');
const { google } = require('googleapis');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 8080;

// Middleware
app.use(cors());
app.use(express.json());

// Gmail API setup
const gmail = google.gmail('v1');

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        service: 'Gmail MCP Server',
        timestamp: new Date().toISOString()
    });
});

// Send email endpoint
app.post('/gmail/send', async (req, res) => {
    try {
        const { params, credentials } = req.body;
        const { to, subject, body_html, body_text, cc, bcc } = params;
        const { access_token } = credentials;

        // Set up OAuth2 client
        const oauth2Client = new google.auth.OAuth2();
        oauth2Client.setCredentials({ access_token });

        // Create email message
        const email = [
            `To: ${to}`,
            `Subject: ${subject}`,
            cc && cc.length > 0 ? `Cc: ${cc.join(', ')}` : '',
            bcc && bcc.length > 0 ? `Bcc: ${bcc.join(', ')}` : '',
            'Content-Type: text/html; charset="UTF-8"',
            'MIME-Version: 1.0',
            '',
            body_html || body_text
        ].filter(line => line !== '').join('\r\n');

        const encodedEmail = Buffer.from(email).toString('base64')
            .replace(/\+/g, '-')
            .replace(/\//g, '_')
            .replace(/=+$/, '');

        // Send email
        const result = await gmail.users.messages.send({
            auth: oauth2Client,
            userId: 'me',
            requestBody: {
                raw: encodedEmail
            }
        });

        res.json({
            success: true,
            message: 'Email sent successfully',
            messageId: result.data.id
        });

    } catch (error) {
        console.error('Error sending email:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to send email',
            error: error.message
        });
    }
});

// Start server
app.listen(port, () => {
    console.log(`Gmail MCP Server running on port ${port}`);
});
EOF
fi

# Build and push Docker image
echo "📦 Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="PORT=8080" \
    --set-secrets="GOOGLE_CLIENT_ID=gmail-oauth-secrets:latest:client_id" \
    --set-secrets="GOOGLE_CLIENT_SECRET=gmail-oauth-secrets:latest:client_secret" \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=300

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo "✅ Gmail MCP Server deployed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "🔗 Health check: $SERVICE_URL/health"
echo "📧 Send email endpoint: $SERVICE_URL/gmail/send"
echo ""
echo "📝 Next steps:"
echo "1. Test the health endpoint: curl $SERVICE_URL/health"
echo "2. Update your .env file with: GMAIL_MCP_SERVER_URL=$SERVICE_URL"
echo "3. Complete OAuth2 flow to get refresh tokens"

# Clean up build directory
cd /
rm -rf $BUILD_DIR

echo "🎉 Deployment complete!"