"""Mock MCP server for E2E workflow tests"""

class MockMCPServer:
    """Mock MCP server that simulates real server behavior"""
    
    def __init__(self):
        self.running = False
        self.clients = []
        self.request_count = 0
        self.server_url = "http://localhost:3000"
    
    async def start(self, timeout: int = 60):
        """Start mock server"""
        self.running = True
        return True
    
    async def stop(self):
        """Stop mock server"""
        self.running = False
        self.clients.clear()
    
    async def _is_server_running(self):
        """Check if server is running"""
        return self.running
    
    def handle_request(self, request: dict) -> dict:
        """Handle mock request"""
        self.request_count += 1
        
        if request.get('type') == 'query_database':
            return self._mock_database_query(request)
        elif request.get('type') == 's3_access':
            return self._mock_s3_access(request)
        elif request.get('type') == 'synthesis':
            return self._mock_synthesis(request)
        
        return {"error": "Unknown request type"}
    
    def _mock_database_query(self, request: dict) -> dict:
        """Mock database query response"""
        return {
            "status": "success",
            "rows": [
                {"player_id": 1, "name": "Test Player", "points": 25}
            ],
            "count": 1
        }
    
    def _mock_s3_access(self, request: dict) -> dict:
        """Mock S3 access response"""
        return {
            "status": "success",
            "objects": ["test_file1.txt", "test_file2.txt"],
            "count": 2
        }
    
    def _mock_synthesis(self, request: dict) -> dict:
        """Mock synthesis response"""
        return {
            "status": "success",
            "result": "Mocked synthesis result",
            "confidence": 0.95
        }

