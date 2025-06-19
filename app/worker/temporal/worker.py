import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio import activity, workflow
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the worker directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all activities and workflows
from worker.temporal.activities.data_collection import collect_market_data
from temporal.activities.ml_analysis import run_ml_analysis
from temporal.activities.rag_analysis import get_rag_context, update_rag_knowledge_base
from temporal.activities.llama_analysis import generate_llama_recommendations, test_llama_connection
from temporal.activities.combine_recommendations import combine_recommendations, store_recommendations
from temporal.workflows.recommendation_workflow import DailyRecommendationWorkflow

async def main():
    """Main function to run the Temporal worker."""
    
    # Connect to local Temporal server
    temporal_host = "localhost:7233"
    ollama_host = "localhost:11434"
    
    logger.info(f"Connecting to Temporal server at: {temporal_host}")
    logger.info(f"Ollama host: {ollama_host}")
    
    try:
        # Connect to Temporal server
        client = await Client.connect(temporal_host)
        logger.info("Successfully connected to Temporal server")
        
        # Create worker
        worker = Worker(
            client,
            task_queue="recommendation-task-queue",
            workflows=[DailyRecommendationWorkflow],
            activities=[
                collect_market_data,
                run_ml_analysis,
                get_rag_context,
                generate_llama_recommendations,
                combine_recommendations,
                store_recommendations,
                update_rag_knowledge_base,
                test_llama_connection
            ]
        )
        
        logger.info("Starting recommendation worker...")
        logger.info(f"Registered workflows: {[w.__name__ for w in worker.workflows]}")
        logger.info(f"Registered activities: {[a.__name__ for a in worker.activities]}")
        
        # Run the worker
        await worker.run()
        
    except Exception as e:
        logger.error(f"Failed to start worker: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)
