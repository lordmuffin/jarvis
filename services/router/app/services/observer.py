import asyncio
import logging
from app.services.lemonade import lemonade_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class SystemObserver:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemObserver, cls).__new__(cls)
            cls._instance.is_healthy = False
            cls._instance.metrics = {}
            cls._instance.system_info = {}
            cls._instance.running = False
        return cls._instance

    async def start(self):
        self.running = True
        logger.info("Starting System Observer...")
        asyncio.create_task(self._poll_loop())

    async def stop(self):
        self.running = False
        logger.info("Stopping System Observer...")

    async def _poll_loop(self):
        while self.running:
            try:
                # Parallel fetch
                health, stats, info = await asyncio.gather(
                    lemonade_client.get_health(),
                    lemonade_client.get_stats(),
                    lemonade_client.get_system_info()
                )
                
                self.is_healthy = health
                self.metrics = stats
                self.system_info = info
                
                # logger.debug(f"Observer Update: Healthy={health}, Stats={stats}")
                
            except Exception as e:
                logger.error(f"Observer Error: {e}")
                self.is_healthy = False
            
            await asyncio.sleep(settings.LEMONADE_CHECK_INTERVAL)

    def get_status(self):
        return {
            "is_healthy": self.is_healthy,
            "metrics": self.metrics,
            "system_info": self.system_info
        }

observer = SystemObserver()
