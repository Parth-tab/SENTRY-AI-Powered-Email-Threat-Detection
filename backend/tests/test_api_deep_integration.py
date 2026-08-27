import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_full_api_suite():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

        # 2. Seed demo samples
        r_seed = await client.post("/api/v1/samples/seed")
        assert r_seed.status_code in [200, 201, 409]

        # 3. List emails with pagination & search
        r_emails = await client.get("/api/v1/emails?limit=10&offset=0")
        assert r_emails.status_code == 200
        data = r_emails.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        email_id = data[0]["id"]

        # 4. Get email details
        r_detail = await client.get(f"/api/v1/emails/{email_id}")
        assert r_detail.status_code == 200
        detail_json = r_detail.json()
        assert "email" in detail_json
        assert "analysis" in detail_json

        # 5. Verify RFC 3227 Chain
        r_chain = await client.post(f"/api/v1/evidence/verify/{email_id}")
        assert r_chain.status_code == 200
        chain_json = r_chain.json()
        assert chain_json["is_valid"] is True

        # 6. Download PDF Report
        r_pdf = await client.get(f"/api/v1/emails/{email_id}/report/pdf")
        assert r_pdf.status_code == 200
        assert r_pdf.headers["content-type"] == "application/pdf"
        assert len(r_pdf.content) > 1000

        # 7. Dashboard Stats
        r_stats = await client.get("/api/v1/dashboard/stats")
        assert r_stats.status_code == 200
        stats_json = r_stats.json()
        assert stats_json["total_emails_analyzed"] >= 1

        # 8. Campaigns List & Graph
        r_camps = await client.get("/api/v1/campaigns")
        assert r_camps.status_code == 200
        assert len(r_camps.json()) >= 1

        r_graph = await client.get("/api/v1/campaigns/graph/all")
        assert r_graph.status_code == 200
        graph_json = r_graph.json()
        assert "nodes" in graph_json
        assert "links" in graph_json

        # 9. 404 Case
        r_404 = await client.get("/api/v1/emails/00000000-0000-0000-0000-000000000000")
        assert r_404.status_code == 404
