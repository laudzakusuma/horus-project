#!/usr/bin/env python3
"""
HORUS AI Engine - Anomaly Detection System
Fixed version without Unicode emojis for Windows compatibility
"""

import sys
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import hashlib
import os
import time
import traceback
from typing import List, Dict, Tuple
from dataclasses import dataclass
import warnings

warnings.filterwarnings('ignore')

@dataclass
class Transaction:
    id: int
    amount: float
    sender: str
    receiver: str
    timestamp: int
    department: str
    transaction_type: str
    metadata: Dict

class HorusAI:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.model_version = "1.0.0"
        self.risk_thresholds = {
            'high': 0.6, 
            'medium': 0.4,  
            'low': 0.2
        }
        self.is_trained = False
        
    def initialize_model(self):
        """Initialize AI model dengan ensemble methods"""
        try:
            # Ensemble model untuk robustness
            self.isolation_forest = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            self.random_forest = RandomForestClassifier(
                n_estimators=50,
                random_state=42,
                class_weight='balanced'  # Handle imbalanced data
            )
            
            self.clustering = DBSCAN(eps=0.5, min_samples=10)
            self.scaler = StandardScaler()
            
            print("HORUS AI Model initialized successfully")
            return True
        except Exception as e:
            print(f"Error initializing ML models: {e}")
            return False
    
    def load_model(self, model_path: str):
        """Load trained model dari file"""
        try:
            if not os.path.exists(model_path):
                print(f"Model file not found: {model_path}")
                return False
                
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.isolation_forest = model_data['isolation_forest']
            self.random_forest = model_data['random_forest']
            self.scaler = model_data['scaler']
            self.clustering = model_data['clustering']
            self.feature_importance = model_data.get('feature_importance', [])
            self.is_trained = True
            
            print(f"Model loaded successfully from {model_path}")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def extract_features(self, transaction_data: Dict) -> np.ndarray:
        """Extract comprehensive features dari transaksi data"""
        try:
            # Create Transaction object from dictionary
            transaction = Transaction(
                id=transaction_data.get('id', 0),
                amount=transaction_data.get('amount', 0.0),
                sender=transaction_data.get('sender', 'unknown'),
                receiver=transaction_data.get('receiver', 'unknown'),
                timestamp=transaction_data.get('timestamp', int(time.time())),
                department=transaction_data.get('department', 'unknown'),
                transaction_type=transaction_data.get('transaction_type', 'unknown'),
                metadata=transaction_data.get('metadata', {})
            )
            
            features = []
            
            # 1. Amount-based features
            features.extend([
                transaction.amount,
                np.log1p(transaction.amount) if transaction.amount > 0 else 0,
                transaction.amount ** 0.5
            ])
            
            # 2. Temporal features
            features.extend([
                transaction.timestamp % 86400,  # Second dalam hari
                (transaction.timestamp % 86400) // 3600,  # Jam dalam hari
                transaction.timestamp // 86400  # Hari sejak epoch
            ])
            
            # 3. Behavioral features (hash-based)
            sender_hash = int(hashlib.md5(transaction.sender.encode()).hexdigest()[:8], 16)
            receiver_hash = int(hashlib.md5(transaction.receiver.encode()).hexdigest()[:8], 16)
            
            features.extend([
                sender_hash % 10000,
                receiver_hash % 10000,
                abs(sender_hash - receiver_hash) % 10000
            ])
            
            # 4. Department encoding
            dept_mapping = {
                'keuangan': 1, 'pajak': 2, 'pengadaan': 3, 
                'proyek': 4, 'umum': 5, 'lainnya': 0
            }
            dept_code = dept_mapping.get(transaction.department.lower(), 0)
            features.append(dept_code)
            
            # 5. Transaction type encoding
            type_mapping = {
                'transfer': 1, 'pembayaran': 2, 'pengeluaran': 3,
                'penerimaan': 4, 'penyesuaian': 5, 'lainnya': 0
            }
            type_code = type_mapping.get(transaction.transaction_type.lower(), 0)
            features.append(type_code)
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            # Return default features as fallback
            return np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]).reshape(1, -1)
    
    def detect_anomaly(self, transaction_data: Dict) -> Tuple[float, Dict]:
        """Deteksi anomaly dan return score dengan explanation"""
        if not self.is_trained:
            return 0.0, {
                'risk_level': 'LOW',
                'confidence': 0.0,
                'triggering_factors': ['Model not trained'],
                'recommendation': 'System initialization required'
            }
        
        try:
            features = self.extract_features(transaction_data)
            features_scaled = self.scaler.transform(features)
            
            # Ensemble scoring dengan fallback
            scores = []
            
            # 1. Isolation Forest score
            try:
                if_score = self.isolation_forest.decision_function(features_scaled)[0]
                if_score_normalized = 1 - (if_score + 0.5)  # Convert to 0-1 scale
                scores.append(('isolation_forest', if_score_normalized))
            except Exception as e:
                print(f"Isolation Forest error: {e}")
                scores.append(('isolation_forest', 0.5))
            
            # 2. Random Forest score (jika trained)
            rf_score = 0.5
            try:
                if hasattr(self.random_forest, 'predict_proba'):
                    rf_proba = self.random_forest.predict_proba(features_scaled)
                    rf_score = rf_proba[0][1] if rf_proba.shape[1] > 1 else 0.5
                    scores.append(('random_forest', rf_score))
                else:
                    scores.append(('random_forest', 0.5))
            except Exception as e:
                print(f"Random Forest error: {e}")
                scores.append(('random_forest', 0.5))
            
            # 3. Clustering anomaly
            try:
                cluster_label = self.clustering.fit_predict(features_scaled)[0]
                cluster_score = 1.0 if cluster_label == -1 else 0.0
                scores.append(('clustering', cluster_score))
            except Exception as e:
                print(f"Clustering error: {e}")
                scores.append(('clustering', 0.0))
            
            # Calculate weighted final score
            weights = {'isolation_forest': 0.5, 'random_forest': 0.3, 'clustering': 0.2}
            final_score = sum(weight * score for (name, score), weight in zip(scores, weights.values()))
            
            # Generate explanation
            explanation = self._generate_explanation(
                transaction_data, final_score, features[0], dict(scores)
            )
            
            return final_score, explanation
            
        except Exception as e:
            print(f"Error in anomaly detection: {e}")
            return 0.0, {
                'risk_level': 'LOW',
                'confidence': 0.0,
                'triggering_factors': ['Analysis error'],
                'recommendation': 'Manual review required'
            }
    
    def _generate_explanation(self, transaction_data: Dict, score: float, 
                            features: np.ndarray, component_scores: Dict) -> Dict:
        """Generate human-readable explanation untuk hasil deteksi"""
        explanation = {
            'risk_level': 'LOW',
            'confidence': float(score),
            'triggering_factors': [],
            'recommendation': 'No action needed',
            'component_scores': component_scores,
            'features_used': len(features)
        }
        
        if score >= self.risk_thresholds['high']:
            explanation['risk_level'] = 'HIGH'
            explanation['recommendation'] = 'Immediate investigation required'
        elif score >= self.risk_thresholds['medium']:
            explanation['risk_level'] = 'MEDIUM'
            explanation['recommendation'] = 'Review recommended'
        else:
            explanation['risk_level'] = 'LOW'
        
        # Detailing triggering factors berdasarkan features
        amount = transaction_data.get('amount', 0)
        if amount > 1000000:
            explanation['triggering_factors'].append('Unusually high amount')
        
        if features[1] > 2:  # Log amount unusual
            explanation['triggering_factors'].append('Amount distribution anomaly')
        
        # Time-based anomaly
        timestamp = transaction_data.get('timestamp', int(time.time()))
        hour = (timestamp % 86400) // 3600
        if hour < 6 or hour > 22:
            explanation['triggering_factors'].append('Unusual transaction time')
        
        # Department-based anomaly
        department = transaction_data.get('department', 'unknown').lower()
        if department == 'unknown':
            explanation['triggering_factors'].append('Unknown department')
        
        # Sender-receiver similarity
        sender = transaction_data.get('sender', '')
        receiver = transaction_data.get('receiver', '')
        if sender == receiver:
            explanation['triggering_factors'].append('Self-transfer detected')
        
        return explanation

    def retrain_model(self, training_data: Dict) -> bool:
        """Placeholder for model retraining - to be implemented"""
        try:
            print("Model retraining requested")
            # Implement actual retraining logic here
            return True
        except Exception as e:
            print(f"Error in model retraining: {e}")
            return False

    def get_model_hash(self) -> str:
        """Generate hash untuk verifikasi model integrity"""
        try:
            model_bytes = pickle.dumps({
                'isolation_forest': self.isolation_forest,
                'random_forest': self.random_forest,
                'scaler': self.scaler,
                'version': self.model_version
            })
            return hashlib.sha256(model_bytes).hexdigest()
        except Exception as e:
            print(f"Error generating model hash: {e}")
            return "hash_generation_failed"

