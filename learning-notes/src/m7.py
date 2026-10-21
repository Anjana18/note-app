MODULE = {
    "title": "Containerization & Kubernetes",
    "intro": "\"Works on my machine\" ends here. Docker packages your service with everything it needs; "
             "Kubernetes runs many copies, restarts them when they fail, and routes traffic only to healthy "
             "ones, *if* you configure it correctly.",
    "topics": [
        # ------------------------------------------------------------------ 7.1
        {
            "title": "Docker & Multi-Stage Builds",
            "blocks": [
                ("analogy", "A Docker image is a **shipping container**: whatever is inside (your JAR, the JRE, "
                            "config), every ship and port handles it the same way. A **multi-stage build** is "
                            "like building furniture in a **workshop**, then shipping only the finished table, "
                            "not the saws and sawdust."),
                ("code", """
# syntax=docker/dockerfile:1
# ---------- Stage 1: build (JDK + Maven, ~500 MB, thrown away) ----------
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN ./mvnw dependency:go-offline -B           # cached layer: only reruns when pom.xml changes
COPY src/ src/
RUN ./mvnw package -DskipTests -B \\
 && java -Djarmode=tools -jar target/*.jar extract --layers --launcher --destination extracted

# ---------- Stage 2: runtime (JRE only, ~200 MB) ----------
FROM eclipse-temurin:21-jre
WORKDIR /app
RUN groupadd --system spring && useradd --system --gid spring spring
USER spring                                     # never run as root
COPY --from=build /app/extracted/dependencies/ ./
COPY --from=build /app/extracted/spring-boot-loader/ ./
COPY --from=build /app/extracted/snapshot-dependencies/ ./
COPY --from=build /app/extracted/application/ ./   # changes most often → last layer
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "org.springframework.boot.loader.launch.JarLauncher"]
"""),
                ("h", "Why the layers matter"),
                ("code", """
 Layer                      Changes when…           Size
 dependencies               you change pom.xml      ~80 MB   ← cached across most builds
 spring-boot-loader         Boot version upgrade    <1 MB
 snapshot-dependencies      SNAPSHOT deps change    small
 application                every code change       ~200 KB  ← only this is rebuilt & pushed
"""),
                ("code", """
# .dockerignore: keep the build context small and secrets out
target/
.git/
*.log
.env
"""),
                ("p", "`-XX:MaxRAMPercentage=75.0` makes the JVM size its heap from the **container's** memory "
                      "limit, leaving room for metaspace, threads and native memory. Alternative: Spring Boot's "
                      "`./mvnw spring-boot:build-image` builds an optimised image with Buildpacks, no Dockerfile needed."),
                ("warn", "Setting `-Xmx` equal to the container memory limit (e.g. both 1 GB). The JVM uses "
                         "memory *beyond* the heap (metaspace, thread stacks, direct buffers), so the container "
                         "exceeds its limit and the kernel kills it: **OOMKilled, exit code 137**, with no Java "
                         "stack trace."),
                ("key", ["Multi-stage: build with JDK, run with JRE, so the image is small and safer.",
                         "Order layers from least to most frequently changing.",
                         "Non-root user; size the heap with `MaxRAMPercentage`, not a hard-coded `-Xmx`."]),
            ],
            "questions": [
                "Why do we `COPY pom.xml` and download dependencies *before* `COPY src/`? What happens to "
                "build time if you reverse the order?",
            ],
            "answer": "Docker caches each layer and reuses it while its inputs are unchanged. Copying only "
                      "`pom.xml` first means the slow dependency download is cached until the pom changes. If "
                      "you copy `src/` first, every code change invalidates that layer and all dependencies are "
                      "downloaded again on **every** build (minutes instead of seconds).",
        },
        # ------------------------------------------------------------------ 7.2
        {
            "title": "Kubernetes Core Objects: Pod, Deployment, Service, ConfigMap, Secret",
            "blocks": [
                ("analogy", "Kubernetes is a **restaurant manager**. You don't tell staff \"go to table 4\"; you "
                            "declare \"I want 3 waiters on shift at all times\" (desired state). If one goes home "
                            "sick, the manager calls in a replacement. The **Service** is the restaurant's single "
                            "phone number that rings whichever waiter is free."),
                ("code", """
  kubectl apply ─► Deployment (replicas: 3, image: order-service:1.4.2)
                       │ manages
                       ▼
                   ReplicaSet ──creates/replaces──► Pod  Pod  Pod      (each: 1 container + IP)
                                                     ▲    ▲    ▲
  other pods ──► Service "order-service" (stable DNS + load balancing; selects label app=order-service)
"""),
                ("code", """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 3
  selector:
    matchLabels: { app: order-service }
  strategy:
    rollingUpdate: { maxUnavailable: 0, maxSurge: 1 }      # zero-downtime deploys
  template:
    metadata:
      labels: { app: order-service }
    spec:
      containers:
        - name: app
          image: registry.example.com/order-service:1.4.2   # pin versions, never :latest
          ports: [{ containerPort: 8080 }]
          envFrom:
            - configMapRef: { name: order-service-config }
            - secretRef:    { name: order-service-secrets }
          resources:
            requests: { cpu: "500m", memory: "768Mi" }      # used for scheduling
            limits:   { memory: "768Mi" }                   # exceed → OOMKilled
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector: { app: order-service }
  ports: [{ port: 80, targetPort: 8080 }]
# other pods call http://order-service/api/orders
"""),
                ("code", """
apiVersion: v1
kind: ConfigMap
metadata: { name: order-service-config }
data:
  SPRING_PROFILES_ACTIVE: "prod"
  SPRING_DATASOURCE_URL: "jdbc:postgresql://orders-db:5432/orders"
---
# Secret values are only base64-encoded, not encrypted. Restrict access with RBAC and
# enable encryption at rest, or use an external secrets manager (Vault, cloud KMS).
kubectl create secret generic order-service-secrets --from-literal=SPRING_DATASOURCE_PASSWORD=...
"""),
                ("warn", "**No resource requests/limits.** The scheduler packs pods blindly, one memory-hungry "
                         "pod starves its neighbours, and the node evicts random pods. Always set requests; set a "
                         "memory limit; be careful with CPU limits (they cause throttling and slow JVM start-up)."),
                ("key", ["Deployment = desired state; ReplicaSet/Pods are managed for you.",
                         "Service = stable name + load balancing over pods selected by labels.",
                         "Config in ConfigMaps, credentials in Secrets, resources always declared."]),
            ],
            "questions": [
                "You delete one of the 3 pods with `kubectl delete pod order-service-abc`. What happens next, "
                "and which object makes it happen?",
            ],
            "answer": "The **ReplicaSet** (owned by the Deployment) sees 2 running pods versus the desired 3 "
                      "and immediately creates a new pod. The Service stops routing to the deleted pod and "
                      "starts routing to the new one once it becomes Ready.",
        },
        # ------------------------------------------------------------------ 7.3
        {
            "title": "Health Probes: Liveness, Readiness & Startup",
            "blocks": [
                ("analogy", "A **hospital check-up**. *Startup probe*: \"has the patient woken up from surgery "
                            "yet?\" (be patient). *Readiness*: \"can they receive visitors right now?\" (if not, "
                            "send visitors elsewhere, but don't panic). *Liveness*: \"is the heart beating?\" "
                            "(if not, resuscitate, i.e. restart)."),
                ("table", [["Probe", "Question", "On failure"],
                           ["**startupProbe**", "Has the app finished starting?", "Keep waiting until threshold, then restart; other probes are paused"],
                           ["**readinessProbe**", "Can it serve traffic now?", "Removed from Service endpoints. **No restart**"],
                           ["**livenessProbe**", "Is it stuck/deadlocked beyond repair?", "Container is **restarted**"]],
                 [0.2, 0.38, 0.42]),
                ("h", "Spring Boot Actuator support"),
                ("code", """
# application.yml (auto-enabled when running on Kubernetes; explicit here for clarity)
management:
  endpoint:
    health:
      probes:
        enabled: true
      group:
        readiness:
          include: readinessState, db, redis     # dependencies affect READINESS only
  endpoints:
    web:
      exposure:
        include: health, info, prometheus
"""),
                ("code", """
          startupProbe:
            httpGet: { path: /actuator/health/liveness, port: 8080 }
            periodSeconds: 5
            failureThreshold: 30                  # up to 150 s to start
          livenessProbe:
            httpGet: { path: /actuator/health/liveness, port: 8080 }
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet: { path: /actuator/health/readiness, port: 8080 }
            periodSeconds: 5
            failureThreshold: 3
"""),
                ("p", "Also add graceful shutdown so in-flight requests finish during rolling updates: "
                      "`server.shutdown: graceful` and `spring.lifecycle.timeout-per-shutdown-phase: 20s`."),
                ("warn", "**Checking the database in the liveness probe.** The DB has a 30-second blip → "
                         "liveness fails on *every* pod → Kubernetes restarts them all at once → all pods are "
                         "starting simultaneously and hammer the recovering DB. A self-inflicted outage. "
                         "External dependencies belong in **readiness**, never liveness."),
                ("key", ["Liveness = restart me; readiness = don't send me traffic; startup = give me time.",
                         "Liveness checks only the app itself; dependencies go in readiness.",
                         "Use a startup probe for slow JVM boots instead of a huge liveness delay."]),
            ],
            "questions": [
                "A pod takes 90 s to start. Its liveness probe has `initialDelaySeconds: 30`, `periodSeconds: 10`, "
                "`failureThreshold: 3`, and no startup probe. What happens, and how do you fix it?",
            ],
            "answer": "Liveness starts at 30 s, fails at 30/40/50 s, so at ~50 s the container is **killed and "
                      "restarted**, before it ever finishes starting. It loops forever (`CrashLoopBackOff`). "
                      "Fix: add a **startupProbe** (e.g. `periodSeconds: 5`, `failureThreshold: 30`) so liveness "
                      "only begins after startup succeeds.",
        },
        # ------------------------------------------------------------------ 7.4
        {
            "title": "Troubleshooting Pods",
            "blocks": [
                ("analogy", "Debugging a pod is like a **doctor's diagnosis**: look at the symptoms (status), "
                            "read the chart (`describe` events), listen to the patient (`logs`), then examine "
                            "directly (`exec`). Don't prescribe before you diagnose."),
                ("code", """
 kubectl get pods  →  what is the STATUS?
 │
 ├─ Pending ───────────────► kubectl describe pod → Events:
 │                            "Insufficient memory/cpu"  → lower requests or add nodes
 │                            "unbound PersistentVolumeClaim" → fix storage
 │
 ├─ ImagePullBackOff ──────► wrong image name/tag, or missing imagePullSecrets for private registry
 │
 ├─ CrashLoopBackOff ──────► kubectl logs <pod> --previous   (logs of the crashed attempt!)
 │                            app exception on startup? bad config/env? liveness killing it?
 │
 ├─ OOMKilled (exit 137) ──► describe → "Last State: Terminated, Reason: OOMKilled"
 │                            raise memory limit or lower MaxRAMPercentage; check for leaks
 │
 └─ Running but 0/1 READY ─► readiness failing → curl /actuator/health/readiness from inside;
                              Service has no endpoints: kubectl get endpoints <svc>
"""),
                ("h", "Your toolkit"),
                ("code", """
kubectl get pods -o wide                         # status, restarts, node, IP
kubectl describe pod order-service-7d9f-abcde    # events: scheduling, pulls, probe failures, OOM
kubectl logs order-service-7d9f-abcde -f         # live logs
kubectl logs order-service-7d9f-abcde --previous # logs from the container that crashed
kubectl get events --sort-by=.lastTimestamp      # cluster-wide recent events
kubectl exec -it order-service-7d9f-abcde -- sh  # shell inside (if image has one)
kubectl top pod                                  # live CPU/memory (needs metrics-server)
kubectl port-forward svc/order-service 8080:80   # hit the service from your laptop
kubectl rollout undo deployment/order-service    # fastest fix for a bad release
"""),
                ("table", [["Exit code", "Meaning"],
                           ["0", "Process exited normally (did your main thread finish? a CommandLineRunner app?)"],
                           ["1", "Application error: read the logs"],
                           ["137", "SIGKILL: usually **OOMKilled**, or failed liveness probe"],
                           ["143", "SIGTERM: normal shutdown requested (rolling update, scale-down)"]],
                 [0.15, 0.85]),
                ("warn", "Running `kubectl logs` on a CrashLoopBackOff pod and seeing only a few startup lines, "
                         "because you're looking at the *new* attempt. The real error is in "
                         "`kubectl logs --previous`. And always read the **Events** section of `describe` "
                         "first: it explains most Pending/ImagePull/OOM problems in one line."),
                ("key", ["Status tells you where to look: Pending → scheduling; BackOff → image or app.",
                         "`describe` (events) → `logs --previous` → `exec`, in that order.",
                         "Exit 137 = killed (OOM/liveness); exit 1 = your app threw."]),
            ],
            "questions": [
                "After deploying v1.5, pods show `CrashLoopBackOff` with 6 restarts. `kubectl logs --previous` "
                "shows: `Failed to configure a DataSource: 'url' attribute is not specified`. What's the likely "
                "cause and the first two actions you take?",
            ],
            "answer": "The datasource URL isn't reaching the app: the ConfigMap is missing/renamed, the "
                      "`envFrom` reference changed, or a profile didn't activate. Actions: (1) "
                      "`kubectl rollout undo deployment/order-service` to restore service immediately; (2) "
                      "inspect `kubectl describe pod` / `kubectl get configmap order-service-config -o yaml` "
                      "and compare the env vars with what v1.5 expects, then fix and redeploy.",
        },
    ],
}
