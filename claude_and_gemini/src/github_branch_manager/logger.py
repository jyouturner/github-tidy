import logging
from google.cloud import logging as cloud_logging

def setup_logger():
    logger = logging.getLogger('github-branch-manager')
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Cloud Logging handler
        client = cloud_logging.Client()
        cloud_handler = cloud_logging.handlers.CloudLoggingHandler(client)
        cloud_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(cloud_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)
    
    return logger 