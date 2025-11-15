import json
import pickle
from anomaly_detector import HorusAI, Transaction
import hashlib
from datetime import datetime
import numpy as np

def generate_sample_data():
    """Generate sample training data dengan labels untuk supervised learning"""
    transactions = []
    labels = []
    
    # Normal transactions (95%)
    for i in range(1000):
        transactions.append(Transaction(
            id=i,
            amount=1000 + (i * 100),
            sender=f"department_{i % 5}",
            receiver=f"vendor_{(i * 7) % 20}",
            timestamp=1609459200 + (i * 3600),
            department=["keuangan", "pajak", "pengadaan", "proyek", "umum"][i % 5],
            transaction_type="transfer",
            metadata={"description": f"Regular payment {i}"}
        ))
        labels.append(0)  # 0 = normal
    
    # Anomalous transactions (5%)
    for i in range(50):
        transactions.append(Transaction(
            id=1000 + i,
            amount=5000000 + (i * 100000),  # Very large amounts
            sender=f"department_suspicious_{i}",
            receiver=f"vendor_suspicious_{i}",
            timestamp=1609459200 + (i * 3600),
            department="unknown",
            transaction_type="adjustment",
            metadata={"description": "Suspicious transaction"}
        ))
        labels.append(1)  # 1 = anomalous
    
    return transactions, labels

def generate_training_labels(transactions):
    """Generate labels based on heuristic rules untuk semi-supervised learning"""
    labels = []
    amounts = [tx.amount for tx in transactions]
    amount_threshold = np.percentile(amounts, 95)  # Top 5% dianggap anomalous
    
    for tx in transactions:
        # Heuristic rules untuk label anomalies
        is_anomalous = (
            tx.amount > amount_threshold or
            tx.department.lower() == 'unknown' or
            tx.sender == tx.receiver or  # Self-transfer
            'suspicious' in tx.sender.lower() or
            'suspicious' in tx.receiver.lower()
        )
        labels.append(1 if is_anomalous else 0)
    
    return labels

def main():
    print("Initializing HORUS AI Training...")
    
    try:
        # Initialize AI
        ai = HorusAI()
        ai.initialize_model()
        
        # Generate training data
        print("Generating training data...")
        training_data, true_labels = generate_sample_data()
        
        # Atau gunakan heuristic labels jika tidak ada true labels
        # training_labels = generate_training_labels(training_data)
        
        print(f"Training on {len(training_data)} transactions...")
        print(f"Normal transactions: {true_labels.count(0)}")
        print(f"Anomalous transactions: {true_labels.count(1)}")
        
        # Train dengan labels untuk supervised learning
        ai.train(training_data, true_labels)
        
        # Save model
        model_data = {
            'isolation_forest': ai.isolation_forest,
            'random_forest': ai.random_forest,
            'scaler': ai.scaler,
            'clustering': ai.clustering,
            'feature_importance': ai.feature_importance,
            'version': ai.model_version,
            'trained_at': datetime.now().isoformat(),
            'training_samples': len(training_data)
        }
        
        # Ensure models directory exists
        import os
        os.makedirs('models', exist_ok=True)
        
        with open('models/horus_ai_model_v1.pkl', 'wb') as f:
            pickle.dump(model_data, f)
        
        # Generate model hash
        model_hash = ai.get_model_hash()
        
        print(f" Training completed!")
        print(f" Model saved: models/horus_ai_model_v1.pkl")
        print(f" Model Hash: {model_hash}")
        print(f" Training stats:")
        print(f"   - Samples: {len(training_data)}")
        print(f"   - Features: {len(ai.feature_names) if hasattr(ai, 'feature_names') else 'N/A'}")
        print(f"   - Anomaly ratio: {true_labels.count(1) / len(true_labels):.2%}")
        
        # Save hash to file
        with open('models/model_hash.txt', 'w') as f:
            f.write(model_hash)
            
        # Test the trained model dengan berbagai scenario
        print("\n Testing trained model...")
        
        test_cases = [
            {
                "name": "Normal Transaction",
                "data": Transaction(
                    id=9999,
                    amount=50000,
                    sender="department_keuangan",
                    receiver="vendor_regular",
                    timestamp=1609459200,
                    department="keuangan",
                    transaction_type="transfer",
                    metadata={"description": "Regular payment"}
                )
            },
            {
                "name": "High Amount Anomaly",
                "data": Transaction(
                    id=10000,
                    amount=10000000,
                    sender="department_proyek",
                    receiver="vendor_luar",
                    timestamp=1609459200,
                    department="proyek",
                    transaction_type="transfer",
                    metadata={"description": "Large project payment"}
                )
            },
            {
                "name": "Suspicious Department",
                "data": Transaction(
                    id=10001,
                    amount=1000000,
                    sender="unknown_dept",
                    receiver="vendor_unknown",
                    timestamp=1609459200,
                    department="unknown",
                    transaction_type="adjustment",
                    metadata={"description": "Suspicious adjustment"}
                )
            }
        ]
        
        for test_case in test_cases:
            score, explanation = ai.detect_anomaly(test_case["data"])
            print(f"\n {test_case['name']}:")
            print(f"   Score: {score:.4f}")
            print(f"   Risk Level: {explanation['risk_level']}")
            print(f"   Factors: {explanation['triggering_factors']}")
            print(f"   Recommendation: {explanation['recommendation']}")
        
        print(f"\n Model testing completed!")
        
    except Exception as e:
        print(f" Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()