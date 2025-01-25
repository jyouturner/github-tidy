import argparse
import os
from .config import Config
from .branch_manager import BranchManager
from .logger import setup_logger

logger = setup_logger()

def main():
    """Main entry point for the GitHub branch manager."""
    parser = argparse.ArgumentParser(description="GitHub Branch Manager")
    parser.add_argument(
        '--mode',
        choices=['archive', 'purge', 'all'],
        default='all',
        help='Mode to run: archive, purge, or all (default: all)'
    )
    args = parser.parse_args()

    try:
        config = Config.from_env()
    except (EnvironmentError, ValueError) as e:
        logger.error(f"Configuration error: {str(e)}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during configuration: {str(e)}")
        exit(1)

    try:
        manager = BranchManager(config)
        
        # Process all repositories in the organization
        for repo in manager.org.get_repos():
            logger.info(f"Processing repository: {repo.name}")
            
            if args.mode in ['archive', 'all']:
                logger.info(f"Running archive mode for {repo.name}")
                manager.archive_branches(repo.name)
            
            if args.mode in ['purge', 'all']:
                logger.info(f"Running purge mode for {repo.name}")
                manager.purge_branches(repo.name)

    except Exception as e:
        logger.error(f"Failed to process repositories: {str(e)}")
        raise

if __name__ == "__main__":
    main() 