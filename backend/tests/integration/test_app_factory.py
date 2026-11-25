"""
Integration test for Flask app factory.
"""

from unittest.mock import MagicMock, patch

from app import create_app


class TestAppFactory:
    """Test Flask app creation."""
    
    @patch("app.extensions.MongoClient")
    @patch("app.services.engine.init_engine")
    def test_create_app(self, mock_init_engine, mock_mongo_client):
        """Test that app can be created with mocked MongoDB."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.users.create_index = MagicMock()
        mock_db.profiles.create_index = MagicMock()
        mock_db.connection_requests.create_index = MagicMock()
        mock_db.connections.create_index = MagicMock()
        mock_db.posts.create_index = MagicMock()
        
        app = create_app("testing")
        
        assert app is not None
        assert app.config["TESTING"] is True
        
        # Check blueprints registered
        assert "auth" in app.blueprints
        assert "profile" in app.blueprints
        assert "users" in app.blueprints
        assert "connections" in app.blueprints
        assert "posts" in app.blueprints
        assert "health" in app.blueprints
    
    @patch("app.extensions.MongoClient")
    @patch("app.services.engine.init_engine")
    def test_health_live_endpoint(self, mock_init_engine, mock_mongo_client):
        """Test health liveness endpoint."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.users.create_index = MagicMock()
        mock_db.profiles.create_index = MagicMock()
        mock_db.connection_requests.create_index = MagicMock()
        mock_db.connections.create_index = MagicMock()
        mock_db.posts.create_index = MagicMock()
        
        app = create_app("testing")
        client = app.test_client()
        
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "alive"
    
    @patch("app.extensions.MongoClient")
    @patch("app.services.engine.init_engine")
    def test_health_ready_endpoint(self, mock_init_engine, mock_mongo_client):
        """Test health readiness endpoint."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_mongo_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_db.users.create_index = MagicMock()
        mock_db.profiles.create_index = MagicMock()
        mock_db.connection_requests.create_index = MagicMock()
        mock_db.connections.create_index = MagicMock()
        mock_db.posts.create_index = MagicMock()
        
        # Mock ping command
        mock_client.admin.command.return_value = {"ok": 1}
        
        app = create_app("testing")
        
        # Mock DSA engine - patch where it's used in health_routes
        with patch("app.services.engine.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.is_initialized = True
            mock_get_engine.return_value = mock_engine
            
            client = app.test_client()
            response = client.get("/api/v1/health/ready")
            
            # Should be ready with mocked dependencies
            assert response.status_code == 200
            data = response.get_json()
            assert data["status"] == "ready"