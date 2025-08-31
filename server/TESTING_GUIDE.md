# Orchestrator Agent Testing Guide with LangSmith Integration

This guide explains how to test your agentic orchestrator pipeline using LangSmith monitoring and mock LLM implementations.

## 🎯 Overview

The testing system includes:
- **LangSmith Integration**: Full workflow tracing and monitoring
- **Mock LLM**: No API calls needed, fast testing
- **Orchestrator Evals**: Comprehensive evaluation test cases
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Speed and memory usage testing

## 🚀 Quick Start

### 1. Setup Environment Variables (Optional for LangSmith)

```bash
# For LangSmith tracing (optional)
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_langsmith_api_key
export LANGCHAIN_PROJECT=smart-invoice-orchestrator
```

### 2. Run Tests

```bash
# Quick smoke tests (fastest)
python tests/run_tests.py quick

# Orchestrator evaluations only
python tests/run_tests.py eval

# Unit tests with mocks
python tests/run_tests.py unit

# Full pipeline with LangSmith (comprehensive)
python tests/run_tests.py pipeline

# Enable LangSmith tracing
python tests/run_tests.py pipeline --langsmith
```

## 📊 Test Types Explained

### 1. **Quick Tests** (`quick`)
- **Duration**: 5-10 seconds
- **Purpose**: Smoke tests to verify basic functionality
- **What it tests**: Imports, instance creation, basic orchestrator decisions
- **Use when**: Quick development feedback, CI/CD checks

### 2. **Orchestrator Evaluations** (`eval`)
- **Duration**: 30-60 seconds  
- **Purpose**: LangSmith evaluation test cases for orchestrator logic
- **What it tests**: 
  - Decision making accuracy
  - Routing logic correctness
  - Error handling scenarios
  - Quality-based routing
  - Retry mechanisms
- **Use when**: Testing orchestrator intelligence and decision making

### 3. **Unit Tests** (`unit`)
- **Duration**: 1-2 minutes
- **Purpose**: Traditional unit tests with mocked dependencies
- **What it tests**:
  - Individual agent behavior
  - Error handling
  - State management
  - Mock LLM integration
- **Use when**: Testing individual components in isolation

### 4. **Full Pipeline** (`pipeline`)
- **Duration**: 3-5 minutes
- **Purpose**: Complete end-to-end testing with LangSmith tracing
- **What it tests**:
  - All test types above
  - Integration between components
  - Performance metrics
  - Full workflow execution
  - LangSmith trace generation
- **Use when**: Pre-production validation, comprehensive testing

## 🔍 Understanding Test Results

### Orchestrator Evaluation Results

```json
{
  "orchestrator_evaluation": {
    "total_tests": 10,
    "passed": 9,
    "failed": 1,
    "overall_score": 0.9
  },
  "routing_function_tests": {
    "total": 5,
    "passed": 5,
    "failed": 0
  },
  "overall_success": true
}
```

**Success Criteria**:
- Overall score > 0.8 (80% of tests pass)
- All routing function tests pass
- No critical decision-making errors

### Unit Test Results

```
test_orchestrator_decision_making (__main__.TestOrchestratorWithMocks) ... ok
test_orchestrator_error_handling (__main__.TestOrchestratorWithMocks) ... ok
test_orchestrator_max_attempts_logic (__main__.TestOrchestratorWithMocks) ... ok
test_orchestrator_quality_based_routing (__main__.TestOrchestratorWithMocks) ... ok

Ran 4 tests in 1.234s
OK
```

## 🎛️ LangSmith Integration

### What LangSmith Shows

1. **Workflow Traces**: Complete execution paths through agents
2. **Agent Timing**: Performance metrics for each agent
3. **Decision Points**: Orchestrator routing decisions with reasoning
4. **Error Patterns**: Common failure points and recovery paths
5. **Quality Metrics**: Confidence scores and quality assessments

### LangSmith Dashboard Views

- **Traces Tab**: Individual workflow executions
- **Datasets Tab**: Test case collections
- **Experiments Tab**: Comparison of different agent versions
- **Analytics Tab**: Aggregate performance metrics

### Example Trace Structure

```
🔀 Orchestrator (Decision: route to contract_processing)
├── 📄 Contract Processing (Status: success, Confidence: 0.8)
├── 🔀 Orchestrator (Decision: route to validation)  
├── ✅ Validation (Status: passed, Score: 0.85)
├── 🔀 Orchestrator (Decision: route to schedule_extraction)
├── 📅 Schedule Extraction (Status: success)
├── 🔀 Orchestrator (Decision: route to invoice_generation)
├── 📄 Invoice Generation (Status: success, Quality: 0.9)
├── 🔀 Orchestrator (Decision: route to quality_assurance)
├── 🔍 Quality Assurance (Status: passed, Score: 0.92)
├── 🔀 Orchestrator (Decision: route to storage_scheduling)
├── 💾 Storage & Scheduling (Status: success)
└── ✅ Workflow Complete
```

