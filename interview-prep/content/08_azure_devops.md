# Azure Cloud

## Which Azure compute options would you choose for Java microservices?
- **Azure Kubernetes Service (AKS)**: full Kubernetes control. Best for many microservices, complex networking, service meshes and portability. You manage upgrades, node pools and add-ons.
- **Azure Container Apps**: serverless containers built on Kubernetes, **KEDA** and **Dapr**. Scales to zero with no cluster to manage. A great default for most microservice workloads.
- **Azure App Service**: PaaS for web apps (Java SE, Tomcat, JBoss). Deployment slots, simple autoscale.
- **Azure Functions**: event-driven serverless (HTTP, timers, Service Bus, Event Hubs triggers). **Durable Functions** handle orchestration.
- **Azure Spring Apps** was retired (announced 2024). Point to Container Apps or AKS as the migration path.
- **VMs / VM Scale Sets**: for lift-and-shift or special needs.

## How do you manage secrets and identity in Azure?
- **Azure Key Vault**: secrets, keys and certificates, with rotation, access policies or RBAC, and soft-delete with purge protection.
- **Managed Identity** (system- or user-assigned): the app authenticates to Key Vault, SQL, Storage, Service Bus and more **without any credentials in code or config**, using `DefaultAzureCredential`.
- **AKS**: **Workload Identity** (federated with Entra ID) and the Secrets Store CSI driver to mount secrets from Key Vault.
- **Microsoft Entra ID (Azure AD)**: OAuth2 / OpenID Connect for users and apps, app registrations, app roles and scopes.
```
// Spring Cloud Azure: Key Vault secrets become Spring properties
spring.cloud.azure.keyvault.secret.property-sources[0].endpoint=https://my-kv.vault.azure.net/
// Auth uses Managed Identity through DefaultAzureCredential, so no secret is stored anywhere
```

## Azure Service Bus vs Event Hubs vs Event Grid vs Storage Queues?
- **Service Bus**: enterprise messaging (commands and orders). FIFO sessions, DLQ, duplicate detection, transactions, topics with filtered subscriptions.
- **Event Hubs**: high-volume **event streaming** (millions of events per second), partitions, replay, Kafka endpoint, Capture to a data lake.
- **Event Grid**: **reactive event routing** with push delivery (e.g. "a blob was created", resource events, custom events). Lightweight notifications.
- **Storage Queues**: simple, cheap and very large queues with basic features.

## How do you choose a database on Azure?
- **Azure SQL / SQL Managed Instance**: relational, with high-availability options, geo-replication and serverless tiers.
- **Azure Database for PostgreSQL / MySQL (Flexible Server)**: managed open-source databases.
- **Cosmos DB**: globally distributed, multi-model NoSQL with single-digit-millisecond latency. **Partition key** choice is critical. Throughput is measured in RU/s. Offers five consistency levels. **Change Feed** drives event-driven projections.
- **Azure Cache for Redis**: caching, sessions, rate limiting.
- **Blob Storage / Data Lake Gen2**: objects, files and analytics.

## What is Azure API Management and where does it fit?
A full API gateway: **policies** (JWT validation, rate limit by key, quotas, caching, transformation, CORS), a developer portal, API versions and revisions, analytics, subscription keys and a self-hosted gateway. It usually sits in front of AKS or Container Apps, behind **Front Door** (global load balancing, WAF and CDN) or an **Application Gateway** (regional L7 load balancer + WAF).

## How do you monitor Java apps on Azure?
- **Azure Monitor + Application Insights**: the **Java agent** (codeless auto-instrumentation built on OpenTelemetry) collects requests, dependencies, exceptions, traces and live metrics, and draws an **application map**.
- **Log Analytics workspace**: query with **KQL**. Container Insights for AKS.
- Alerts, action groups, Workbooks, and **Azure Managed Grafana / Managed Prometheus**.
```
// KQL: p95 latency per operation over the last hour
requests
| where timestamp > ago(1h)
| summarize p95 = percentile(duration, 95), failures = countif(success == false) by name
| order by p95 desc
```

