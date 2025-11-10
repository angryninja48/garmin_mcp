"""
Workout-related functions for Garmin Connect MCP Server
"""
import datetime
from typing import Any, Dict, List, Optional, Union, Literal
from typing_extensions import TypedDict

# The garmin_client will be set by the main file
garmin_client = None


def configure(client):
    """Configure the module with the Garmin client instance"""
    global garmin_client
    garmin_client = client

def _check_client():
    """Check if Garmin client is available"""
    if not garmin_client:
        return "❌ Garmin API not available: Missing GARMIN_EMAIL and/or GARMIN_PASSWORD environment variables"
    return None



def _pace_min_km_to_ms(pace_str: str) -> float:
    """Convert pace from min:sec/km format to m/s
    
    Args:
        pace_str: Pace in format "M:SS" (e.g., "4:30" for 4 minutes 30 seconds per km)
    
    Returns:
        Speed in meters per second
    """
    try:
        if ':' in pace_str:
            minutes, seconds = pace_str.split(':')
            total_seconds = int(minutes) * 60 + int(seconds)
        else:
            # If no colon, assume it's just minutes
            total_seconds = float(pace_str) * 60
        
        # Convert to m/s: 1000 meters / total_seconds
        return 1000.0 / total_seconds
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"Invalid pace format: {pace_str}. Use format 'M:SS' (e.g., '4:30')")


class WorkoutStepBase(TypedDict, total=False):
    """Base class for workout steps"""
    type: Literal["warmup", "interval", "rest", "cooldown"]
    goal_type: Literal["time", "distance", "lap_button"]
    goal_value: Union[int, float]
    target_type: Optional[Literal["no.target", "heart_rate", "pace"]]
    target_min: Optional[Union[int, float, str]]
    target_max: Optional[Union[int, float, str]]
    description: Optional[str]


class RepeatStep(TypedDict):
    """Class for repeat steps"""
    type: Literal["repeat"]
    iterations: int
    repeat_steps: List[WorkoutStepBase]


WorkoutStep = Union[WorkoutStepBase, RepeatStep]


def _create_workout_step(step_type: str, goal_type: str, goal_value: Union[int, float], 
                        target_type: str = "no.target", target_min: Optional[Union[int, float]] = None,
                        target_max: Optional[Union[int, float]] = None, description: str = None) -> Dict:
    """Create a workout step with the specified parameters"""
    
    # Step type mapping
    step_type_map = {
        "warmup": {"stepTypeId": 1, "stepTypeKey": "warmup", "displayOrder": 1},
        "cooldown": {"stepTypeId": 2, "stepTypeKey": "cooldown", "displayOrder": 2},
        "interval": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
        "rest": {"stepTypeId": 5, "stepTypeKey": "rest", "displayOrder": 5}
    }
    
    # Goal/End condition mapping
    goal_type_map = {
        "time": {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
        "distance": {"conditionTypeId": 3, "conditionTypeKey": "distance", "displayOrder": 3, "displayable": True},
        "lap_button": {"conditionTypeId": 1, "conditionTypeKey": "lap.button", "displayOrder": 1, "displayable": True}
    }
    
    # Target type mapping
    target_type_map = {
        "no.target": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1},
        "heart_rate": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone", "displayOrder": 4},
        "pace": {"workoutTargetTypeId": 6, "workoutTargetTypeKey": "pace.zone", "displayOrder": 6}
    }
    
    step = {
        "type": "ExecutableStepDTO",
        "stepId": None,  # Will be set by Garmin
        "stepOrder": None,  # Will be set when building workout
        "stepType": step_type_map[step_type],
        "childStepId": None,
        "description": description,
        "endCondition": goal_type_map[goal_type],
        "endConditionValue": goal_value,
        "preferredEndConditionUnit": None,
        "endConditionCompare": None,
        "targetType": target_type_map[target_type],
        "targetValueOne": target_min,
        "targetValueTwo": target_max,
        "targetValueUnit": None,
        "zoneNumber": None,
        "secondaryTargetType": None,
        "secondaryTargetValueOne": None,
        "secondaryTargetValueTwo": None,
        "secondaryTargetValueUnit": None,
        "secondaryZoneNumber": None,
        "endConditionZone": None,
        "strokeType": {"strokeTypeId": 0, "strokeTypeKey": None, "displayOrder": 0},
        "equipmentType": {"equipmentTypeId": 0, "equipmentTypeKey": None, "displayOrder": 0},
        "category": None,
        "exerciseName": None,
        "workoutProvider": None,
        "providerExerciseSourceId": None,
        "weightValue": None,
        "weightUnit": None
    }
    
    return step


