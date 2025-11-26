import os
import requests
import json
from fastapi import FastAPI, Request, HTTPException
from config import Settings
from pydantic import BaseModel
from typing import Dict, Any, List
import uuid
import time
import re

settings = Settings()

GOOGLE_API_KEY = settings.GOOGLE_API_KEY
MODEL_NAME = settings.MODEL_NAME
SECRET_KEY = settings.SECRET_KEY

app = FastAPI(title="Depre Buddy Sequential Triage Agent", version="1.0")
