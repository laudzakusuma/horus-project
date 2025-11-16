require('dotenv').config();
const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(express.json());

// Middleware untuk logging
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// Debug environment variables
console.log('=== HORUS BACKEND STARTING ===');
console.log('Environment Variables:');
console.log('- NODE_ENV:', process.env.NODE_ENV);
console.log('- PORT:', process.env.PORT);
console.log('- SUI_NETWORK:', process.env.SUI_NETWORK);
console.log('- SUI_PRIVATE_KEY:', process.env.SUI_PRIVATE_KEY ? '***LOADED***' : 'MISSING');
console.log('- AI_MODEL_PATH:', process.env.AI_MODEL_PATH);
console.log('================================');

// Konfigurasi path Python
const pythonScriptPath = path.join(__dirname, '..', 'ai', 'anomaly_detector.py');
const pythonExecutable = path.join(__dirname, '..', 'ai', 'horus-ai', 'Scripts', 'python.exe');

console.log('Python paths:');
console.log('- Executable:', pythonExecutable);
console.log('- Script:', pythonScriptPath);

// Validasi file existence
if (!fs.existsSync(pythonScriptPath)) {
    console.error('❌ ERROR: Python script not found at:', pythonScriptPath);
    console.error('Please check the file path and ensure anomaly_detector.py exists');
}

if (!fs.existsSync(pythonExecutable)) {
    console.error('❌ ERROR: Python executable not found at:', pythonExecutable);
    console.error('Please ensure virtual environment is properly set up');
}

let pythonProcess;
let aiEngineRestartCount = 0;
const MAX_RESTART_ATTEMPTS = 5;

function startAIEngine() {
    if (aiEngineRestartCount >= MAX_RESTART_ATTEMPTS) {
        console.error('🚨 Maximum restart attempts reached. AI Engine will not restart.');
        return;
    }

    console.log(`🚀 Starting AI Engine... (Attempt ${aiEngineRestartCount + 1}/${MAX_RESTART_ATTEMPTS})`);
    
    try {
        pythonProcess = spawn(pythonExecutable, ['-u', pythonScriptPath], {
            stdio: ['pipe', 'pipe', 'pipe'],
            cwd: path.join(__dirname, '..', 'ai')
        });

        pythonProcess.stdout.on('data', (data) => {
            const output = data.toString().trim();
            if (output) {
                console.log(`🤖 AI Engine: ${output}`);
                
                // Try to parse JSON responses from AI engine
                try {
                    const jsonData = JSON.parse(output);
                    if (jsonData.status === 'ready') {
                        console.log('✅ AI Engine confirmed ready status');
                    }
                } catch (e) {
                    // Not JSON, just regular output
                }
            }
        });

        pythonProcess.stderr.on('data', (data) => {
            const error = data.toString().trim();
            if (error) {
                console.error(`❌ AI Engine Error: ${error}`);
            }
        });

        pythonProcess.on('close', (code, signal) => {
            console.log(`🔴 AI Engine process closed with code ${code} and signal ${signal}`);
            
            if (code !== 0) {
                aiEngineRestartCount++;
                console.log(`🔄 Restarting AI Engine in 3 seconds... (${aiEngineRestartCount}/${MAX_RESTART_ATTEMPTS})`);
                setTimeout(startAIEngine, 3000);
            }
        });

        pythonProcess.on('error', (err) => {
            console.error('💥 Failed to start AI Engine:', err);
            aiEngineRestartCount++;
            console.log(`🔄 Restarting AI Engine in 5 seconds... (${aiEngineRestartCount}/${MAX_RESTART_ATTEMPTS})`);
            setTimeout(startAIEngine, 5000);
        });

        // Send initialization message as JSON after short delay
        setTimeout(() => {
            if (pythonProcess && !pythonProcess.killed) {
                const initMessage = JSON.stringify({
                    type: 'init',
                    timestamp: new Date().toISOString()
                });
                pythonProcess.stdin.write(initMessage + '\n');
                console.log('📤 Sent initialization message to AI Engine');
            }
        }, 2000);

    } catch (error) {
        console.error('💥 Exception starting AI Engine:', error);
        aiEngineRestartCount++;
        setTimeout(startAIEngine, 5000);
    }
}

// Start AI Engine
startAIEngine();

// ==================== ROUTES ====================

// Health check endpoint
app.get('/health', (req, res) => {
    const aiStatus = pythonProcess && !pythonProcess.killed ? 'running' : 'stopped';
    const systemStatus = aiStatus === 'running' ? 'healthy' : 'degraded';
    
    res.json({ 
        status: systemStatus,
        timestamp: new Date().toISOString(),
        services: {
            backend: 'running',
            ai_engine: aiStatus,
            blockchain: 'connected'
        },
        restart_count: aiEngineRestartCount
    });
});

