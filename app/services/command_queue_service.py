# app/services/command_queue_service.py
import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional, Awaitable
import time

logger = logging.getLogger(__name__)

class CommandQueueService:
    """Service for managing command queues for devices"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CommandQueueService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._device_queues: Dict[str, asyncio.Queue] = {}
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._command_delay = 0.4  # 400ms între comenzi consecutive
        self._running = True
        
    def set_command_delay(self, delay_seconds: float):
        """Set the delay between consecutive commands"""
        self._command_delay = max(0.1, min(2.0, delay_seconds))  # Limitați între 100ms și 2s
        logger.info(f"Command delay set to {self._command_delay} seconds")
        
    async def add_command(self, 
                         device_id: str, 
                         command_func: Callable[..., Awaitable[bool]], 
                         command_args: List[Any] = None, 
                         command_kwargs: Dict[str, Any] = None,
                         priority: int = 0):
        """Add a command to a device's queue"""
        # Ensure the device has a queue
        if device_id not in self._device_queues:
            self._device_queues[device_id] = asyncio.Queue()
            # Start a processing task for this device
            self._processing_tasks[device_id] = asyncio.create_task(
                self._process_device_queue(device_id)
            )
            
        # Create command object
        command = {
            "func": command_func,
            "args": command_args or [],
            "kwargs": command_kwargs or {},
            "timestamp": time.time(),
            "priority": priority,  # Lower values = higher priority
            "id": id(command_func)  # Unique identifier for the command
        }
        
        # Add to the device's queue
        await self._device_queues[device_id].put(command)
        logger.debug(f"Command added to queue for device {device_id}")
        
    async def add_bulk_command(self,
                              device_ids: List[str],
                              command_func: Callable[..., Awaitable[bool]],
                              command_args: List[Any] = None,
                              command_kwargs: Dict[str, Any] = None,
                              sequential: bool = True,
                              bypass_queue: bool = False):  # Parameter for direct execution
        """Add the same command to multiple devices' queues with coordination"""
        base_timestamp = time.time()
        results = {}
        
        # If bypass_queue is True, execute commands directly for true simultaneity
        if bypass_queue:
            # Create tasks to execute all commands in parallel
            tasks = []
            for device_id in device_ids:
                # Create a copy of args and kwargs for this specific device
                args_copy = list(command_args) if command_args else []
                if args_copy and args_copy[0] is None:
                    args_copy[0] = device_id
                else:
                    args_copy.insert(0, device_id)
                    
                kwargs_copy = command_kwargs.copy() if command_kwargs else {}
                
                # Create task to execute command directly
                tasks.append(command_func(*args_copy, **kwargs_copy))
            
            # Wait for all commands to complete
            if tasks:
                results_list = await asyncio.gather(*tasks, return_exceptions=True)
                # Map results to device IDs
                for i, device_id in enumerate(device_ids):
                    if isinstance(results_list[i], Exception):
                        logger.error(f"Error executing command for device {device_id}: {results_list[i]}")
                        results[device_id] = False
                    else:
                        results[device_id] = results_list[i]
            
            return results
        
        # Original queue-based implementation
        for index, device_id in enumerate(device_ids):
            # If sequential processing is requested, add increasing delays
            delay_factor = index if sequential else 0
            priority = delay_factor
            
            # Create a copy of args for this device
            args_copy = list(command_args) if command_args else []
            # Replace None with device_id if that's the pattern
            if args_copy and args_copy[0] is None:
                args_copy[0] = device_id
            
            # Create a copy of kwargs
            kwargs_copy = command_kwargs.copy() if command_kwargs else {}
            
            # Add the command to this device's queue
            await self.add_command(
                device_id=device_id,
                command_func=command_func,
                command_args=args_copy,
                command_kwargs=kwargs_copy,
                priority=priority
            )
        
        logger.info(f"Bulk command added for {len(device_ids)} devices")
        return {device_id: True for device_id in device_ids}  # Return pending results
            
    async def _process_device_queue(self, device_id: str):
        """Process commands for a specific device"""
        logger.info(f"Started command queue processor for device {device_id}")
        
        last_command_time = 0
        
        while self._running:
            try:
                # Get the next command
                command = await self._device_queues[device_id].get()
                
                # Calculate delay to ensure minimum time between commands
                time_since_last = time.time() - last_command_time
                if time_since_last < self._command_delay:
                    await asyncio.sleep(self._command_delay - time_since_last)
                
                # Execute the command
                func = command["func"]
                args = command["args"]
                kwargs = command["kwargs"]
                
                logger.debug(f"Executing command for device {device_id}")
                try:
                    result = await func(*args, **kwargs)
                    logger.debug(f"Command result for device {device_id}: {result}")
                except Exception as e:
                    logger.error(f"Error executing command for device {device_id}: {e}")
                
                # Mark command as done
                self._device_queues[device_id].task_done()
                
                # Update last command time
                last_command_time = time.time()
                
            except asyncio.CancelledError:
                logger.info(f"Command queue processor for device {device_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in command queue processor for device {device_id}: {e}")
                # Add a small delay to prevent tight loops on persistent errors
                await asyncio.sleep(1)
    
    async def clear_queue(self, device_id: str):
        """Clear all pending commands for a device"""
        if device_id in self._device_queues:
            # Create a new queue to replace the existing one
            old_queue = self._device_queues[device_id]
            self._device_queues[device_id] = asyncio.Queue()
            
            # Clear the old queue
            while not old_queue.empty():
                try:
                    old_queue.get_nowait()
                    old_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            logger.info(f"Command queue cleared for device {device_id}")
    
    async def shutdown(self):
        """Shutdown the command queue service"""
        self._running = False
        
        # Cancel all processing tasks
        for device_id, task in self._processing_tasks.items():
            if not task.done():
                task.cancel()
                
        # Wait for tasks to finish
        for device_id, task in self._processing_tasks.items():
            try:
                await task
            except asyncio.CancelledError:
                pass
            
        logger.info("Command queue service shut down")

# Create singleton instance
command_queue = CommandQueueService()