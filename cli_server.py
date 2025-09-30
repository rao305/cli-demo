#!/usr/bin/env python3
"""
Simple BoilerAI CLI - Message Echo System
=========================================
Just receives messages from frontend and echoes them back.
Only asks for API key to power up.
"""

import json
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

class SimpleBoilerAI:
    """Simple CLI that just echoes messages"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider = "gemini"
        print(f"✅ SimpleBoilerAI initialized with {self.provider} API key")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Just echo back the query"""
        return {
            "success": True,
            "response": query,  # Just echo back
            "provider": self.provider,
            "api_key_set": bool(self.api_key)
        }

class BoilerAICLIServer:
    """CLI Server that connects to SimpleBoilerAI"""
    
    def __init__(self):
        self.api_key = None
        self.provider = "gemini"
        self.cli_agent = None
        self.initialized = False
        
    def setup_api_key(self):
        """Setup API key. Supports non-interactive mode via GEMINI_API_KEY env variable."""
        print("=" * 50)
        print("BoilerAI CLI Server - Simple Echo Mode")
        print("=" * 50)
        
        print("Using provider: Gemini (Google)")
        print("\nAPI Key Required for gemini")
        print("=" * 40)
        print("Get your Gemini API key from: https://makersuite.google.com/app/apikey")
        print("Your key should start with 'AIzaSy'")
        
        # Non-interactive mode: use env var if provided
        env_key = os.getenv("GEMINI_API_KEY", "").strip()
        if env_key:
            self.api_key = env_key
            print("\n[INFO] Using GEMINI_API_KEY from environment.")
        else:
            print("\n[COPY-PASTE FRIENDLY] You can copy and paste your API key here:")
            while True:
                self.api_key = input(f"Enter your {self.provider} API key: ").strip()
                if not self.api_key:
                    print("No API key provided. Please try again.")
                    continue
                # Basic validation
                if self.provider == "gemini" and not self.api_key.startswith('AIzaSy'):
                    print("WARNING: Gemini API key usually starts with 'AIzaSy'")
                    confirm = input("Are you sure this is correct? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue
                break
        
        print(f"\nAPI key received: {self.api_key[:10]}...")
        print(f"[OK] {self.provider} API key set for this session")
        
        # Initialize the simple CLI
        self.cli_agent = SimpleBoilerAI(self.api_key)
        self.initialized = True
        return True
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process query using the simple CLI"""
        if self.cli_agent:
            return self.cli_agent.process_query(query)
        else:
            return {
                "success": False,
                "error": "CLI not initialized"
            }

# Global server instance
cli_server = BoilerAICLIServer()

class RequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "status": "ok",
                "initialized": cli_server.initialized,
                "provider": cli_server.provider,
                "mode": "echo"
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests - main query endpoint"""
        if self.path != '/query':
            self.send_response(404)
            self.end_headers()
            return
        
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())
            
            query = data.get('query', '')
            
            # Log incoming query
            print(f"[RECV] Query received: {query[:100]}... ({len(query)} chars)")

            # Process query
            start_time = time.time()
            result = cli_server.process_query(query)
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Log response
            response_text = result.get('response', '')
            print(f"[SENT] Response in {elapsed_ms}ms | {len(response_text)} chars")
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())

def main():
    """Start the server"""
    print("\nStarting BoilerAI CLI Server...")
    print("=" * 40)
    
    # Setup API key
    if not cli_server.setup_api_key():
        print("[ERROR] Failed to setup API key")
        return
    
    # Start server
    print("\n" + "=" * 50)
    print("BoilerAI CLI Server Started - Simple Echo Mode")
    print("=" * 50)
    print("Server running on: http://localhost:8000")
    print(f"Provider: {cli_server.provider}")
    print(f"API Key: {cli_server.api_key[:10]}...")
    print("Ready to echo messages from frontend!")
    print("Press Ctrl+C to stop the server")
    print("=" * 50 + "\n")

    server = HTTPServer(('localhost', 8000), RequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[STOP] Server stopped by user")
        server.shutdown()

if __name__ == "__main__":
    main()