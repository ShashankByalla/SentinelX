# agent/auto_resolver.py
import os
import subprocess
import logging

logger = logging.getLogger("auto_resolver")

class AutoResolver:
    def __init__(self):
        self.rules = {
            "pb-001-restart-app": self.restart_app,
            "pb-002-restart-nginx": self.restart_nginx,
            "pb-003-high-cpu": self.restart_sentinelx,
            "pb-021-db-timeout": self.restart_app,  # fallback for now
        }

    def resolve(self, playbook_id: str):
        """Run resolution action based on playbook_id"""
        action = self.rules.get(playbook_id)
        if not action:
            logger.warning(f"No resolver implemented for {playbook_id}")
            return {"ok": False, "error": f"No resolver for {playbook_id}"}

        try:
            result = action()
            return {"ok": True, "result": result}
        except Exception as e:
            logger.error(f"Resolution failed for {playbook_id}: {e}")
            return {"ok": False, "error": str(e)}

    def restart_app(self):
        """Restart dummy_service app inside host"""
        logger.info("Restarting dummy_service app...")
        subprocess.run(["pkill", "-f", "dummy_service.py"], check=False)
        subprocess.Popen(["python", "agent/dummy_service.py"], cwd="/app")
        return "dummy_service restarted"

    def restart_nginx(self):
        """Restart nginx container"""
        logger.info("Restarting nginx container...")
        subprocess.run(["docker", "restart", "sentinelx_nginx"], check=True)
        return "nginx restarted"

    def restart_sentinelx(self):
        """Restart sentinelx container itself"""
        logger.info("Restarting sentinelx container...")
        subprocess.run(["docker", "restart", "sentinelx"], check=True)
        return "sentinelx restarted"