## 🧪 Mock LLM System

### Mock LLM Features

- **No API Calls**: 100% local testing, no external dependencies
- **Configurable Responses**: Pattern-based response matching  
- **Failure Simulation**: Test error handling with controlled failures
- **Call Tracking**: Monitor LLM usage and debug issues
- **Performance**: Very fast execution for rapid testing

### Mock Response Patterns

The mock LLM provides realistic responses for different scenarios:

```python
# Contract processing responses
"rental_agreement" -> "Monthly rent: $1200, Tenant: John Doe..."

# Orchestrator decisions  
"validation_passed" -> {"next_action": "schedule_extraction", "confidence": 0.8}

# Invoice generation
"rental" -> {"contract_type": "rental_lease", "amount": 1200, ...}
```

### Creating Custom Mock Responses

```python
from tests.mock_llm import MockLLMFactory

custom_patterns = {
    "my_pattern": {
        "custom_input": "custom_response"
    }
}

mock_llm = MockLLMFactory.create_custom_llm(custom_patterns)
```

## 📈 Performance Testing

### Metrics Tracked

- **Execution Time**: How fast agents make decisions
- **Memory Usage**: Memory consumption during processing
- **Call Frequency**: Number of LLM calls per workflow
- **Success Rate**: Percentage of successful completions

### Performance Targets

- Orchestrator decision: < 10ms with mocked LLM
- Full workflow: < 5 seconds with all mocks
- Memory growth: < 1000 objects per 1000 workflows

## 🐛 Debugging Failed Tests

### Common Issues and Solutions

1. **Import Errors**
   ```bash
   # Fix: Ensure server directory is in Python path
   export PYTHONPATH="/path/to/smart-invoice-scheduler/server:$PYTHONPATH"
   ```

2. **Mock LLM Failures**
   ```python
   # Check mock patterns match your input
   mock_llm.get_call_history()  # See what inputs were received
   ```

3. **Orchestrator Decision Errors**
   ```python
   # Check state has required fields
   assert "workflow_id" in state
   assert "processing_status" in state
   ```

4. **LangSmith Connection Issues**
   ```bash
   # Verify environment variables
   echo $LANGCHAIN_TRACING_V2
   echo $LANGCHAIN_API_KEY
   ```

### Test Debug Mode

```bash
# Run with verbose output
python tests/run_tests.py eval --verbose

# Run specific test case
python -m unittest tests.test_orchestrator_with_mocks.TestOrchestratorWithMocks.test_orchestrator_decision_making -v
```

## 📋 Test Development Guidelines

### Adding New Test Cases

1. **Orchestrator Evaluations**: Add to `tests/orchestrator_evals.py`
2. **Unit Tests**: Add to `tests/test_orchestrator_with_mocks.py`  
3. **Integration Tests**: Add to `tests/test_pipeline.py`

### Test Case Structure

```python
{
    "name": "test_case_name",
    "description": "What this test validates",
    "input_state": {...},  # Input state for agent
    "expected_decision": {...},  # Expected orchestrator decision
    "success_criteria": {...}  # How to evaluate success
}
```

### Mock Pattern Guidelines

```python
# Good: Specific, realistic patterns
"rental_agreement_monthly" -> realistic_rental_response

# Bad: Generic, unrealistic patterns  
"any_input" -> "generic_response"
```

## 🚀 CI/CD Integration

### Basic CI/CD Pipeline

```yaml
# .github/workflows/test.yml
- name: Run Quick Tests
  run: python tests/run_tests.py quick

- name: Run Unit Tests  
  run: python tests/run_tests.py unit

- name: Run Evaluations
  run: python tests/run_tests.py eval
```

### With LangSmith Integration

```yaml
- name: Run Full Pipeline
  env:
    LANGCHAIN_TRACING_V2: true
    LANGCHAIN_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
  run: python tests/run_tests.py pipeline --langsmith
```

## 📊 Monitoring and Alerts

### Success Thresholds

- **Orchestrator Evaluations**: > 80% success rate
- **Unit Tests**: 100% pass rate
- **Performance**: < 10s total pipeline time
- **Quality**: Average confidence > 0.7

### LangSmith Monitoring

1. Set up LangSmith project: `smart-invoice-orchestrator`
2. Create dashboards for key metrics
3. Set alerts for performance degradation
4. Monitor error patterns over time

## 🎯 Next Steps

1. **Run Quick Tests**: Verify basic functionality
2. **Add LangSmith API Key**: Enable full tracing  
3. **Run Full Pipeline**: Get comprehensive results
4. **Review LangSmith Traces**: Understand agent behavior
5. **Customize Test Cases**: Add your specific scenarios
6. **Set up CI/CD**: Automate testing in your pipeline

## 📚 Additional Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Testing Best Practices](https://docs.python.org/3/library/unittest.html)

---

Happy Testing! 🧪✨