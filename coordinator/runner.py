import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from coordinator.graph import create_event_planning_graph
from coordinator.config import DEBUG_MODE, VERBOSE_LOGGING

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EventPlanRunner:
    """
    Test runner and debugger for the EventPlanGenie workflow
    """
    
    def __init__(self, **graph_kwargs):
        """Initialize the runner with graph configuration"""
        self.graph = create_event_planning_graph(**graph_kwargs)
        self.execution_history = []
        
    async def run_sample_event(self, event_type: str = "birthday_party") -> Dict[str, Any]:
        """Run a sample event planning workflow"""
        
        sample_inputs = {
            "birthday_party": {
                "event_type": "birthday_party",
                "budget": 5000.0,
                "estimated_guests": 25,
                "preferred_date": "2025-08-15",
                "preferred_time": "18:00",
                "duration_hours": 4,
                "user_preferences": {
                    "indoor": True,
                    "near_city_center": True,
                    "parking_required": True,
                    "theme": "tropical"
                },
                "location_preferences": {
                    "venue_type": "restaurant",
                    "max_distance_km": 20,
                    "accessibility_required": False
                }
            },
            "wedding": {
                "event_type": "wedding",
                "budget": 25000.0,
                "estimated_guests": 120,
                "preferred_date": "2025-09-20",
                "preferred_time": "16:00",
                "duration_hours": 8,
                "user_preferences": {
                    "outdoor": True,
                    "elegant": True,
                    "photography_important": True,
                    "theme": "romantic"
                },
                "location_preferences": {
                    "venue_type": "garden",
                    "max_distance_km": 50,
                    "accessibility_required": True
                }
            },
            "corporate_event": {
                "event_type": "corporate_event",
                "budget": 15000.0,
                "estimated_guests": 80,
                "preferred_date": "2025-07-10",
                "preferred_time": "09:00",
                "duration_hours": 6,
                "user_preferences": {
                    "professional": True,
                    "tech_equipment": True,
                    "catering": True,
                    "theme": "innovation"
                },
                "location_preferences": {
                    "venue_type": "conference_center",
                    "max_distance_km": 15,
                    "accessibility_required": True
                }
            }
        }
        
        test_input = sample_inputs.get(event_type, sample_inputs["birthday_party"])
        return await self.run_event_planning(test_input)
    
    async def run_event_planning(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete event planning workflow"""
        
        start_time = time.time()
        logger.info(f"Starting event planning workflow: {user_input.get('event_type', 'unknown')}")
        
        try:
            # Execute the workflow
            result = await self.graph.plan_event(user_input)
            
            execution_time = time.time() - start_time
            
            # Log execution details
            execution_record = {
                "timestamp": datetime.now().isoformat(),
                "input": user_input,
                "result": result,
                "execution_time": execution_time,
                "success": result.get("success", False)
            }
            
            self.execution_history.append(execution_record)
            
            logger.info(f"Workflow completed in {execution_time:.2f}s - Success: {result.get('success', False)}")
            
            if VERBOSE_LOGGING:
                self._log_detailed_results(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow failed with error: {str(e)}")
            error_result = {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            
            self.execution_history.append({
                "timestamp": datetime.now().isoformat(),
                "input": user_input,
                "result": error_result,
                "execution_time": time.time() - start_time,
                "success": False
            })
            
            return error_result
    
    def _log_detailed_results(self, result: Dict[str, Any]):
        """Log detailed results for debugging"""
        
        if result.get("success"):
            event_plan = result.get("event_plan", {})
            logger.debug(f"Generated event plan with:")
            logger.debug(f"  - Idea: {event_plan.get('idea', {}).get('title', 'N/A')}")
            logger.debug(f"  - Location: {event_plan.get('location', {}).get('name', 'N/A')}")
            logger.debug(f"  - Vendors: {len(event_plan.get('vendors', {}))}")
            logger.debug(f"  - Schedule items: {len(event_plan.get('schedule', {}).get('timeline_breakdown', []))}")
            
            files = result.get("generated_files", {})
            if files:
                logger.debug(f"Generated files: {list(files.keys())}")
        
        if result.get("errors"):
            logger.warning(f"Workflow had {len(result['errors'])} errors:")
            for error in result["errors"]:
                logger.warning(f"  - {error.get('stage', 'unknown')}: {error.get('error', 'N/A')}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions"""
        
        if not self.execution_history:
            return {"message": "No executions recorded"}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for ex in self.execution_history if ex["success"])
        avg_execution_time = sum(ex["execution_time"] for ex in self.execution_history) / total_executions
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions,
            "average_execution_time": avg_execution_time,
            "last_execution": self.execution_history[-1]["timestamp"] if self.execution_history else None
        }
    
    async def run_performance_test(self, num_iterations: int = 5) -> Dict[str, Any]:
        """Run performance testing with multiple iterations"""
        
        logger.info(f"Starting performance test with {num_iterations} iterations")
        
        performance_results = []
        
        for i in range(num_iterations):
            logger.info(f"Performance test iteration {i+1}/{num_iterations}")
            
            # Alternate between different event types
            event_types = ["birthday_party", "wedding", "corporate_event"]
            event_type = event_types[i % len(event_types)]
            
            result = await self.run_sample_event(event_type)
            performance_results.append({
                "iteration": i + 1,
                "event_type": event_type,
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0),
                "stage": result.get("stage", "unknown")
            })
        
        # Calculate performance metrics
        successful_runs = [r for r in performance_results if r["success"]]
        
        if successful_runs:
            avg_time = sum(r["execution_time"] for r in successful_runs) / len(successful_runs)
            min_time = min(r["execution_time"] for r in successful_runs)
            max_time = max(r["execution_time"] for r in successful_runs)
        else:
            avg_time = min_time = max_time = 0
        
        summary = {
            "total_iterations": num_iterations,
            "successful_runs": len(successful_runs),
            "success_rate": len(successful_runs) / num_iterations,
            "average_execution_time": avg_time,
            "min_execution_time": min_time,
            "max_execution_time": max_time,
            "detailed_results": performance_results
        }
        
        logger.info(f"Performance test completed - Success rate: {summary['success_rate']:.2%}")
        return summary

# Async main functions for different test scenarios
async def run_sample():
    """Run a simple sample event"""
    runner = EventPlanRunner()
    result = await runner.run_sample_event("birthday_party")
    print(json.dumps(result, indent=2, default=str))

async def run_all_samples():
    """Run samples for all event types"""
    runner = EventPlanRunner()
    
    for event_type in ["birthday_party", "wedding", "corporate_event"]:
        print(f"\n{'='*50}")
        print(f"Running sample: {event_type}")
        print(f"{'='*50}")
        
        result = await runner.run_sample_event(event_type)
        print(f"Success: {result.get('success', False)}")
        print(f"Stage: {result.get('stage', 'unknown')}")
        
        if result.get("errors"):
            print(f"Errors: {len(result['errors'])}")

async def run_performance_test():
    """Run performance testing"""
    runner = EventPlanRunner()
    results = await runner.run_performance_test(num_iterations=3)
    print(json.dumps(results, indent=2, default=str))

# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "sample":
            asyncio.run(run_sample())
        elif command == "all":
            asyncio.run(run_all_samples())
        elif command == "performance":
            asyncio.run(run_performance_test())
        else:
            print("Usage: python runner.py [sample|all|performance]")
    else:
        # Default: run sample
        asyncio.run(run_sample())