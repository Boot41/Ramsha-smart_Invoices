Key Area for Optimization: Pausing and Resuming Workflows for Human Input

  The most critical aspect for seamless human-in-the-loop interaction is how the wait_for_human_input function
  truly pauses the asynchronous workflow and then resumes it upon receiving input.

  Proposed Optimization Strategy:

  The core idea is to use asyncio.Event objects to effectively pause and resume the specific workflow task that
  requires human input.

   1. `orchestrator_service.py` Enhancements:
       * Maintain State for Human Input: Introduce two dictionaries within OrchestratorService:
           * human_input_events: Dict[str, asyncio.Event]: To store an asyncio.Event object for each workflow task
             that is currently waiting for human input.
           * human_input_data: Dict[str, Any]: To temporarily store the human input received for a specific task_id.
       * New `wait_for_human_input` Method: Implement an async method in OrchestratorService that:
           * Creates an asyncio.Event for the given task_id.
           * Updates the workflow's internal status (e.g., in running_workflows) to WAITING_FOR_HUMAN_INPUT.
           * Sends a websocket message to the frontend (via websocket_manager) indicating that human input is
             required, including the task_id and the prompt.
           * Calls await self.human_input_events[task_id].wait(). This will pause the specific workflow task until
             the event is set.
           * Once the event is set, it retrieves the user_input from human_input_data, cleans up the event and data,
             and returns the input to the workflow.
       * New `process_human_input` Method: Implement a method in OrchestratorService that:
           * Receives the task_id and user_input from the /human_input endpoint.
           * Stores the user_input in human_input_data[task_id].
           * Calls self.human_input_events[task_id].set() to unblock the waiting workflow task.
           * Optionally, sends a websocket message to the frontend confirming that the input was received and the
             workflow is resuming.
       * Store `user_id` with Task: Ensure that the user_id is stored alongside the asyncio.Task in the
         running_workflows dictionary. This allows the websocket_manager to send targeted messages to the correct
         user.

   2. `controller/orchestrator_controller.py` Update:
       * Modify the process_human_input function to call the new orchestrator_service.process_human_input method.

   3. `workflows/invoice_workflow.py` (and other workflows):
       * The self.orchestrator.wait_for_human_input call will now be an await call, correctly pausing the workflow
         until input is received.

  Frontend Integration (Conceptual):

   * Websocket Listener: The frontend should have a dedicated websocket listener that processes messages from the
     backend. When a message with status: "WAITING_FOR_HUMAN_INPUT" is received, it should display the prompt and an
     input field.
   * HTTP for Input Submission: When the user provides input, the frontend sends an HTTP POST request to the
     /human_input endpoint.
   * Workflow State Display: The frontend can use the websocket messages (and optionally poll the
     /orchestrator/status/{task_id} endpoint) to display the current status of the workflow to the user (e.g.,
     "Running validation...", "Waiting for your review...", "Completed").

  This approach ensures that your backend workflows are truly non-blocking while waiting for human input, and that
  communication with the frontend is real-time and efficient.

  Would you like me to proceed with implementing these changes in the relevant files?