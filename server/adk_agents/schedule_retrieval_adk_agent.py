"""
Schedule Retrieval ADK Agent

Retrieves invoice schedules from Pinecone using RAG and schedules invoices accordingly
"""

from typing import Dict, Any, AsyncGenerator, Optional, List
import logging
from datetime import datetime, timedelta
import json

from google.adk.agents.invocation_context import InvocationContext
from pydantic import PrivateAttr
from services.contract_rag_service import get_contract_rag_service
from services.cloud_scheduler_service import get_cloud_scheduler_service
from services.pinecone_service import get_pinecone_service

from .base_adk_agent import BaseADKAgent, SimpleEvent
from schemas.workflow_schemas import AgentType, ProcessingStatus
from schemas.unified_invoice_schemas import UnifiedInvoiceData

logger = logging.getLogger(__name__)


class ScheduleRetrievalADKAgent(BaseADKAgent):
    """ADK Agent responsible for retrieving invoice schedules using RAG from Pinecone and scheduling invoices"""
    
    _contract_rag_service = PrivateAttr()
    _cloud_scheduler_service = PrivateAttr()
    
    def __init__(self):
        super().__init__(
            name="schedule_retrieval_agent",
            agent_type=AgentType.STORAGE_SCHEDULING,  # Using existing enum value
            description="Retrieves invoice schedules from Pinecone using RAG and schedules invoice generation",
            max_retries=3
        )
        # Initialize concrete services
        self._contract_rag_service = get_contract_rag_service()
        self._cloud_scheduler_service = get_cloud_scheduler_service()

        # ADK client placeholder - try to import a Gemini/ADK client if available
        try:
            from google import adk as _adk  # type: ignore
            self._adk_client = _adk
        except Exception:
            self._adk_client = None
    
    # Concrete services are initialized in __init__
    
    async def run(self, state: Dict[str, Any], context: InvocationContext) -> AsyncGenerator[SimpleEvent, None]:
        """
        ADK implementation for schedule retrieval and invoice scheduling workflow
        
        Steps:
        1. Check if invoice generation completed successfully
        2. Extract invoice characteristics for schedule matching
        3. Query Pinecone for relevant schedules using RAG
        4. Match schedules to invoice characteristics
        5. Schedule invoice generation based on matched schedules
        6. Update workflow state with scheduling information
        """
        workflow_id = state.get('workflow_id')
        user_id = state.get("user_id")
        contract_name = state.get("contract_name")
        
        yield self.create_progress_event(f"🗓️ Starting schedule retrieval for workflow {workflow_id}", 10.0)

        # Check if we should skip processing
        should_skip, reason = self.should_skip_processing(state)
        if should_skip:
            yield self.create_progress_event(f"⏸️ Skipping schedule retrieval: {reason}", 50.0)
            self.set_workflow_status(state, ProcessingStatus.NEEDS_HUMAN_INPUT.value, paused=True)
            yield self.create_success_event(
                "Schedule retrieval paused - waiting for prerequisite completion",
                data={"schedule_retrieval_skipped": True, "skip_reason": reason}
            )
            return

        try:
            # Step 1: Verify invoice generation completed
            yield self.create_progress_event("Verifying invoice generation completion...", 20.0)
            invoice_generation_result = state.get("invoice_generation_result")
            
            if not invoice_generation_result or not invoice_generation_result.get("generation_successful"):
                error_msg = "Invoice generation must complete successfully before schedule retrieval"
                yield self.create_error_event("Prerequisites not met", error_msg)
                raise ValueError(error_msg)

            # Step 2: Get invoice data for schedule matching
            yield self.create_progress_event("Extracting invoice characteristics for schedule matching...", 30.0)
            current_invoice_data = self.get_latest_invoice_data(state)
            
            if not current_invoice_data:
                error_msg = "No invoice data available for schedule matching"
                yield self.create_error_event("Missing invoice data", error_msg)
                raise ValueError(error_msg)

            # Ensure we have UnifiedInvoiceData
            if isinstance(current_invoice_data, dict):
                unified_invoice = UnifiedInvoiceData(**current_invoice_data)
            else:
                unified_invoice = current_invoice_data

            # Step 3: Create RAG query for schedule retrieval (use contract id if present)
            yield self.create_progress_event("Creating RAG query for schedule matching...", 40.0)
            contract_id = state.get("contract_id") or state.get("contract_uuid") or state.get("contract_id")
            rag_query = self._create_schedule_query(unified_invoice, user_id, contract_name, contract_id=contract_id)

            yield self.create_progress_event(f"Querying Pinecone for schedules: {rag_query[:100]}...", 50.0)

            # Step 4: Query Pinecone for relevant schedules. Prefer using ADK/Gemini to craft the query or filter if available.
            if self._adk_client and hasattr(self._adk_client, "generate"):
                # Placeholder: use Gemini model to expand/filter the query. If ADK not configured, fall back.
                try:
                    # The exact ADK API may vary; use a graceful call structure.
                    gemini_response = await self._maybe_call_gemini(rag_query, user_id)
                    # If Gemini provides a refined query or filter, use it
                    if gemini_response and isinstance(gemini_response, str) and len(gemini_response) > 0:
                        rag_query = gemini_response
                except Exception:
                    # Non-fatal: continue with original rag_query
                    pass

            # Query Pinecone using existing PineconeService
            pinecone_service = get_pinecone_service()
            pinecone_result = pinecone_service.search_similar(
                query_text=rag_query,
                top_k=10,
                filter_metadata={
                    "user_id": user_id,
                    "contract_id": contract_id,
                    "document_type": "contract"
                }
            )

            retrieved_schedules = []
            if pinecone_result.get("success"):
                for match in pinecone_result.get("results", []):
                    md = match.get("metadata", {}) or {}
                    # Attempt to parse schedule metadata stored during ingestion
                    try:
                        schedule = {
                            "schedule_id": md.get("schedule_id") or match.get("id"),
                            "name": md.get("name") or md.get("client_name") or "schedule",
                            "frequency": md.get("frequency") or md.get("freq") or "monthly",
                            "day_of_month": md.get("day_of_month"),
                            "day_of_week": md.get("day_of_week"),
                            "time": md.get("time") or md.get("scheduled_time") or "09:00:00",
                            "timezone": md.get("timezone", "UTC"),
                            "description": md.get("description") or md.get("text"),
                            "metadata": md,
                            "score": match.get("score")
                        }
                    except Exception:
                        schedule = {"schedule_id": match.get("id"), "metadata": md}

                    retrieved_schedules.append(schedule)
            
            # Log the schedules JSON response
            schedules_json = {
                "total_schedules": len(retrieved_schedules),
                "schedules": retrieved_schedules,
                "query_used": rag_query,
                "user_id": user_id,
                "retrieval_timestamp": datetime.now().isoformat()
            }
            self.logger.info("📅 SCHEDULES JSON RESPONSE: %s", json.dumps(schedules_json, indent=2, default=str))
            
            yield self.create_progress_event(f"Found {len(retrieved_schedules)} potential schedules", 60.0)

            # Step 5: Match and rank schedules
            yield self.create_progress_event("Matching schedules to invoice characteristics...", 70.0)
            matched_schedules = self._match_schedules_to_invoice(retrieved_schedules, unified_invoice)
            
            if not matched_schedules:
                yield self.create_progress_event("No matching schedules found - using default schedule", 75.0)
                matched_schedules = [self._create_default_schedule(unified_invoice)]

            # Step 6: Schedule invoices based on matched schedules
            yield self.create_progress_event("Scheduling invoices based on matched schedules...", 80.0)
            scheduled_invoices = []
            
            for schedule in matched_schedules[:3]:  # Limit to top 3 schedules
                scheduled_invoice = await self._schedule_invoice(schedule, current_invoice_data, state, contract_name=contract_name)
                scheduled_invoices.append(scheduled_invoice)
                
            yield self.create_progress_event(f"Scheduled {len(scheduled_invoices)} invoices", 90.0)

            # Step 7: Update workflow state with scheduling information
            # Expand monthly schedules into concrete dates for the next N months
            expansion_months = state.get("schedule_expansion_months", 6)
            expanded_schedule_dates = self._expand_schedules_to_dates(matched_schedules, expansion_months)

            scheduling_result = {
                "total_schedules_retrieved": len(retrieved_schedules),
                "schedules_found": len(retrieved_schedules),
                "schedules_matched": len(matched_schedules),
                "invoices_scheduled": len(scheduled_invoices),
                "scheduled_invoices": scheduled_invoices,
                "retrieved_schedules": retrieved_schedules,
                "matched_schedules": matched_schedules,
                "scheduling_timestamp": datetime.now().isoformat(),
                "rag_query_used": rag_query,
                "scheduling_successful": True,
                "expanded_schedule_dates": expanded_schedule_dates,
                "schedules_json": schedules_json
            }
            
            # Log the final scheduling result JSON
            self.logger.info("🎯 SCHEDULING RESULT JSON: %s", json.dumps(scheduling_result, indent=2, default=str))
            
            # Store agent-specific result
            state["schedule_retrieval_result"] = scheduling_result
            
            # Update centralized data with scheduling info
            final_data = current_invoice_data.copy()
            final_data["scheduling_info"] = scheduling_result
            self.update_invoice_data(state, final_data, "schedule_retrieval_agent")
            
            # Legacy compatibility
            state["scheduling_completed"] = True
            state["scheduled_invoices"] = scheduled_invoices
            
            # Set workflow status
            self.set_workflow_status(state, ProcessingStatus.SUCCESS.value)
            
            yield self.create_progress_event("✅ Schedule retrieval and invoice scheduling completed", 100.0)

            yield self.create_success_event(
                "Schedules retrieved from Pinecone and invoices scheduled successfully",
                data={
                    "total_schedules_retrieved": len(retrieved_schedules),
                    "schedules_found": len(retrieved_schedules),
                    "schedules_matched": len(matched_schedules),
                    "invoices_scheduled": len(scheduled_invoices),
                    "scheduled_invoices_json": scheduled_invoices,
                    "schedules_json": retrieved_schedules,
                    "rag_query": rag_query,
                    "scheduling_successful": True,
                    "workflow_id": workflow_id,
                    "scheduling_result": scheduling_result
                },
                confidence=0.90
            )

        except Exception as e:
            self.logger.error("❌ Schedule retrieval failed: %s", str(e))
            
            self.set_workflow_status(state, ProcessingStatus.FAILED.value)
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append({
                "agent": "schedule_retrieval",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            yield self.create_error_event("Schedule retrieval failed", str(e))
            raise e
    
    def _create_schedule_query(self, unified_invoice: UnifiedInvoiceData, user_id: str, contract_name: str, contract_id: Optional[str] = None) -> str:
        """Create RAG query for schedule retrieval based on invoice characteristics"""
        query_parts = []
        
        # Add payment frequency information
        if unified_invoice.payment_terms and unified_invoice.payment_terms.frequency:
            query_parts.append(f"payment frequency: {unified_invoice.payment_terms.frequency}")
        
        # Add service type information
        if unified_invoice.service_details and unified_invoice.service_details.description:
            query_parts.append(f"service type: {unified_invoice.service_details.description[:100]}")
        
        # Add contract information
        if contract_id:
            query_parts.append(f"contract_id: {contract_id}")
        else:
            query_parts.append(f"contract: {contract_name}")
        query_parts.append(f"user: {user_id}")
        
        # Add payment amount for priority scheduling
        if unified_invoice.payment_terms and unified_invoice.payment_terms.amount:
            query_parts.append(f"amount: {unified_invoice.payment_terms.amount}")
        
        return " | ".join(query_parts)

    

    async def _maybe_call_gemini(self, query: str, user_id: Optional[str]) -> Optional[str]:
        """Attempt to call Gemini via ADK to refine or expand the RAG query. Graceful no-op if ADK unavailable."""
        if not self._adk_client:
            return None

        try:
            # This is a conservative, generic placeholder for calling the Gemini model through ADK.
            # Real usage will depend on the installed google.adk API surface.
            gen = getattr(self._adk_client, "generate", None)
            if gen is None:
                return None

            # Many ADK clients are synchronous; attempt to support both sync and async.
            prompt = f"Refine the following schedule retrieval query for Pinecone RAG. Keep it short and focused. QUERY: {query} USER:{user_id}"
            result = gen(prompt) if callable(gen) else None
            # If result is an object with text, attempt to extract
            if isinstance(result, str):
                return result
            text = getattr(result, "text", None) or getattr(result, "content", None)
            if isinstance(text, str):
                return text
        except Exception:
            return None

        return None
    
    def _match_schedules_to_invoice(self, schedules: List[Dict[str, Any]], unified_invoice: UnifiedInvoiceData) -> List[Dict[str, Any]]:
        """Match and rank schedules based on invoice characteristics"""
        matched_schedules = []
        
        for schedule in schedules:
            score = 0
            
            # Match payment frequency
            invoice_frequency = unified_invoice.payment_terms.frequency if unified_invoice.payment_terms else None
            if invoice_frequency and schedule.get("frequency") == invoice_frequency.lower():
                score += 10
            
            # Match service category
            service_desc = unified_invoice.service_details.description if unified_invoice.service_details else ""
            schedule_category = schedule.get("metadata", {}).get("category", "")
            if schedule_category.lower() in service_desc.lower():
                score += 5
            
            # Prefer high priority schedules
            if schedule.get("metadata", {}).get("priority") == "high":
                score += 3
            
            schedule["match_score"] = score
            if score > 0:
                matched_schedules.append(schedule)
        
        # Sort by match score descending
        matched_schedules.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return matched_schedules
    
    def _create_default_schedule(self, unified_invoice: UnifiedInvoiceData) -> Dict[str, Any]:
        """Create a default schedule when no matches are found"""
        frequency = "monthly"  # Default
        if unified_invoice.payment_terms and unified_invoice.payment_terms.frequency:
            frequency = unified_invoice.payment_terms.frequency.lower()
        
        return {
            "schedule_id": "default_schedule",
            "name": f"Default {frequency.title()} Schedule",
            "frequency": frequency,
            "day_of_month": 1 if frequency == "monthly" else None,
            "day_of_week": 1 if frequency == "weekly" else None,
            "time": "09:00:00",
            "timezone": "UTC",
            "description": f"Default {frequency} invoice schedule",
            "metadata": {
                "category": "default",
                "priority": "medium",
                "auto_send": False
            },
            "match_score": 1
        }

    def _expand_schedules_to_dates(self, schedules: List[Dict[str, Any]], months: int = 6) -> Dict[str, List[str]]:
        """Expand schedules into concrete dates for the next `months` months.

        Returns a mapping of schedule_id -> list of ISO date strings representing the execution date for each month.
        Only monthly schedules are expanded; weekly schedules return the next `months * 4` weekly occurrences.
        """
        result: Dict[str, List[str]] = {}
        now = datetime.now()

        for sched in schedules:
            sid = sched.get("schedule_id", "unknown")
            freq = (sched.get("frequency") or "monthly").lower()
            dates: List[str] = []

            if freq == "monthly":
                day = sched.get("day_of_month") or 1
                # For the next `months` months, compute the date with day clamp
                current = now
                for i in range(months):
                    year = current.year + ((current.month - 1 + i) // 12)
                    month = ((current.month - 1 + i) % 12) + 1
                    # clamp day to last day of month if necessary
                    try:
                        dt = datetime(year=year, month=month, day=day, hour=9, minute=0, second=0)
                    except Exception:
                        # day too large for month -> choose last day of month
                        next_month = datetime(year=year, month=month, day=1) + timedelta(days=31)
                        last_day = (next_month.replace(day=1) - timedelta(days=1)).day
                        dt = datetime(year=year, month=month, day=last_day, hour=9, minute=0, second=0)
                    dates.append(dt.isoformat())

            elif freq == "weekly":
                # Expand next months * 4 weeks
                target_weekday = sched.get("day_of_week", 0)
                count = months * 4
                current = now
                added = 0
                while added < count:
                    days_ahead = (target_weekday - current.weekday() + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    current = current + timedelta(days=days_ahead)
                    dates.append(current.isoformat())
                    added += 1

            else:
                # Default: next `months` daily occurrences once per month interval
                for i in range(months):
                    dt = now + timedelta(days=30 * i)
                    dates.append(dt.isoformat())

            result[sid] = dates

        return result
    
    async def _schedule_invoice(self, schedule: Dict[str, Any], invoice_data: Dict[str, Any], state: Dict[str, Any], contract_name: Optional[str] = None) -> Dict[str, Any]:
        """Schedule an invoice based on the schedule configuration"""
        try:
            # Create scheduling configuration
            schedule_config = {
                "schedule_id": schedule["schedule_id"],
                "name": schedule["name"],
                "frequency": schedule["frequency"],
                "day_of_month": schedule.get("day_of_month"),
                "day_of_week": schedule.get("day_of_week"),
                "time": schedule.get("time", "09:00:00"),
                "timezone": schedule.get("timezone", "UTC"),
                "auto_send": schedule.get("metadata", {}).get("auto_send", False),
                "match_score": schedule.get("match_score", 0)
            }
            
            # Create invoice scheduling payload
            invoice_payload = {
                "workflow_id": state.get("workflow_id"),
                "user_id": state.get("user_id"),
                "contract_name": state.get("contract_name"),
                "invoice_data": invoice_data,
                "invoice_uuid": state.get("invoice_generation_result", {}).get("invoice_uuid"),
                "invoice_number": state.get("invoice_generation_result", {}).get("invoice_number")
            }
            
            # Use Cloud Scheduler to create recurring or one-off jobs
            cloud = self._cloud_scheduler_service

            # Parse time
            time_parts = schedule_config.get("time", "09:00:00").split(":")
            hour = int(time_parts[0]) if len(time_parts) > 0 else 9
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            client_name = contract_name or state.get("contract_name") or invoice_payload.get("contract_name") or "client"

            if schedule_config.get("frequency") == "monthly":
                # Compute the next occurrence based on day_of_month
                day_of_month = int(schedule_config.get("day_of_month") or 1)
                now_dt = datetime.now()
                # try this month
                try:
                    candidate = now_dt.replace(day=day_of_month, hour=hour, minute=minute, second=0)
                except Exception:
                    # clamp to last day of month
                    next_month = (now_dt.replace(day=1) + timedelta(days=32)).replace(day=1)
                    last_day = (next_month - timedelta(days=1)).day
                    candidate = now_dt.replace(day=last_day, hour=hour, minute=minute, second=0)

                if candidate <= now_dt:
                    # move to next month
                    month = now_dt.month + 1 if now_dt.month < 12 else 1
                    year = now_dt.year if now_dt.month < 12 else now_dt.year + 1
                    try:
                        candidate = candidate.replace(year=year, month=month, day=day_of_month)
                    except Exception:
                        # clamp
                        next_month = datetime(year=year, month=month, day=1) + timedelta(days=31)
                        last_day = (next_month.replace(day=1) - timedelta(days=1)).day
                        candidate = datetime(year=year, month=month, day=last_day, hour=hour, minute=minute, second=0)

                start_date = candidate.date().isoformat()
                # create recurring schedule
                job_res = cloud.create_recurring_invoice_schedule(
                    client_name=client_name,
                    frequency="monthly",
                    start_date=start_date,
                    hour=hour,
                    minute=minute
                )
                self.logger.info("✅ Created recurring monthly schedule")
                scheduled_result = {"scheduled_invoice_id": job_res.get("job_name"), "job_result": job_res}
                return scheduled_result

            elif schedule_config.get("frequency") == "weekly":
                # Use start_date as next weekday occurrence
                day_of_week = schedule_config.get("day_of_week", 0)
                next_dt = datetime.now()
                days_ahead = (int(day_of_week) - next_dt.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                start_date = (next_dt + timedelta(days=days_ahead)).date().isoformat()
                job_res = cloud.create_recurring_invoice_schedule(
                    client_name=client_name,
                    frequency="weekly",
                    start_date=start_date,
                    hour=hour,
                    minute=minute
                )
                scheduled_result = {"scheduled_invoice_id": job_res.get("job_name"), "job_result": job_res}
                return scheduled_result

            else:
                # One-off or unsupported frequency: create a single job for the next occurrence
                # Use first expanded date if available in state
                target_date = None
                expanded = state.get("schedule_retrieval_result", {}).get("expanded_schedule_dates", {})
                sid = schedule.get("schedule_id")
                if expanded and sid in expanded and len(expanded[sid]) > 0:
                    target_date = expanded[sid][0][:10]
                else:
                    target_date = datetime.now().date().isoformat()

                # Build cron for that day and time (runs monthly on that day; acceptable as fallback)
                dt = datetime.fromisoformat(f"{target_date}T{schedule_config.get('time', '09:00:00')}")
                cron_expr = f"{dt.minute} {dt.hour} {dt.day} {dt.month} *"
                job_name = f"invoice-{client_name}-{schedule_config.get('schedule_id')}-{int(datetime.now().timestamp())}"
                job_res = cloud.create_invoice_schedule_job(
                    job_name=job_name,
                    schedule=cron_expr,
                    target_date=target_date,
                    description=f"One-off invoice for {client_name} on {target_date}"
                )

                scheduled_result = {"scheduled_invoice_id": job_res.get("job_name"), "job_result": job_res}
                return scheduled_result
            
        except Exception as e:
            self.logger.error("❌ Failed to schedule invoice for schedule %s: %s", schedule.get('schedule_id'), str(e))
            raise e