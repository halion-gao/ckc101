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

def test_cors_headers_and_options(client):
    """Test CORS headers on GET request and OPTIONS preflight."""
    # Test GET has CORS headers
    response = client.get('/api/metrics')
    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == '*'
    assert response.headers.get('Access-Control-Allow-Headers') == 'Content-Type,Authorization'
    assert response.headers.get('Access-Control-Allow-Methods') == 'GET,POST,PUT,DELETE,OPTIONS'

    # Test OPTIONS preflight request to api route
    response_opt = client.options('/api/company/action')
    assert response_opt.status_code == 200
    assert response_opt.headers.get('Access-Control-Allow-Origin') == '*'
    assert response_opt.headers.get('Access-Control-Allow-Headers') == 'Content-Type,Authorization'
    assert response_opt.headers.get('Access-Control-Allow-Methods') == 'GET,POST,PUT,DELETE,OPTIONS'

def test_list_s3_files(client):
    """Test listing files from S3 bucket."""
    from unittest.mock import patch
    import datetime
    
    mock_response = {
        "Contents": [
            {
                "Key": "test-file.txt",
                "Size": 1024,
                "LastModified": datetime.datetime(2026, 5, 28, 12, 0, 0)
            }
        ]
    }
    with patch('src.app.s3_client.list_objects_v2', return_value=mock_response) as mock_list:
        response = client.get('/api/s3/files')
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()
        assert data['status'] == 'SUCCESS'
        assert len(data['files']) == 1
        assert data['files'][0]['key'] == 'test-file.txt'
        assert data['files'][0]['size'] == 1024
        assert data['files'][0]['last_modified'] == '2026-05-28 12:00:00'
        mock_list.assert_called_once_with(Bucket='ckc101-07')

def test_list_s3_files_error(client):
    """Test S3 file listing error handling."""
    from unittest.mock import patch
    from botocore.exceptions import ClientError
    
    error_response = {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist'}}
    with patch('src.app.s3_client.list_objects_v2', side_effect=ClientError(error_response, 'ListObjectsV2')):
        response = client.get('/api/s3/files')
        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'ERROR'
        assert 'NoSuchBucket' in data['message'] or 'bucket does not exist' in data['message']

def test_upload_to_s3(client):
    """Test uploading a file to S3 bucket."""
    from unittest.mock import patch
    import io
    
    data = {
        'file': (io.BytesIO(b'dummy file content'), 'test_upload.txt')
    }
    with patch('src.app.s3_client.upload_fileobj') as mock_upload:
        response = client.post('/api/s3/upload', data=data, content_type='multipart/form-data')
        assert response.status_code == 200
        assert response.is_json
        res_data = response.get_json()
        assert res_data['status'] == 'SUCCESS'
        assert 'test_upload.txt' in res_data['message']
        assert res_data['key'] == 'test_upload.txt'
        
        assert mock_upload.call_count == 1
        args, kwargs = mock_upload.call_args
        assert args[1] == 'ckc101-07'
        assert args[2] == 'test_upload.txt'

def test_upload_to_s3_no_file(client):
    """Test upload failing when no file part is present."""
    response = client.post('/api/s3/upload', data={})
    assert response.status_code == 400
    assert response.get_json()['status'] == 'ERROR'

def test_api_cpu_stress(client):
    """Test the CPU stress API endpoint."""
    from unittest.mock import patch
    
    with patch('multiprocessing.Process') as mock_process:
        response = client.post('/api/cpu/stress?duration=5')
        assert response.status_code == 200
        assert response.is_json
        data = response.get_json()
        assert data['status'] == 'SUCCESS'
        assert 'Stressing CPU' in data['message']
        assert mock_process.call_count > 0

if __name__ == "__main__":
    pytest.main([__file__])
