"""
Firebase state management for real-time trading data and system state.
Handles Firestore for structured data and Realtime Database for streaming updates.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from google.cloud import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    import firebase_admin
    from firebase_admin import db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase libraries not available - using mock mode")

from config import config

class FirebaseManager:
    """Manages all Firebase interactions for the trading system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.firestore_client = None
        self.realtime_db = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        if FIREBASE_AVAILABLE and config.firebase_app:
            self._initialize_clients()
        else:
            self.logger.warning("Running in mock mode - no actual Firebase connection")
    
    def _initialize_clients(self) -> None:
        """Initialize Firebase clients"""
        try:
            self.firestore_client = firestore.Client()
            self.realtime_db = db.reference()
            self.logger.info("Firebase clients initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Firebase clients: {e}")
    
    # ========== FIRESTORE OPERATIONS ==========
    
    def save_trading_signal(self, signal_data: Dict[str, Any]) -> str:
        """Save a trading signal to Firestore"""
        try:
            if