def _create_repeat_group(steps: List[Dict], iterations: int) -> Dict:
    """Create a repeat group containing multiple steps"""
    return {
        "type": "RepeatGroupDTO",
        "stepId": None,  # Will be set by Garmin
        "stepOrder": None,  # Will be set when building workout
        "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
        "childStepId": 1,
        "numberOfIterations": iterations,
        "workoutSteps": steps,
        "endConditionValue": iterations,
        "preferredEndConditionUnit": None,
        "endConditionCompare": None,
        "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations", "displayOrder": 7, "displayable": False},
        "skipLastRestStep": False,
        "smartRepeat": False
    }


def register_tools(app):
    """Register all workout-related tools with the MCP server app"""
    
    @app.tool()
    async def get_workouts() -> str:
        """Get all workouts"""
        error = _check_client()
        if error:
            return error
        
        try:
            workouts = garmin_client.get_workouts()
            if not workouts:
                return "No workouts found."
            return workouts
        except Exception as e:
            return f"Error retrieving workouts: {str(e)}"
    
    @app.tool()
    async def get_workout_by_id(workout_id: int) -> str:
        """Get details for a specific workout
        
        Args:
            workout_id: ID of the workout to retrieve
        """
        error = _check_client()
        if error:
            return error
        
        try:
            workout = garmin_client.get_workout_by_id(workout_id)
            if not workout:
                return f"No workout found with ID {workout_id}."
            return workout
        except Exception as e:
            return f"Error retrieving workout: {str(e)}"
    
    @app.tool()
    async def download_workout(workout_id: str) -> str:
        """Download a workout as a FIT file (this will return a message about how to access the file)
        
        Args:
            workout_id: ID of the workout to download
        """
        error = _check_client()
        if error:
            return error
        
        try:
            workout_data = garmin_client.download_workout(workout_id)
            if not workout_data:
                return f"No workout data found for workout with ID {workout_id}."
            
            # Since we can't return binary data directly, we'll inform the user
            return f"Workout data for ID {workout_id} is available. The data is in FIT format and would need to be saved to a file."
        except Exception as e:
            return f"Error downloading workout: {str(e)}"
    
    @app.tool()
    async def create_workout(
        workout_name: str,
        sport_type: str = "running",
        description: str = None,
        steps: Optional[List[WorkoutStep]] = None
    ) -> str:
        """Create and upload a custom workout to Garmin Connect
        
        Args:
            workout_name: Name for the workout
            sport_type: Sport type (running, cycling, swimming, etc.) - default is "running"
            description: Optional description for the workout
            steps: List of workout steps. Each step can be either a regular step or a repeat step.
                Regular step format:
                {
                    "type": "warmup|interval|rest|cooldown",
                    "goal_type": "time|distance|lap_button",
                    "goal_value": number (seconds for time, meters for distance),
                    "target_type": "no.target|heart_rate|pace",
                    "target_min": number (bpm for HR, pace as "M:SS" string for pace),
                    "target_max": number (bpm for HR, pace as "M:SS" string for pace),
                    "description": "optional step description"
                }
                Repeat step format:
                {
                    "type": "repeat",
                    "iterations": number,
                    "repeat_steps": [list of regular steps]
                }
                
        Example steps for a simple interval workout:
        [
            {"type": "warmup", "goal_type": "time", "goal_value": 600, "description": "Easy warm-up"},
            {
                "type": "repeat", 
                "iterations": 3, 
                "repeat_steps": [
                    {"type": "interval", "goal_type": "distance", "goal_value": 1000, "target_type": "pace", "target_min": "4:00", "target_max": "4:30", "description": "Fast 1K"},
                    {"type": "rest", "goal_type": "time", "goal_value": 120, "description": "Recovery jog"}
                ]
            },
            {"type": "cooldown", "goal_type": "time", "goal_value": 300, "description": "Cool down"}
        ]
        """
        try:
            # Use default workout if no steps provided
            if steps is None:
                steps = [
                    {"type": "warmup", "goal_type": "time", "goal_value": 300, "description": "Warm up"},
                    {"type": "interval", "goal_type": "time", "goal_value": 1200, "target_type": "no.target", "description": "Main set"},
                    {"type": "cooldown", "goal_type": "time", "goal_value": 300, "description": "Cool down"}
                ]
            
            # Build workout steps
            workout_steps = []
            step_order = 1
            
            for step_data in steps:
                if step_data["type"] == "repeat":
                    # Handle repeat groups
                    repeat_steps = []
                    child_step_order = 1
                    
                    for repeat_step_data in step_data["repeat_steps"]:
                        # Convert pace if needed
                        target_min = repeat_step_data.get("target_min")
                        target_max = repeat_step_data.get("target_max")
                        
                        if repeat_step_data.get("target_type") == "pace":
                            if target_min and isinstance(target_min, str):
                                target_min = _pace_min_km_to_ms(target_min)
                            if target_max and isinstance(target_max, str):
                                target_max = _pace_min_km_to_ms(target_max)
                        
                        repeat_step = _create_workout_step(
                            step_type=repeat_step_data["type"],
                            goal_type=repeat_step_data["goal_type"], 
                            goal_value=repeat_step_data["goal_value"],
                            target_type=repeat_step_data.get("target_type", "no.target"),
                            target_min=target_min,
                            target_max=target_max,
                            description=repeat_step_data.get("description")
                        )
                        repeat_step["stepOrder"] = child_step_order
                        repeat_step["childStepId"] = 1
                        repeat_steps.append(repeat_step)
                        child_step_order += 1
                    
                    repeat_group = _create_repeat_group(repeat_steps, step_data["iterations"])
                    repeat_group["stepOrder"] = step_order
                    workout_steps.append(repeat_group)
                else:
                    # Handle regular steps
                    target_min = step_data.get("target_min")
                    target_max = step_data.get("target_max")
                    
                    # Convert pace if needed
                    if step_data.get("target_type") == "pace":
                        if target_min and isinstance(target_min, str):
                            target_min = _pace_min_km_to_ms(target_min)
                        if target_max and isinstance(target_max, str):
                            target_max = _pace_min_km_to_ms(target_max)
                    
                    step = _create_workout_step(
                        step_type=step_data["type"],
                        goal_type=step_data["goal_type"],
                        goal_value=step_data["goal_value"],
                        target_type=step_data.get("target_type", "no.target"),
                        target_min=target_min,
                        target_max=target_max,
                        description=step_data.get("description")
                    )
                    step["stepOrder"] = step_order
                    workout_steps.append(step)
                
                step_order += 1
            
            # Sport type mapping (expand as needed)
            sport_type_map = {
                "running": {"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
                "cycling": {"sportTypeId": 2, "sportTypeKey": "cycling", "displayOrder": 2},
                "swimming": {"sportTypeId": 5, "sportTypeKey": "swimming", "displayOrder": 5},
                "walking": {"sportTypeId": 9, "sportTypeKey": "walking", "displayOrder": 9}
            }
            
            sport_type_data = sport_type_map.get(sport_type, sport_type_map["running"])
            
            # Build the complete workout
            workout_data = {
                "workoutName": workout_name,
                "description": description,
                "sportType": sport_type_data,
                "workoutSegments": [
                    {
                        "segmentOrder": 1,
                        "sportType": sport_type_data,
                        "workoutSteps": workout_steps
                    }
                ]
            }
            
            # Upload the workout
            url = f"{garmin_client.garmin_workouts}/workout"
            result = garmin_client.garth.post("connectapi", url, json=workout_data, api=True)
            
            return f"Workout '{workout_name}' created successfully! Result: {result}"
            
        except Exception as e:
            return f"Error creating workout: {str(e)}"
    
    @app.tool()
    async def upload_activity(file_path: str) -> str:
        """Upload an activity from a file (this is just a placeholder - file operations would need special handling)
        
        Args:
            file_path: Path to the activity file (.fit, .gpx, .tcx)
        """
        error = _check_client()
        if error:
            return error
        
        try:
            # This is a placeholder - actual implementation would need to handle file access
            return f"Activity upload from file path {file_path} is not supported in this MCP server implementation."
        except Exception as e:
            return f"Error uploading activity: {str(e)}"

    return app