def main():
    """Main function for the AI Engine"""
    ai_engine = HorusAI()
    
    try:
        # Initialize the AI engine
        print("HORUS AI Engine Starting...")
        
        # First try to load pre-trained model
        model_path = os.getenv('AI_MODEL_PATH', './models/horus_ai_model_v1.pkl')
        model_loaded = ai_engine.load_model(model_path)
        
        if not model_loaded:
            print("No pre-trained model found, initializing new model...")
            if ai_engine.initialize_model():
                print("New model initialized successfully")
                ai_engine.is_trained = True
            else:
                print("Failed to initialize AI Engine. Exiting.")
                sys.exit(1)
        else:
            print("Pre-trained model loaded successfully!")
        
        print("HORUS AI Engine Ready - Listening for transactions...")
        print("Send JSON data via stdin for analysis")
        print("Example: {\"type\": \"transaction\", \"data\": {\"amount\": 100, \"sender\": \"A\", \"receiver\": \"B\"}}")
        print("-" * 50)
        
        # Send ready status to Node.js
        ready_message = json.dumps({
            "status": "ready", 
            "message": "AI Engine initialized and ready",
            "timestamp": time.time(),
            "model_loaded": ai_engine.is_trained
        })
        print(ready_message)
        sys.stdout.flush()
        
        # Main loop - listen for input
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Parse JSON input
                data = json.loads(line)
                
                # Process based on message type
                message_type = data.get('type', 'unknown')
                
                if message_type == 'init':
                    # Respond to initialization request
                    response = {
                        "status": "initialized",
                        "message": "AI Engine is ready",
                        "timestamp": time.time(),
                        "model_loaded": ai_engine.is_trained
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                elif message_type == 'transaction':
                    transaction_data = data.get('data', {})
                    anomaly_score, explanation = ai_engine.detect_anomaly(transaction_data)
                    
                    result = {
                        "anomaly_score": float(anomaly_score),
                        "explanation": explanation,
                        "transaction_id": transaction_data.get('id', 'unknown'),
                        "timestamp": time.time()
                    }
                    
                    # Print result as JSON for Node.js to read
                    print(json.dumps(result))
                    sys.stdout.flush()
                    
                elif message_type == 'retrain':
                    success = ai_engine.retrain_model(data.get('data', {}))
                    response = {
                        "retrain_success": success,
                        "timestamp": time.time()
                    }
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                elif message_type == 'health':
                    # Health check request
                    health_status = {
                        "status": "healthy",
                        "model_loaded": ai_engine.is_trained,
                        "timestamp": time.time(),
                        "model_hash": ai_engine.get_model_hash()
                    }
                    print(json.dumps(health_status))
                    sys.stdout.flush()
                    
                else:
                    error_response = {
                        "error": "Unknown message type",
                        "received_type": message_type,
                        "timestamp": time.time()
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
            except json.JSONDecodeError as e:
                error_response = {
                    "error": "Invalid JSON format",
                    "message": str(e),
                    "input": line,
                    "timestamp": time.time()
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    "error": f"Processing error: {str(e)}",
                    "timestamp": time.time()
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        print("AI Engine stopped by user")
        # Send shutdown message
        shutdown_msg = json.dumps({
            "status": "shutdown",
            "message": "AI Engine stopped by user",
            "timestamp": time.time()
        })
        print(shutdown_msg)
        sys.stdout.flush()
    except Exception as e:
        error_msg = json.dumps({
            "error": f"Fatal error in AI Engine: {str(e)}",
            "timestamp": time.time()
        })
        print(error_msg)
        sys.stdout.flush()
        # Use traceback.print_exc() instead of format_exc() to avoid encoding issues
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()