## How do you design a secure network in Azure?
- A hub-and-spoke **VNet** topology with **Azure Firewall** in the hub.
- **Private Endpoints** for PaaS services (SQL, Key Vault, Storage), with public access disabled.
- **NSGs** and Kubernetes network policies, **WAF** on Front Door or App Gateway, and **DDoS Protection**.
- Least-privilege **RBAC**, **Azure Policy** for governance, and **Defender for Cloud** for posture management.

## How do you autoscale on Azure?
- **AKS**: **HPA** (pods, by CPU, memory or custom metrics), the **Cluster Autoscaler** (nodes), and **KEDA** (event-driven: Service Bus queue length, Kafka lag, Event Hubs). Node Auto-Provisioning (Karpenter-based) is also available.
- **Container Apps**: built-in KEDA scale rules, including scale to zero.
- **App Service**: autoscale rules on metrics or schedules.
- **Cosmos DB**: autoscale RU/s. **Azure SQL**: serverless or elastic pools.

# DevOps, CI/CD, Docker & Kubernetes

## Describe a CI/CD pipeline you have built for Java microservices.
**CI (on every pull request and merge)**:
1. Checkout -> build with Maven or Gradle (cache dependencies).
2. Unit tests + integration tests (Testcontainers), with a JaCoCo coverage gate.
3. Static analysis: **SonarQube** quality gate, Checkstyle, SpotBugs.
4. Security: **SCA** (OWASP Dependency-Check, Snyk, Dependabot), **SAST** (CodeQL), secrets scanning.
5. Build the Docker image (Jib, Buildpacks or a multi-stage Dockerfile), **scan the image** (Trivy, Defender for Containers), and push it to **Azure Container Registry** tagged with the git SHA.

**CD**:
6. Deploy to dev, then test, then prod with Helm charts or Kustomize (or GitOps with **Argo CD / Flux**).
7. Smoke tests, contract tests and performance tests (JMeter, Gatling, k6) at the right stages.
8. **Approval gates** for production, **progressive delivery** (canary or blue-green), automatic rollback when health or metrics degrade.
- Tools: **Azure DevOps Pipelines** (YAML multi-stage, environments, service connections with workload identity federation) or **GitHub Actions** (OIDC to Azure, no stored secrets).
```
# Azure DevOps (simplified)
stages:
- stage: Build
  jobs:
  - job: build
    steps:
    - task: Maven@4
      inputs: { goals: 'verify', options: '-B' }
    - task: Docker@2
      inputs: { command: buildAndPush, repository: orders-svc,
                containerRegistry: acr-conn, tags: '$(Build.SourceVersion)' }
- stage: DeployProd
  dependsOn: Build
  jobs:
  - deployment: prod
    environment: prod        # approvals and checks are configured on the environment
    strategy:
      runOnce:
        deploy:
          steps:
          - script: helm upgrade --install orders ./chart --set image.tag=$(Build.SourceVersion)
```

## How do you write a production-grade Dockerfile for a Spring Boot app?
- **Multi-stage build**: build in a JDK image, run in a slim **JRE** image (e.g. Eclipse Temurin JRE or a distroless image).
- **Layered jar**: dependencies change less often than code, so layer caching makes rebuilds fast.
- Run as a **non-root user**, pin base image versions, add `.dockerignore`, and put no secrets in the image.
- Use container-aware JVM flags such as `-XX:MaxRAMPercentage=75`, and handle SIGTERM for graceful shutdown (`server.shutdown=graceful`).
```
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY . .
RUN ./mvnw -B -DskipTests package && \
    java -Djarmode=tools -jar target/app.jar extract --layers --launcher --destination extracted

FROM eclipse-temurin:21-jre
RUN useradd -r -u 1001 appuser
WORKDIR /app
COPY --from=build /app/extracted/dependencies/ ./
COPY --from=build /app/extracted/spring-boot-loader/ ./
COPY --from=build /app/extracted/snapshot-dependencies/ ./
COPY --from=build /app/extracted/application/ ./
USER 1001
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "org.springframework.boot.loader.launch.JarLauncher"]
```

