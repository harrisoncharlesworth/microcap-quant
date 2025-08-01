# Subagents Plan: Fix Automated Trading Scheduler Issues

## Context
The automated trading system has several critical issues that prevent reliable cron scheduling:
- Timezone mismatch (container in UTC vs US/Eastern)
- Long-running jobs blocking the scheduler loop
- No crash protection for the main loop
- Inconsistent key access patterns for position data
- No health monitoring/heartbeat

## Plan Overview
Fix 5 critical issues identified by Oracle to ensure reliable scheduled task execution.

## Task 1: Fix Timezone Configuration (HIGH PRIORITY)
**Agent**: timezone_agent
**Files**: Dockerfile, auto_trader/automated_trader.py, auto_trader/config.py
**Tasks**:
- Add timezone environment variable to Dockerfile (ENV TZ=America/New_York)
- Implement proper timezone handling in scheduler setup
- Convert ET times to UTC dynamically or ensure container uses correct timezone
- Test timezone calculation is correct

## Task 2: Add Threading for Non-Blocking Execution (HIGH PRIORITY)
**Agent**: threading_agent  
**Files**: auto_trader/automated_trader.py
**Tasks**:
- Add ThreadPoolExecutor import and setup
- Modify scheduler calls to use thread pool for long-running tasks
- Ensure run_daily_cycle, run_opening_cycle, run_intraday_news_check run in separate threads
- Add proper error handling for threaded execution

## Task 3: Add Crash Protection and Health Monitoring (MEDIUM PRIORITY)
**Agent**: monitoring_agent
**Files**: auto_trader/automated_trader.py
**Tasks**:
- Wrap main scheduler loop in try/except
- Add heartbeat logging every minute
- Add health check logging for scheduled jobs
- Log next run times for all scheduled jobs
- Ensure system continues running after individual job failures

## Task 4: Fix Position Data Key Access Issues (HIGH PRIORITY)
**Agent**: data_consistency_agent
**Files**: auto_trader/ai_decision_engine.py, auto_trader/broker_interface.py, auto_trader/automated_trader.py
**Tasks**:
- Fix 'buy_price' KeyError in intraday news check function
- Fix AI decision engine counting bug (shows 0 decisions when decisions exist)
- Update ai_decision_engine._format_portfolio to handle avg_entry_price
- Fix broker_interface.check_stop_losses to handle missing stop_loss values
- Ensure consistent key access patterns across all position data handling
- Add fallback values for missing keys

## Task 5: Add Docker Health Check (LOW PRIORITY)
**Agent**: docker_agent
**Files**: Dockerfile
**Tasks**:
- Add HEALTHCHECK directive to Dockerfile
- Create simple health check script or endpoint
- Ensure health check verifies scheduler is running properly

## Execution Order
1. Tasks 1 & 2 in parallel (both HIGH priority, different files)
2. Tasks 3 & 4 in parallel (both MEDIUM priority, can work independently)  
3. Task 5 after others complete (depends on Dockerfile changes)

## Success Criteria
- Scheduler runs at correct US/Eastern times
- Long-running jobs don't block subsequent scheduled tasks
- System recovers from individual job failures
- No more KeyError exceptions for position data
- Health monitoring provides visibility into system status
