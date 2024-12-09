import logging
import watchtower
import boto3
from datetime import datetime

def setup_cloudwatch_logging(app_name='maps-server'):
    # Create CloudWatch Logs client (not CloudWatch metrics)
    logs = boto3.client('logs', region_name='eu-central-1')  # Replace with your region
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create CloudWatch handler
    handler = watchtower.CloudWatchLogHandler(
        log_group=f'{app_name}-logs',
        log_stream_name=datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
        boto3_client=logs  # Use logs client instead of cloudwatch client
    )
    
    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger