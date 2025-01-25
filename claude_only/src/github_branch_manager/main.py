import os
from .config import Config
from .branch_manager import BranchManager
from .logger import setup_logger

def main():
    logger = setup_logger()
    try:
        config = Config.from_env()
        manager = BranchManager(config)
        
        # Process all repositories in the organization
        for repo in manager.org.get_repos():
            logger.info(f"Processing repository: {repo.name}")
            manager.archive_branches(repo.name)
            
    except Exception as e:
        logger.error(f"Failed to process repositories: {str(e)}")
        raise

if __name__ == "__main__":
    main() 