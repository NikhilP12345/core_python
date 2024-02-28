
print("Sdg")
include = [
    'celery_module.tasks'
] 
# 'celery_analytics.modules.ifsc_cache.ifsc_cache',
result_expires = 3600
timezone = 'UTC'
task_acks_late = True
task_reject_on_worker_lost = True
task_routes = {
    'celery_module.tasks.*': {'queue': 'celery'},
}
