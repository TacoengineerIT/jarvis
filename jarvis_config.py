from pathlib import Path
import json

class JarvisConfig:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        self.config = {}
    def get(self, key, default=None):
        return default

config = JarvisConfig()
