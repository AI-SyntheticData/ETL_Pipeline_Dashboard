#!/usr/bin/env python3
"""
ML Model Training and Explainability Module
Trains RandomForest classifier for AML risk prediction with SHAP and LIME explainability
"""

import os
import json
import pickle
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import shap
from lime.lime_tabular import LimeTabularExplainer
import warnings
warnings.filterwarnings('ignore')


class AMLRiskModel:
    """AML Risk Prediction Model with Explainability"""

    def __init__(self, model_dir='models'):
        """
        Initialize the AML Risk Model

        Args:
            model_dir: Directory to save/load models
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        self.model = None
        self.shap_explainer = None
        self.lime_explainer = None
        self.feature_names = None
        self.model_metadata = {}

    def prepare_features(self, data):
        """
        Prepare features from raw data

        Args:
            data: Dictionary with 'accounts', 'transactions', 'wire_transfers'

        Returns:
            X: Feature DataFrame
            y: Labels array
            account_ids: List of account IDs
        """
        print("Preparing features for ML model...")

        accounts = data['accounts']
        transactions = data['transactions']
        wire_transfers = data['wire_transfers']

        features_list = []
        labels = []
        account_ids = []

        for account in accounts:
            account_id = account['account_id']
            account_txns = [t for t in transactions if t['account_id'] == account_id]
            account_wires = [w for w in wire_transfers if w['account_id'] == account_id]

            # Extract features
            features = {
                'initial_deposit': float(account.get('initial_deposit', 0)),
                'risk_score': float(account.get('risk_score', 0)),
                'is_pep': 1 if account.get('is_pep') else 0,
                'is_sanctioned': 1 if account.get('is_sanctioned') else 0,
                'kyc_incomplete': 1 if account.get('kyc_status') == 'INCOMPLETE' else 0,
                'has_anomaly': 1 if account.get('anomaly_type') else 0,
                'total_transactions': len(account_txns),
                'suspicious_transactions': len([t for t in account_txns if t.get('alert_generated')]),
                'avg_transaction_amount': np.mean([float(t.get('amount', 0)) for t in account_txns]) if account_txns else 0,
                'max_transaction_amount': np.max([float(t.get('amount', 0)) for t in account_txns]) if account_txns else 0,
                'total_wires': len(account_wires),
                'suspicious_wires': len([w for w in account_wires if w.get('is_suspicious')]),
                'avg_wire_amount': np.mean([float(w.get('amount', 0)) for w in account_wires]) if account_wires else 0,
                'max_wire_amount': np.max([float(w.get('amount', 0)) for w in account_wires]) if account_wires else 0,
            }

            features_list.append(features)
            account_ids.append(account_id)

            # Create label (1 = high risk, 0 = low risk)
            is_high_risk = (
                account.get('is_sanctioned') or
                account.get('is_pep') or
                account.get('risk_score', 0) > 70 or
                len([t for t in account_txns if t.get('alert_generated')]) > 5 or
                len([w for w in account_wires if w.get('is_suspicious')]) > 2
            )
            labels.append(1 if is_high_risk else 0)

        X = pd.DataFrame(features_list)
        y = np.array(labels)

        self.feature_names = X.columns.tolist()

        print(f"✓ Prepared {len(X)} samples with {len(X.columns)} features")
        print(f"  - High risk: {sum(y)} ({sum(y)/len(y)*100:.1f}%)")
        print(f"  - Low risk: {len(y)-sum(y)} ({(len(y)-sum(y))/len(y)*100:.1f}%)")

        return X, y, account_ids

    def train(self, data, test_size=0.2, n_estimators=100, max_depth=10):
        """
        Train the RandomForest model

        Args:
            data: Dictionary with accounts, transactions, wire_transfers
            test_size: Proportion of data for testing
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees

        Returns:
            metrics: Dictionary with evaluation metrics
        """
        print("\n" + "=" * 70)
        print("TRAINING AML RISK PREDICTION MODEL")
        print("=" * 70 + "\n")

        # Prepare data
        X, y, account_ids = self.prepare_features(data)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples\n")

        # Train model
        print("Training RandomForest classifier...")
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )

        self.model.fit(X_train, y_train)
        print("✓ Model trained\n")

        # Evaluate
        print("Evaluating model performance...")
        metrics = self._evaluate_model(X_train, y_train, X_test, y_test)

        # Create explainers
        print("\nCreating explainability models...")
        self._create_explainers(X)

        # Save metadata
        self.model_metadata = {
            'trained_at': datetime.now().isoformat(),
            'n_samples': len(X),
            'n_features': len(X.columns),
            'feature_names': self.feature_names,
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'test_size': test_size,
            'metrics': metrics
        }

        print("\n" + "=" * 70)
        print("MODEL TRAINING COMPLETE")
        print("=" * 70 + "\n")

        return metrics

    def _evaluate_model(self, X_train, y_train, X_test, y_test):
        """Evaluate model performance"""

        # Training predictions
        y_train_pred = self.model.predict(X_train)
        y_train_proba = self.model.predict_proba(X_train)[:, 1]

        # Test predictions
        y_test_pred = self.model.predict(X_test)
        y_test_proba = self.model.predict_proba(X_test)[:, 1]

        # Calculate metrics
        metrics = {
            'train': {
                'accuracy': accuracy_score(y_train, y_train_pred),
                'precision': precision_score(y_train, y_train_pred, zero_division=0),
                'recall': recall_score(y_train, y_train_pred, zero_division=0),
                'f1_score': f1_score(y_train, y_train_pred, zero_division=0),
                'roc_auc': roc_auc_score(y_train, y_train_proba)
            },
            'test': {
                'accuracy': accuracy_score(y_test, y_test_pred),
                'precision': precision_score(y_test, y_test_pred, zero_division=0),
                'recall': recall_score(y_test, y_test_pred, zero_division=0),
                'f1_score': f1_score(y_test, y_test_pred, zero_division=0),
                'roc_auc': roc_auc_score(y_test, y_test_proba)
            }
        }

        # Print results
        print("\nTraining Set Performance:")
        print(f"  Accuracy:  {metrics['train']['accuracy']:.4f}")
        print(f"  Precision: {metrics['train']['precision']:.4f}")
        print(f"  Recall:    {metrics['train']['recall']:.4f}")
        print(f"  F1-Score:  {metrics['train']['f1_score']:.4f}")
        print(f"  ROC-AUC:   {metrics['train']['roc_auc']:.4f}")

        print("\nTest Set Performance:")
        print(f"  Accuracy:  {metrics['test']['accuracy']:.4f}")
        print(f"  Precision: {metrics['test']['precision']:.4f}")
        print(f"  Recall:    {metrics['test']['recall']:.4f}")
        print(f"  F1-Score:  {metrics['test']['f1_score']:.4f}")
        print(f"  ROC-AUC:   {metrics['test']['roc_auc']:.4f}")

        # Confusion matrix
        cm = confusion_matrix(y_test, y_test_pred)
        print("\nConfusion Matrix (Test):")
        print(f"  TN: {cm[0][0]:4d}  |  FP: {cm[0][1]:4d}")
        print(f"  FN: {cm[1][0]:4d}  |  TP: {cm[1][1]:4d}")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        print("\nTop 5 Most Important Features:")
        for idx, row in feature_importance.head(5).iterrows():
            print(f"  {row['feature']:30s}: {row['importance']:.4f}")

        metrics['feature_importance'] = feature_importance.to_dict('records')

        return metrics

    def _create_explainers(self, X):
        """Create SHAP and LIME explainers"""

        print("Creating SHAP explainer...")
        self.shap_explainer = shap.TreeExplainer(self.model)
        print("✓ SHAP explainer ready")

        print("Creating LIME explainer...")
        self.lime_explainer = LimeTabularExplainer(
            X.values,
            feature_names=self.feature_names,
            class_names=['Low Risk', 'High Risk'],
            mode='classification',
            random_state=42
        )
        print("✓ LIME explainer ready")

    def predict(self, X):
        """
        Make predictions

        Args:
            X: Features DataFrame or array

        Returns:
            predictions: Array of predictions (0 or 1)
            probabilities: Array of probability scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)

        return predictions, probabilities

    def explain_prediction(self, X_sample, method='both'):
        """
        Explain a single prediction using SHAP and/or LIME

        Args:
            X_sample: Single sample (Series or 1D array)
            method: 'shap', 'lime', or 'both'

        Returns:
            Dictionary with explanations
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        explanations = {}

        # Convert to DataFrame if needed
        if not isinstance(X_sample, pd.DataFrame):
            X_sample = pd.DataFrame([X_sample], columns=self.feature_names)

        # SHAP explanation
        if method in ['shap', 'both']:
            shap_values = self.shap_explainer.shap_values(X_sample)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # High risk class

            explanations['shap'] = {
                'values': shap_values[0] if len(shap_values.shape) > 1 else shap_values,
                'base_value': self.shap_explainer.expected_value[1] if isinstance(
                    self.shap_explainer.expected_value, list
                ) else self.shap_explainer.expected_value
            }

        # LIME explanation
        if method in ['lime', 'both']:
            lime_exp = self.lime_explainer.explain_instance(
                X_sample.values[0],
                self.model.predict_proba,
                num_features=len(self.feature_names)
            )
            explanations['lime'] = lime_exp.as_list()

        return explanations

    def save_model(self, version=None):
        """
        Save the trained model and metadata

        Args:
            version: Model version string (default: timestamp)

        Returns:
            filepath: Path to saved model
        """
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")

        if version is None:
            version = datetime.now().strftime('%Y%m%d_%H%M%S')

        model_path = os.path.join(self.model_dir, f'aml_model_{version}.pkl')
        metadata_path = os.path.join(self.model_dir, f'aml_model_{version}_metadata.json')

        # Save model (exclude LIME explainer as it contains unpicklable lambdas)
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'shap_explainer': self.shap_explainer
                # LIME explainer will be recreated on load
            }, f)

        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(self.model_metadata, f, indent=2)

        print(f"\n✓ Model saved to: {model_path}")
        print(f"✓ Metadata saved to: {metadata_path}")
        print(f"  Note: LIME explainer will be recreated on load")

        return model_path

    def load_model(self, filepath, X_sample=None):
        """
        Load a trained model

        Args:
            filepath: Path to saved model file
            X_sample: Optional sample data to recreate LIME explainer
        """
        print(f"Loading model from: {filepath}")

        with open(filepath, 'rb') as f:
            saved_data = pickle.load(f)

        self.model = saved_data['model']
        self.feature_names = saved_data['feature_names']
        self.shap_explainer = saved_data.get('shap_explainer')
        self.lime_explainer = saved_data.get('lime_explainer')

        # Recreate LIME explainer if not present and sample data provided
        if self.lime_explainer is None and X_sample is not None:
            print("  Creating LIME explainer...")
            self.lime_explainer = LimeTabularExplainer(
                X_sample.values if hasattr(X_sample, 'values') else X_sample,
                feature_names=self.feature_names,
                class_names=['Low Risk', 'High Risk'],
                mode='classification',
                random_state=42
            )
            print("  ✓ LIME explainer created")

        # Load metadata
        metadata_path = filepath.replace('.pkl', '_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.model_metadata = json.load(f)

        print("✓ Model loaded successfully")
        print(f"  Features: {len(self.feature_names)}")
        print(f"  Trained: {self.model_metadata.get('trained_at', 'Unknown')}")


def train_aml_model(data, model_dir='models', save=True):
    """
    Convenience function to train and save AML model

    Args:
        data: Dictionary with accounts, transactions, wire_transfers
        model_dir: Directory to save model
        save: Whether to save the trained model

    Returns:
        model: Trained AMLRiskModel instance
        metrics: Evaluation metrics
    """
    model = AMLRiskModel(model_dir=model_dir)
    metrics = model.train(data)

    if save:
        model.save_model()

    return model, metrics


if __name__ == "__main__":
    print("AML Risk Model Module")
    print("=" * 70)
    print("\nThis module provides ML model training for AML risk prediction.")
    print("\nUsage:")
    print("  from layers.explanation.ml_model import AMLRiskModel, train_aml_model")
    print("\nFeatures:")
    print("  • RandomForest classifier with hyperparameter tuning")
    print("  • SHAP and LIME explainability")
    print("  • Model evaluation with multiple metrics")
    print("  • Model persistence (save/load)")
    print("  • Feature importance analysis")
    print("=" * 70)