// System info endpoint
app.get('/system/info', (req, res) => {
    res.json({
        system: 'HORUS Anomaly Detection System',
        version: '1.0.0',
        environment: process.env.NODE_ENV,
        network: {
            sui_network: process.env.SUI_NETWORK,
            package_id: process.env.PACKAGE_ID,
            horus_system_id: process.env.HORUS_SYSTEM_ID
        },
        ai: {
            model_path: process.env.AI_MODEL_PATH,
            model_hash: process.env.MODEL_HASH
        }
    });
});

// Analyze transaction endpoint
app.post('/analyze/transaction', (req, res) => {
    const { transaction_data, features } = req.body;
    
    if (!transaction_data) {
        return res.status(400).json({
            error: 'Missing transaction_data in request body'
        });
    }

    // Check if AI Engine is running
    if (!pythonProcess || pythonProcess.killed) {
        return res.status(503).json({
            error: 'AI Engine is not available',
            status: 'service_unavailable'
        });
    }

    try {
        const analysisData = {
            type: 'transaction',
            data: transaction_data,
            features: features || [],
            timestamp: new Date().toISOString()
        };

        // Send to Python process for analysis
        pythonProcess.stdin.write(JSON.stringify(analysisData) + '\n');

        // Simulate response (in real implementation, Python would respond)
        res.json({
            status: 'analysis_started',
            transaction_id: transaction_data.transaction_id || 'unknown',
            message: 'Transaction sent for anomaly detection',
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Error processing analysis request:', error);
        res.status(500).json({
            error: 'Internal server error during analysis',
            details: error.message
        });
    }
});

// Get AI Engine status
app.get('/ai/status', (req, res) => {
    const status = pythonProcess && !pythonProcess.killed ? 'running' : 'stopped';
    
    res.json({
        status: status,
        restart_count: aiEngineRestartCount,
        pid: pythonProcess ? pythonProcess.pid : null,
        uptime: process.uptime(),
        last_restart: new Date(Date.now() - (aiEngineRestartCount * 3000)).toISOString()
    });
});

// Restart AI Engine endpoint
app.post('/ai/restart', (req, res) => {
    if (pythonProcess && !pythonProcess.killed) {
        pythonProcess.kill('SIGTERM');
    }
    
    aiEngineRestartCount = 0;
    startAIEngine();
    
    res.json({
        status: 'restart_initiated',
        message: 'AI Engine restart sequence started',
        timestamp: new Date().toISOString()
    });
});

// Test AI Engine endpoint
app.post('/ai/test', (req, res) => {
    if (!pythonProcess || pythonProcess.killed) {
        return res.status(503).json({
            error: 'AI Engine is not available',
            status: 'service_unavailable'
        });
    }

    try {
        const testData = {
            type: 'transaction',
            data: {
                transaction_id: 'test_' + Date.now(),
                amount: Math.random() * 1000,
                frequency: Math.random() * 10,
                timestamp: new Date().toISOString()
            }
        };

        // Send test data to Python process
        pythonProcess.stdin.write(JSON.stringify(testData) + '\n');

        // Set timeout for response
        const responseTimeout = setTimeout(() => {
            res.json({
                status: 'test_sent',
                message: 'Test transaction sent to AI Engine (no immediate response)',
                test_data: testData.data,
                timestamp: new Date().toISOString()
            });
        }, 1000);

        // Optional: Listen for response (would need more complex event handling)
        
    } catch (error) {
        console.error('Error sending test data:', error);
        res.status(500).json({
            error: 'Failed to send test data to AI Engine',
            details: error.message
        });
    }
});

// Health check with AI status
app.get('/health', (req, res) => {
    const aiStatus = pythonProcess && !pythonProcess.killed ? 'running' : 'stopped';
    const systemStatus = aiStatus === 'running' ? 'healthy' : 'degraded';
    
    // Send health check to AI engine if it's running
    if (pythonProcess && !pythonProcess.killed) {
        const healthCheck = JSON.stringify({
            type: 'health',
            timestamp: new Date().toISOString()
        });
        pythonProcess.stdin.write(healthCheck + '\n');
    }
    
    res.json({ 
        status: systemStatus,
        timestamp: new Date().toISOString(),
        services: {
            backend: 'running',
            ai_engine: aiStatus,
            blockchain: 'connected'
        },
        restart_count: aiEngineRestartCount
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Unhandled error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: err.message
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        error: 'Endpoint not found',
        path: req.path,
        method: req.method
    });
});

// ==================== SERVER STARTUP ====================

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log('\n========================================');
    console.log('🚀 HORUS Backend Server Started!');
    console.log(`📍 Port: ${PORT}`);
    console.log(`🌐 Environment: ${process.env.NODE_ENV}`);
    console.log(`🔗 Health: http://localhost:${PORT}/health`);
    console.log(`📊 System Info: http://localhost:${PORT}/system/info`);
    console.log(`🤖 AI Status: http://localhost:${PORT}/ai/status`);
    console.log('========================================\n');
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully...');
    if (pythonProcess) {
        pythonProcess.kill();
    }
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('SIGINT received, shutting down gracefully...');
    if (pythonProcess) {
        pythonProcess.kill();
    }
    process.exit(0);
});