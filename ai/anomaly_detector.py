import numpy as np
import pandas as pd
import json
import hashlib
import pickle
from typing import List, Dict, Tuple
from dataclasses import dataclass
import warnings
import sys
import os
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
            from sklearn.ensemble import IsolationForest, RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.cluster import DBSCAN
            
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
        except ImportError as e:
            print(f"Error importing ML libraries: {e}")
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
            
            print(f" Model loaded successfully from {model_path}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def train(self, transactions: List[Transaction], labels: List[int] = None):
        """Train model dengan data transaksi"""
        print("Training HORUS AI model...")
        
        try:
            # Extract features
            X = np.vstack([self.extract_features(tx) for tx in transactions])
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            if labels is not None:
                # Supervised learning dengan Random Forest
                y = np.array(labels)
                print(f"Training Random Forest with {len(y)} samples, {sum(y)} anomalies")
                self.random_forest.fit(X_scaled, y)
                print("Supervised training completed")
            else:
                # Unsupervised learning saja
                print("No labels provided, using unsupervised learning only")
            
            # Always train unsupervised models
            self.isolation_forest.fit(X_scaled)
            print(" Unsupervised training completed")
            
            # Clustering untuk pattern discovery
            self.clustering.fit(X_scaled)
            print(" Clustering completed")
            
            self._calculate_feature_importance(X_scaled)
            self.is_trained = True
            
            print(f" All models trained successfully!")
            
        except Exception as e:
            print(f" Training failed: {e}")
            raise
    
    def _calculate_feature_importance(self, X):
        """Calculate feature importance untuk interpretability"""
        try:
            if hasattr(self.random_forest, 'feature_importances_'):
                self.feature_importance = self.random_forest.feature_importances_
                print(f"Feature importance calculated: {len(self.feature_importance)} features")
            else:
                # Fallback importance calculation
                from sklearn.ensemble import IsolationForest
                temp_forest = IsolationForest(random_state=42)
                temp_forest.fit(X)
                self.feature_importance = np.ones(X.shape[1]) / X.shape[1]
                print("Using uniform feature importance")
        except Exception as e:
            print(f"Feature importance calculation failed: {e}")
            self.feature_importance = np.ones(X.shape[1]) / X.shape[1]
    
    def extract_features(self, transaction: Transaction) -> np.ndarray:
        """Extract comprehensive features dari transaksi"""
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
    
    def detect_anomaly(self, transaction: Transaction) -> Tuple[float, Dict]:
        """Deteksi anomaly dan return score dengan explanation"""
        if not self.is_trained:
            return 0.0, {
                'risk_level': 'LOW',
                'confidence': 0.0,
                'triggering_factors': ['Model not trained'],
                'recommendation': 'System initialization required'
            }
        
        try:
            features = self.extract_features(transaction)
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
                transaction, final_score, features[0], dict(scores)
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
    
    def _generate_explanation(self, transaction: Transaction, 
                            score: float, features: np.ndarray, component_scores: Dict) -> Dict:
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
        if transaction.amount > 1000000:
            explanation['triggering_factors'].append('Unusually high amount')
        
        if features[1] > 2:  # Log amount unusual
            explanation['triggering_factors'].append('Amount distribution anomaly')
        
        # Time-based anomaly
        hour = (transaction.timestamp % 86400) // 3600
        if hour < 6 or hour > 22:
            explanation['triggering_factors'].append('Unusual transaction time')
        
        # Department-based anomaly
        if transaction.department.lower() == 'unknown':
            explanation['triggering_factors'].append('Unknown department')
        
        # Sender-receiver similarity
        if transaction.sender == transaction.receiver:
            explanation['triggering_factors'].append('Self-transfer detected')
        
        return explanation

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

# Global AI instance
ai_engine = HorusAI()

def main():
    """Main function untuk AI engine"""
    print("HORUS AI Engine Starting...")
    
    # Initialize model
    if not ai_engine.initialize_model():
        print("Failed to initialize AI model")
        return
    
    # Try to load pre-trained model
    model_loaded = ai_engine.load_model('models/horus_ai_model_v1.pkl')
    
    if not model_loaded:
        print("No pre-trained model found. System will use basic initialization.")
    else:
        print("Pre-trained model loaded successfully!")
    
    print("HORUS AI Engine Ready - Listening for transactions...")
    
    # Process input dari stdin
    for line in sys.stdin:
        try:
            if line.strip():
                data = json.loads(line.strip())
                
                if data.get('type') == 'detect_anomaly':
                    tx_data = data['data']
                    
                    # Convert to Transaction object
                    transaction = Transaction(
                        id=tx_data.get('id', 0),
                        amount=float(tx_data.get('amount', 0)),
                        sender=tx_data.get('sender', ''),
                        receiver=tx_data.get('receiver', ''),
                        timestamp=tx_data.get('timestamp', 0),
                        department=tx_data.get('department', ''),
                        transaction_type=tx_data.get('transaction_type', ''),
                        metadata=tx_data.get('metadata', {})
                    )
                    
                    # Detect anomaly
                    score, explanation = ai_engine.detect_anomaly(transaction)
                    
                    # Send result
                    result = {
                        'type': 'anomaly_result',
                        'data': {
                            'score': float(score),
                            'risk_level': explanation['risk_level'],
                            'explanation': explanation,
                            'transaction_id': transaction.id
                        }
                    }
                    
                    print(json.dumps(result))
                    
                elif data.get('type') == 'health_check':
                    print(json.dumps({
                        'type': 'health_status',
                        'data': {
                            'status': 'healthy',
                            'model_loaded': ai_engine.is_trained,
                            'version': ai_engine.model_version,
                            'components_working': True
                        }
                    }))
                    
        except json.JSONDecodeError as e:
            print(json.dumps({
                'type': 'error',
                'data': {'message': f'Invalid JSON input: {e}'}
            }))
        except Exception as e:
            print(json.dumps({
                'type': 'error', 
                'data': {'message': str(e)}
            }))

if __name__ == "__main__":
    main()