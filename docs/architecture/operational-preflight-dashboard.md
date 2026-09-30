# Operational Preflight Dashboard

Phase 31 makes one existing backend operation available from the Models page:

```text
Models dashboard -> local control token -> one preflight API call -> persisted results
```

The endpoint invokes the same `PaperWorkerService.run_once` used by the CLI. It has no
worker loop and no imports from model artifacts, strategy, risk, execution, or broker code.
The UI refreshes dashboard data after the call so it displays the persisted preflight rather
than synthetic status.
