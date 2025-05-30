"""
Workout-related functions for Garmin Connect MCP Server
"""
import datetime
from typing import Any, Dict, List, Optional, Union

# The garmin_client will be set by the main file
garmin_client = None


def configure(client):
    """Configure the module with the Garmin client instance"""
    global garmin_client
    garmin_client = client


def register_tools(app):
    """Register all workout-related tools with the MCP server app"""
    
    @app.tool()
    async def get_workouts() -> str:
        """Get all workouts"""
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
        try:
            workout_data = garmin_client.download_workout(workout_id)
            if not workout_data:
                return f"No workout data found for workout with ID {workout_id}."
            
            # Since we can't return binary data directly, we'll inform the user
            return f"Workout data for ID {workout_id} is available. The data is in FIT format and would need to be saved to a file."
        except Exception as e:
            return f"Error downloading workout: {str(e)}"
    
    @app.tool()
    async def upload_workout() -> str:
        """Upload a workout from JSON data
        
        Args:
            workout_json: JSON string containing workout data
        """
        try:
            workout_example = {
                'workoutName': 'So Simple session 5',
                'sportType': {
                    'sportTypeId': 1,
                    'sportTypeKey': 'running',
                    'displayOrder': 1
                },
                'workoutSegments': [
                    {
                        'segmentOrder': 1,
                        'sportType': {
                            'sportTypeId': 1,
                            'sportTypeKey': 'running',
                            'displayOrder': 1
                        },
                        'workoutSteps': [
                            {
                                'type': 'ExecutableStepDTO',
                                'stepId': 633927266,
                                'stepOrder': 1,
                                'stepType': {
                                    'stepTypeId': 1,
                                    'stepTypeKey': 'warmup',
                                    'displayOrder': 1
                                },
                                'endCondition': {
                                    'conditionTypeId': 2,
                                    'conditionTypeKey': 'time',
                                    'displayOrder': 2,
                                    'displayable': True
                                },
                                'endConditionValue': 180.0,
                                'targetType': {
                                    'workoutTargetTypeId': 1,
                                    'workoutTargetTypeKey': 'no.target',
                                    'displayOrder': 1
                                },
                                'strokeType': {
                                    'strokeTypeId': 0,
                                    'displayOrder': 0
                                },
                                'equipmentType': {
                                    'equipmentTypeId': 0,
                                    'displayOrder': 0
                                }
                            },
                        ]
                    }
                ]
            }

            # Use the garth client directly to upload the workout
            url = f"{garmin_client.garmin_workouts}/workout"
            result = garmin_client.garth.post("connectapi", url, json=workout_example, api=True)
            return result
        except Exception as e:
            return f"Error uploading workout: {str(e)}"
            
    @app.tool()
    async def upload_activity(file_path: str) -> str:
        """Upload an activity from a file (this is just a placeholder - file operations would need special handling)
        
        Args:
            file_path: Path to the activity file (.fit, .gpx, .tcx)
        """
        try:
            # This is a placeholder - actual implementation would need to handle file access
            return f"Activity upload from file path {file_path} is not supported in this MCP server implementation."
        except Exception as e:
            return f"Error uploading activity: {str(e)}"

    return app