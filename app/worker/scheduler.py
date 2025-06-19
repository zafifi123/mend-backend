import asyncio
from temporalio.client import Client
from datetime import datetime, timedelta
import pytz
import os
import sys

# Add the worker directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from temporal.workflows.recommendation_workflow import DailyRecommendationWorkflow

async def schedule_daily_recommendations():
    """Schedule the daily recommendation workflow using cron."""
    
    # Connect to local Temporal server
    client = await Client.connect("localhost:7233")
    
    # Get current time in EST (market timezone)
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    
    print(f"Current time (EST): {now}")
    
    # Schedule workflow to run daily at 4:00 AM EST (premarket open)
    # Cron format: minute hour day month day_of_week
    # 0 4 * * * = Every day at 4:00 AM
    cron_schedule = "0 4 * * *"
    
    try:
        # Start the workflow with cron schedule
        handle = await client.start_workflow(
            DailyRecommendationWorkflow.run,
            id="daily-recommendations-cron",
            task_queue="recommendation-task-queue",
            cron_schedule=cron_schedule
        )
        
        print(f"Scheduled daily workflow with ID: {handle.id}")
        print(f"Cron schedule: {cron_schedule} (4:00 AM EST daily)")
        return handle
        
    except Exception as e:
        print(f"Error scheduling workflow: {e}")
        print("Falling back to immediate execution...")
        
        # Fallback: run immediately
        handle = await client.start_workflow(
            DailyRecommendationWorkflow.run,
            id=f"daily-recommendations-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            task_queue="recommendation-task-queue"
        )
        
        print(f"Started immediate workflow with ID: {handle.id}")
        return handle

async def run_manual_recommendation():
    """Run the recommendation workflow manually for testing."""
    
    client = await Client.connect("localhost:7233")
    
    handle = await client.start_workflow(
        DailyRecommendationWorkflow.run,
        id=f"manual-recommendations-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        task_queue="recommendation-task-queue"
    )
    
    print(f"Started manual workflow with ID: {handle.id}")
    
    # Wait for completion
    result = await handle.result()
    print(f"Workflow completed with {len(result)} recommendations")
    
    return result

async def main():
    """Main function to run the scheduler."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        # Run manual recommendation
        await run_manual_recommendation()
    else:
        # Schedule daily recommendations
        await schedule_daily_recommendations()

if __name__ == "__main__":
    asyncio.run(main())
