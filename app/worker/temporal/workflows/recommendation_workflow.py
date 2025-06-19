from datetime import datetime, timedelta
from temporalio import workflow
from typing import List, Dict, Any
from worker.temporal.activities.data_collection import collect_market_data
from temporal.activities.ml_analysis import run_ml_analysis
from temporal.activities.rag_analysis import get_rag_context
from temporal.activities.llama_analysis import generate_llama_recommendations
from temporal.activities.combine_recommendations import combine_recommendations, store_recommendations
from temporal.models import CombinedRecommendation

@workflow.defn
class DailyRecommendationWorkflow:
    @workflow.run
    async def run(self) -> List[CombinedRecommendation]:
        """Generate 5 daily trade recommendations using multiple analysis methods."""
        
        # Step 1: Collect market data
        market_data = await workflow.execute_activity(
            collect_market_data,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Step 2: Run classical ML analysis
        ml_recommendations = await workflow.execute_activity(
            run_ml_analysis,
            market_data,
            start_to_close_timeout=timedelta(minutes=15)
        )
        
        # Step 3: Run RAG analysis for context
        rag_context = await workflow.execute_activity(
            get_rag_context,
            market_data,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Step 4: Generate Llama recommendations with RAG context
        llama_recommendations = await workflow.execute_activity(
            generate_llama_recommendations,
            market_data,
            rag_context,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Step 5: Combine and rank recommendations
        final_recommendations = await workflow.execute_activity(
            combine_recommendations,
            ml_recommendations,
            llama_recommendations,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Step 6: Store recommendations in database
        await workflow.execute_activity(
            store_recommendations,
            final_recommendations,
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        return final_recommendations[:5]  # Return top 5 recommendations 