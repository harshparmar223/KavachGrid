"""
KavachGrid — GIS API Unit Tests
Author: Abhishek
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_get_topology():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/gis/topology")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "lines" in data
        assert "center" in data
        assert "zoom" in data
        assert "total_nodes" in data


@pytest.mark.asyncio
async def test_get_heatmap():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/gis/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
