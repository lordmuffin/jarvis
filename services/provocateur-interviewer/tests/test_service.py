import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from app.background.provocateur import ProvocateurWorker
from app.realtime.interviewer import summarize_session, trigger_gitpulse

@pytest.mark.asyncio
async def test_provocateur_stale_logic():
    worker = ProvocateurWorker()
    with patch("pathlib.Path.stat") as mock_stat:
        # Mock a file from 40 days ago (stale)
        mock_stat.return_value.st_mtime = 0 
        is_stale = worker.is_stale(Path("test.md"), days=30)
        assert is_stale is True

        # Mock a file from now (fresh)
        import time
        mock_stat.return_value.st_mtime = time.time()
        is_stale = worker.is_stale(Path("test.md"), days=30)
        assert is_stale is False

@pytest.mark.asyncio
async def test_provocateur_crawler():
    worker = ProvocateurWorker()
    worker.gemini.generate_content = AsyncMock(return_value="What is the meaning of life?")
    worker.messaging.publish = AsyncMock()
    
    with patch("os.walk") as mock_walk:
        mock_walk.return_value = [("/tmp", [], ["note.md"])]
        with patch("pathlib.Path.read_text", return_value="Some content here"):
            with patch.object(worker, "is_stale", return_value=True):
                await worker.process_vault()
                
                worker.gemini.generate_content.assert_called_once()
                worker.messaging.publish.assert_called_once()

@pytest.mark.asyncio
async def test_summarize_session():
    with patch("app.realtime.interviewer.gemini_service.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "# Lessons Learned\n..."
        history = ["User: Hi", "Journalist: Hello"]
        summary = await summarize_session(history)
        assert "Lessons Learned" in summary
        mock_gen.assert_called_once()

@pytest.mark.asyncio
async def test_trigger_gitpulse():
    with patch("app.realtime.interviewer.messaging_service.publish", new_callable=AsyncMock) as mock_pub:
        await trigger_gitpulse("Summary content")
        mock_pub.assert_called_once()
        assert mock_pub.call_args[0][0] == "gitpulse.create_pr"
