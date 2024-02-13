# Immortus

_Events from the past, executed in the future_

![A picture of Immortus from Marvel Comics Universe](assets/immortus.jpg)

A Helm Chart to deploy and manage
[celery workers](https://docs.celeryq.dev/en/stable/userguide/workers.html),
[celery beat](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), and the
[flower](https://flower.readthedocs.io/en/latest/index.html) dashboard on
[GKE](https://cloud.google.com/kubernetes-engine).

# TODO: UPDATE THIS README AS THERE HAVE BEEN TOO MANY CHANGES!

## Container Setup

The helm chart requires the container's entrypoint to consume certain arguments that are
passed using `CMD` based on which component is executed. Additionally, some environment variables
are injected that can be consumed as required.

### Commands

- **Web Server:** `-m server`
- **Celery Worker:** `-m worker [-q <queue>]`
- **Celery Beat Scheduler:** `-m beat`
- **Flower Dashboard:** `-m flower`
- **Event Consumer:** `-m events`

### Environment Variables

- CH_CELERY_BROKER_URI
- CH_CELERY_BACKEND_URI
- CH_EVENTS_RMQ_URI
- CH_FLOWER_USER
- CH_FLOWER_PASSWORD

## Management & Configuration

The [values.yaml](celery-helm/values.yaml) file is used to configure all the components.
Check the file to understand configuration.

## Installation

### Create a GKE Cluster

If the GKE cluster hasn't been created yet, set it up. This can be done via the cloud console, or
using the command line:

```bash
# TODO: Add commands
```

### Create Secrets

The Helm Chart requires a `secretKeyRef`, and expects the following keys to be
available in the secret:

- **ch_flower_user**: Flower basic auth user
- **ch_flower_password**: Flower basic auth password
- **ch_celery_broker_uri**: Celery Broker URI
- **ch_celery_backend_uri**: Celery Backend URI
- **ch_events_rmq_uri**: Events consumer RMQ URI

### Install the Helm Chart

First configure `kubectl` to use the deployed cluster. Next, install with:

```bash
helm install <helm-name> celery-helm
```

## Upgrades

If there is any change to the `values.yaml` file, the same can be propogated to the cluster
using the upgrade command:

```bash
helm upgrade <helm-name> celery-helm
```

For example, to increase the number of workers for particular queue, increment the
`.Values.worker.queues[].replicas` for that queue. To delete all workers of a particular
queue, remove the entry from the `.Values.worker.queues[]` list.
