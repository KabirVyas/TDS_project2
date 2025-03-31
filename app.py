import os
import json
import sqlite3
import subprocess
import numpy as np
import pandas as pd
import requests
from flask import Flask, request, jsonify, Response
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util
from PIL import Image
from dateutil import parser
import calendar
import re
from datetime import datetime
from openpyxl import Workbook
from markdown2 import markdown
import shutil
from dateutil import parser
from fastapi.responses import PlainTextResponse
from pathlib import Path
import csv
import glob
import time
import stat
import duckdb
from bs4 import BeautifulSoup
import whisper

# Load environment variables from .env file
load_dotenv()

# Retrieve AI Proxy Token from environment variables
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
API_BASE_URL = "https://aiproxy.sanand.workers.dev/openai/v1"

# Ensure the API key is set
if not AIPROXY_TOKEN:
    raise ValueError("Error: AIPROXY_TOKEN is not set. Make sure you have added it to your .env file.")

# Initialize Flask app
app = Flask(__name__)


# Ensure all files are accessed from the 'data' folder inside the project root
PROJECT_ROOT = os.path.abspath(os.getcwd())
DATA_DIR = os.path.join(PROJECT_ROOT, "data")  # ✅ Allowed data directory

# Task mapping for LLM classification
TASK_MAPPING = {
    "install_and_execute": "run_datagen",
    "format_markdown": "format_markdown",
    "count_weekday": "count_weekday",
    "sort_contacts": "sort_contacts",
    "extract_content": "extract_content",
    "extract_headers": "extract_headers",
    "extract_email": "extract_email",
    "extract_credit_card": "extract_credit_card",
    "find_similar_comments": "find_similar_comments",
    "execute_dynamic_query": "execute_dynamic_query"
}

def classify_task(task_description):
    """Use AI Proxy to classify the task correctly."""
    try:
        headers = {
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Classify the task description into EXACTLY one of these labels:\n"
                        + ", ".join(TASK_MAPPING.keys())
                        + ".\n\n"
                        "Return ONLY the exact label, nothing else."
                    )
                },
                {"role": "user", "content": task_description}
            ]
        }

        response = requests.post(
            "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            print(f"ERROR: AI Proxy API failed - {response.text}", flush=True)
            return None

        classification = response.json()["choices"][0]["message"]["content"].strip().lower()

        print(f"DEBUG: AI Proxy classified '{task_description}' as '{classification}'", flush=True)

        return classification if classification in TASK_MAPPING else None

    except Exception as e:
        print(f"ERROR: AI Proxy request failed - {e}", flush=True)
        return None

@app.route("/run", methods=["GET", "POST"])
def run_task():
    """Runs a task based on classification."""
    task_description = request.args.get("task")

    if not task_description:
        return jsonify({"error": "Missing task parameter"}), 400

    task_label = classify_task(task_description)

    if not task_label:
        return jsonify({"error": "Task classification failed"}), 500

    if task_label == "vs_code":
        return jsonify(vs_code(task_description)) 
    
    if task_label == "send_https_request":
        return jsonify(send_https_request(task_description)) 

    return jsonify({"error": f"Task '{task_label}' is not yet implemented"}), 400

@app.route("/read", methods=["GET", "POST"])
def read_file():
    """Reads a file from the project directory and returns its contents as plain text."""
    relative_path = request.args.get("path")

    if not relative_path:
        return Response("Missing path parameter", status=400, mimetype="text/plain")

    # ✅ Remove leading slash to prevent absolute path issues
    relative_path = relative_path.lstrip("/")

    # ✅ Construct full file path
    file_path = os.path.join(PROJECT_ROOT, relative_path)

    if not os.path.isfile(file_path):
        return Response("File not found", status=404, mimetype="text/plain")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content, status=200, mimetype="text/plain")  # ✅ Always plain text output
    except Exception as e:
        return Response(f"Failed to read file: {str(e)}", status=500, mimetype="text/plain")
    
def vs_code(task_description):
    """Runs 'code -s' in the terminal and returns the output in JSON format."""
    try:
        # ✅ Step 1: Execute the command
        try:
            command_output = subprocess.check_output("code -s", shell=True, text=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            command_output = f"Error executing command: {e.output}"

        # ✅ Step 2: Return the output in JSON format
        return jsonify({"answer": command_output}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500
    
def send_https_request(task_description):
    """Sends a HTTPS request using HTTPie and returns the JSON response."""
    try:
        url = "https://httpbin.org/get"
        params = {"email": "22f2001048@ds.study.iitm.ac.in"}

        # ✅ Step 1: Send the HTTPS request
        try:
            response = requests.get(url, params=params)
            json_output = response.json()  # Extract JSON body
        except requests.RequestException as e:
            return jsonify({"answer": f"Request failed: {str(e)}"}), 500

        # ✅ Step 2: Return JSON response in the required format
        return jsonify({"answer": json_output}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500


