"""
Configuration management for Autonomous Trading Intelligence Network.
Centralizes all configuration, environment variables, and Firebase initialization.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class FirebaseConfig:
    """Firebase configuration settings"""
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")
    service_account_path: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    database_url: str = os.getenv("FIREBASE_DATABASE_URL", "")

@dataclass
class ExchangeConfig:
    """Exchange API configuration"""
    name: str = os.getenv("EXCHANGE_NAME", "binance")
    api_key: str = os.getenv("EXCHANGE_API_KEY", "")
    api_secret: str = os.getenv("EXCHANGE_API_SECRET", "")
    testnet: bool = os.getenv("EXCHANGE_TESTNET", "True").lower() == "true"

@dataclass
class TradingConfig:
    """Trading parameters and limits"""
    max_position_size: float = float(os.getenv("MAX_POSITION_SIZE", "10000"))
    max_risk_per_trade: float = float(os.getenv("MAX_RISK_PER_TRADE", "0.02"))
    max_daily_loss: float = float(os.getenv("MAX_DAILY_LOSS", "0.05"))
    min_confidence_threshold: float = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.7"))
    portfolio_allocation: Dict[str, float] = None
    
    def __post_init__(self):
        if self.portfolio_allocation is None:
            self.portfolio_allocation = {
                "BTC": 0.4,
                "ETH": 0.3,
                "ALTS": 0.2,
                "CASH": 0.1
            }

@dataclass
class MLConfig:
    """Machine Learning configuration"""
    model_path: str = os.getenv("MODEL_PATH", "models/")
    retrain_interval_hours: int = int(os.getenv("RETRAIN_INTERVAL_HOURS", "24"))
    feature_window: int = int(os.getenv("FEATURE_WINDOW", "50"))
    prediction_horizon: int = int(os.getenv("PREDICTION_HORIZON", "10"))

class ConfigManager:
    """Manages application configuration and Firebase initialization"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.firebase_config = FirebaseConfig()
        self.exchange_config = ExchangeConfig()
        self.trading_config = TradingConfig()
        self.ml_config = MLConfig()
        self._validate_config()
        self.firebase_app = self._initialize_firebase()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure structured logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/trading_system.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def _validate_config(self) -> None:
        """Validate all configuration parameters"""
        if not self.firebase_config.project_id:
            raise ValueError("FIREBASE_PROJECT_ID environment variable is required")
        
        if not os.path.exists(self.firebase_config.service_account_path):
            self.logger.warning(f"Firebase service account file not found at {self.firebase_config.service_account_path}")
            
        if not self.exchange_config.api_key or not self.exchange_config.api_secret:
            self.logger.warning("Exchange API credentials not found - execution will be simulated")
    
    def _initialize_firebase(self) -> Optional[Any]:
        """Initialize Firebase Admin SDK"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            if not firebase_admin._apps:
                if os.path.exists(self.firebase_config.service_account_path):
                    cred = credentials.Certificate(self.firebase_config.service_account_path)
                    app = firebase_admin.initialize_app(cred, {
                        'projectId': self.firebase_config.project_id,
                        'databaseURL': self.firebase_config.database_url
                    })
                    self.logger.info("Firebase initialized successfully")
                    return app
                else:
                    self.logger.warning("Firebase service account file not found - using mock mode")
                    return None
            return firebase_admin.get_app()
        except ImportError:
            self.logger.error("firebase-admin not installed. Install with: pip install firebase-admin")
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all config to dictionary"""
        return {
            "firebase": asdict(self.firebase_config),
            "exchange": asdict(self.exchange_config),
            "trading": asdict(self.trading_config),
            "ml": asdict(self.ml_config)
        }

# Global configuration instance
config = ConfigManager()