## Explain core Kubernetes objects.
- **Pod**: the smallest deployable unit, one or more containers. **Deployment**: declarative replica sets and rolling updates. **StatefulSet**: stable identities and storage (databases, Kafka). **DaemonSet**: one pod per node (log agents).
- **Service** (ClusterIP, NodePort, LoadBalancer): a stable virtual IP and DNS name. **Ingress** / **Gateway API**: L7 routing into the cluster.
- **ConfigMap** / **Secret**: configuration. **HPA**: autoscaling. **PodDisruptionBudget**: keeps a minimum number of pods available during node maintenance.
- **Resource requests and limits**: requests drive scheduling, limits cap usage. Exceeding the memory limit gets the pod **OOMKilled**, and CPU above the limit is throttled.
- **Namespaces**, **RBAC**, **NetworkPolicy**.

## Explain liveness, readiness and startup probes.
- **Liveness**: "Is the app stuck?" If it fails, **the container is restarted**. Do not include downstream dependencies (DB) here, or a DB outage will restart every pod.
- **Readiness**: "Can the app take traffic?" If it fails, **the pod is removed from the Service endpoints** but not restarted. Check critical dependencies here.
- **Startup**: gives slow-starting JVM apps time to boot before liveness checks begin.
- Spring Boot Actuator exposes `/actuator/health/liveness` and `/actuator/health/readiness`.

## Deployment strategies: rolling, blue-green, canary?
- **Rolling update**: replace pods gradually (`maxSurge`, `maxUnavailable`). This is the Kubernetes default. Old and new versions run side by side, so changes must be backward compatible.
- **Blue-green**: two full environments; switch traffic all at once. Rollback is instant, but it costs double the resources. App Service **deployment slots** work this way.
- **Canary**: send a small percentage of traffic (5% -> 25% -> 100%) to the new version while watching metrics, and roll back automatically on errors. Tools: Argo Rollouts, Flagger, a service mesh.
- **Feature flags** (Azure App Configuration, LaunchDarkly) **separate deploying code from releasing features**.
- **DB migrations** (Flyway / Liquibase) must be backward compatible: **expand -> migrate -> contract**.

## What is Infrastructure as Code? Terraform vs Bicep?
Infrastructure is defined in version-controlled code: reviewed, repeatable and testable.
- **Terraform**: multi-cloud with the HCL language, a **state file** (store it remotely in an Azure Storage backend with locking), plan/apply, and modules.
- **Bicep**: Azure-native DSL that compiles to ARM templates. No state file to manage, and new Azure features are available on day zero.
- Best practices: modules, separate environments (workspaces or directories), `plan` output shown on the PR, drift detection, and policy as code (Azure Policy, OPA, Checkov).

## What is GitOps?
Git is the **single source of truth** for the desired state of the cluster. An operator (**Argo CD** or **Flux**, and Flux is built into AKS as an extension) pulls from git and reconciles the cluster continuously.
- Benefits: an audit trail, easy rollback (git revert), drift correction, and no cluster credentials in CI.

## What DevOps metrics do you track? (DORA)
- **Deployment frequency**, **lead time for changes**, **change failure rate**, **time to restore service (MTTR)**.
- Plus SLOs and error budgets (SRE practice): if the error budget is exhausted, pause feature releases and focus on reliability.

## A pod is in CrashLoopBackOff. How do you debug it?
1. `kubectl describe pod <p>`: look at the events, exit codes (137 = OOMKilled, 1 = application error), image pull errors and probe failures.
2. `kubectl logs <p> --previous`: the logs from the crashed container.
3. Check config and secrets (missing environment variables, a wrong Key Vault reference), resource limits (the JVM heap is bigger than the memory limit), and a liveness probe that fires too early (add a startup probe).
4. `kubectl exec` or `kubectl debug` (ephemeral containers) to look inside, and `kubectl get events --sort-by=.lastTimestamp`.
