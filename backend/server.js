const express = require('express');
const { SuiClient, getFullnodeUrl } = require('@mysten/sui.js/client');
const { TransactionBlock } = require('@mysten/sui.js/transactions');
const { Ed25519Keypair } = require('@mysten/sui.js/keypairs/ed25519');
const { fromBase64 } = require('@mysten/sui.js/utils');
const { PythonShell } = require('python-shell');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const fs = require('fs');

class HorusBackend {
    constructor() {
        this.app = express();
        this.setupMiddleware();
        this.setupRoutes();
        this.initSuiClient();
        this.initAIEngine();
    }

    setupMiddleware() {
        this.app.use(helmet());
        this.app.use(cors());
        this.app.use(express.json({ limit: '10mb' }));
        
        // Rate limiting
        const limiter = rateLimit({
            windowMs: 15 * 60 * 1000, // 15 minutes
            max: 100 // limit each IP to 100 requests per windowMs
        });
        this.app.use(limiter);
        
        // Request logging
        this.app.use((req, res, next) => {
            console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
            next();
        });
    }

    initSuiClient() {
        try {
            this.suiClient = new SuiClient({ url: getFullnodeUrl('testnet') });
            
            // Load keypair from environment
            const privateKey = process.env.SUI_PRIVATE_KEY;
            if (!privateKey) {
                console.warn('SUI_PRIVATE_KEY not found in environment variables');
                return;
            }
            
            this.keypair = Ed25519Keypair.fromSecretKey(fromBase64(privateKey));
            
            this.packageId = process.env.PACKAGE_ID;
            this.horusSystemId = process.env.HORUS_SYSTEM_ID;
            
            console.log('Sui client initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Sui client:', error);
        }
    }

    initAIEngine() {
        try {
            // Initialize Python AI engine
            const pythonPath = path.join(__dirname, '../ai/horus-ai/Scripts/python.exe');
            
            this.aiEngine = new PythonShell('ai/anomaly_detector.py', {
                mode: 'json',
                pythonPath: pythonPath,
                pythonOptions: ['-u'] // unbuffered output
            });

            this.aiEngine.on('message', (message) => {
                console.log('AI Engine:', message);
            });
            
            this.aiEngine.on('error', (error) => {
                console.error('AI Engine Error:', error);
            });
            
            this.aiEngine.on('close', () => {
                console.log('AI Engine process closed');
            });

            console.log('AI Engine initialized');
        } catch (error) {
            console.error('Failed to initialize AI engine:', error);
        }
    }

    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({ 
                status: 'healthy', 
                timestamp: Date.now(),
                version: '1.0.0'
            });
        });

        // Record transaction
        this.app.post('/transaction', async (req, res) => {
            try {
                const transaction = req.body;
                const result = await this.processTransaction(transaction);
                res.json(result);
            } catch (error) {
                console.error('Transaction processing error:', error);
                res.status(500).json({ error: error.message });
            }
        });

        // Get system info
        this.app.get('/system/info', async (req, res) => {
            try {
                const info = await this.getSystemInfo();
                res.json(info);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });

        // Test anomaly detection
        this.app.post('/detect', async (req, res) => {
            try {
                const transaction = req.body;
                const result = await this.testDetection(transaction);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });
    }

    async processTransaction(transactionData) {
        // Simulate AI analysis (will be integrated with actual AI later)
        const aiResult = {
            score: Math.random(),
            risk_level: Math.random() > 0.8 ? 'HIGH' : 'LOW',
            explanation: 'Simulated analysis',
            features: [1, 2, 3, 4, 5]
        };

        return {
            transactionId: transactionData.id || Date.now(),
            status: 'processed',
            aiAnalysis: aiResult,
            timestamp: Date.now(),
            message: 'Transaction processed successfully (simulation)'
        };
    }

    async testDetection(transactionData) {
        return new Promise((resolve, reject) => {
            if (!this.aiEngine) {
                reject(new Error('AI Engine not initialized'));
                return;
            }

            const timeout = setTimeout(() => {
                reject(new Error('AI analysis timeout'));
            }, 10000);

            this.aiEngine.send(JSON.stringify({
                type: 'detect_anomaly',
                data: transactionData
            }));

            this.aiEngine.once('message', (message) => {
                clearTimeout(timeout);
                try {
                    const result = JSON.parse(message);
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            });

            this.aiEngine.once('error', (error) => {
                clearTimeout(timeout);
                reject(error);
            });
        });
    }

    async getSystemInfo() {
        return {
            name: 'HORUS Anomaly Detection System',
            version: '1.0.0',
            status: 'operational',
            blockchain: {
                connected: !!this.suiClient,
                network: 'testnet'
            },
            ai: {
                initialized: !!this.aiEngine,
                status: 'ready'
            },
            timestamp: Date.now()
        };
    }

    start(port = 3000) {
        this.server = this.app.listen(port, () => {
            console.log(`HORUS Backend running on port ${port}`);
            console.log(`Health check: http://localhost:${port}/health`);
            console.log(`System info: http://localhost:${port}/system/info`);
        });

        // Graceful shutdown
        process.on('SIGTERM', () => this.gracefulShutdown());
        process.on('SIGINT', () => this.gracefulShutdown());
    }

    async gracefulShutdown() {
        console.log('Shutting down HORUS backend gracefully...');
        
        if (this.aiEngine) {
            this.aiEngine.end(() => {
                console.log('AI Engine stopped');
            });
        }
        
        if (this.server) {
            this.server.close(() => {
                console.log('HTTP server closed');
                process.exit(0);
            });
        }
    }
}

// Create and start server
const backend = new HorusBackend();
backend.start(process.env.PORT || 3000);

module.exports = HorusBackend;