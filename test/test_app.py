import os
import sys
# pyrefly: ignore [missing-import]
import pytest

# Ensure the root/src directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Test that the index/dashboard renders correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert 'SRE 運維指揮中心'.encode('utf-8') in response.data
    assert b'cpu-radial-bar' in response.data
    assert b'id="menu-docs"' in response.data

def test_api_metrics(client):
    """Test the metrics endpoint yields correct JSON structure."""
    response = client.get('/api/metrics')
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    required_keys = ['cpu', 'memory', 'disk', 'network_in', 'network_out', 'latency', 'uptime', 'timestamp']
    for key in required_keys:
        assert key in data
        
    assert isinstance(data['cpu'], (int, float))
    assert isinstance(data['memory'], (int, float))
    assert isinstance(data['disk'], (int, float))
    assert isinstance(data['uptime'], str)

def test_api_ping(client):
    """Test the ping health checker endpoint."""
    # Test default ping
    response = client.get('/api/ping')
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    assert 'url' in data
    assert 'status' in data
    assert 'status_code' in data
    assert 'latency' in data
    assert 'timestamp' in data
    
    # Test specific URL
    response = client.get('/api/ping?url=localhost')
    data = response.get_json()
    assert 'localhost' in data['url']

def test_api_logs(client):
    """Test the logs API endpoint and its filters."""
    # Test all logs
    response = client.get('/api/logs?level=ALL&limit=10')
    assert response.status_code == 200
    assert response.is_json
    logs = response.get_json()
    assert len(logs) <= 10
    
    if logs:
        assert 'timestamp' in logs[0]
        assert 'level' in logs[0]
        assert 'service' in logs[0]
        assert 'message' in logs[0]
        
    # Test filtered levels
    response_info = client.get('/api/logs?level=INFO&limit=5')
    logs_info = response_info.get_json()
    for log in logs_info:
        assert log['level'] == 'INFO'
        
    response_error = client.get('/api/logs?level=ERROR&limit=5')
    logs_error = response_error.get_json()
    for log in logs_error:
        assert log['level'] == 'ERROR'

def test_api_stocks(client):
    """Test the stocks endpoint."""
    response = client.get('/api/stocks')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    
    # We should have GOOGL, MSFT, AAPL, AMZN, SRE-CLOUD
    assert len(data) == 5
    for stock in data:
        assert 'ticker' in stock
        assert 'name' in stock
        assert 'price' in stock
        assert 'prev_close' in stock
        assert 'change' in stock
        assert 'change_percent' in stock
        assert 'history' in stock
        assert isinstance(stock['price'], (int, float))
        assert isinstance(stock['history'], list)
        assert len(stock['history']) > 0

def test_api_company(client):
    """Test the company details endpoint."""
    response = client.get('/api/company')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    
    assert 'shifts' in data
    assert 'incidents' in data
    assert len(data['shifts']) == 3
    assert len(data['incidents']) == 3

def test_api_company_action(client):
    """Test SRE action dispatcher."""
    # Test invalid action
    response = client.post('/api/company/action', json={'action': 'invalid_action'})
    assert response.status_code == 400
    
    # Test valid action: restart_service
    response = client.post('/api/company/action', json={'action': 'restart_service'})
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data['status'] == 'SUCCESS'
    assert len(data['logs']) > 0
    
    # INC-104 should be RESOLVED now
    resolved_inc = [inc for inc in data['incidents'] if inc['id'] == 'INC-104']
    assert len(resolved_inc) == 1
    assert resolved_inc[0]['status'] == 'RESOLVED'

def test_blog_route(client):
    """Test that the blog page renders correctly."""
    response = client.get('/blog')
    assert response.status_code == 200
    assert 'My Cloud Lab Blog'.encode('utf-8') in response.data
    assert b'https://docs.google.com/document/d/' in response.data

def test_aws_guide_route(client):
    """Test that the AWS guide page renders correctly."""
    response = client.get('/aws-guide')
    assert response.status_code == 200
    assert 'AWS 部署與架構筆記'.encode('utf-8') in response.data

def test_github_preview_route(client):
    """Test that the GitHub repository preview page renders correctly."""
    response = client.get('/github')
    assert response.status_code == 200
    assert 'GitHub Repository Preview'.encode('utf-8') in response.data
    assert b'README.md' in response.data

if __name__ == "__main__":
    pytest.main([__file__])
