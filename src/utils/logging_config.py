import logging
import sys
from pathlib import Path

def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    memory_logger = logging.getLogger('memory_system')
    workflow_logger = logging.getLogger('workflow_engine')
    query_logger = logging.getLogger('query_planning')
    
    return memory_logger, workflow_logger, query_logger