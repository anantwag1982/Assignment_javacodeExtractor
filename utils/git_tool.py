import os
import shutil
import asyncio
from git import Repo
from git.exc import GitCommandError

class GitManager:
    def __init__(self, logger, exception_handler):
        self.logger = logger
        self.exception_handler = exception_handler
    
    async def clone_repository(self, repo_url: str, clone_dir: str) -> str:
        repo_name = os.path.splitext(os.path.basename(repo_url.rstrip("/")))[0]
        local_dir = os.path.join(clone_dir, repo_name)
        
        # Remove corrupted repo if exists
        if os.path.exists(local_dir) and not os.path.isdir(os.path.join(local_dir, '.git')):
            self.logger.warning(f"Removing corrupted repo: {local_dir}")
            await asyncio.to_thread(shutil.rmtree, local_dir)
        
        if not os.path.exists(local_dir):
            try:
                self.logger.info(f"Cloning repository: {repo_url}")
                await asyncio.to_thread(Repo.clone_from, repo_url, local_dir)
                return local_dir
            except GitCommandError as ex:
                await self.exception_handler.handle(ex, "clone_repository")
                raise
        else:
            self.logger.info(f"Repository exists: {local_dir}")
            return local_dir