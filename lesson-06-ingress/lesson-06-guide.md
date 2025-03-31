# Lesson 6: Opening the Bifrost (Ingress & External Access)

**Objective:** Expose our "Hero Registry" application, currently only accessible within the cluster (`ClusterIP` Service), to the outside world using a Kubernetes Ingress resource and the Ingress controller running in your K3s cluster (likely Traefik).

**Analogy:** Our Avengers HQ (Kubernetes cluster) is operational, and the team (Pods/Service) is assembled. However, it's currently isolated. We need Heimdall (the Ingress Controller) to open the Bifrost Bridge (external network path) and use the Ingress resource as the runic instructions, directing visitors arriving from Midgard (your browser/network) asking for `hero-registry.komebacklab.local` to the correct internal communication channel (`hero-registry-service`).

## Concepts Introduced

### 1. The Problem: Internal Access Only

*   Our `hero-registry-service` is of type `ClusterIP` (Lesson 3). This means it has an IP address and DNS name *only* reachable from *within* the Kubernetes cluster.
*   We could use `kubectl port-forward`, but that's only for temporary debugging/access from your local machine.
*   We could change the Service type to `NodePort` or `LoadBalancer`, but:
    *   `NodePort` exposes the app on a high port on *every* node's IP, which is awkward to manage and access.
    *   `LoadBalancer` requires integration with an external load balancer (cloud provider or something like MetalLB in your homelab), which adds complexity.
*   We need a standard, flexible way to manage external HTTP/HTTPS access, handle hostnames, paths, and TLS termination.

### 2. Ingress Controller: Heimdall, Guardian of the Bifrost

*   **What it is:** A specialized load balancer/reverse proxy running within the Kubernetes cluster that watches for Ingress resources and configures itself according to the rules defined in them. K3s bundles the Traefik Ingress controller by default.
*   **Analogy:** The Ingress Controller is Heimdall. He stands at the entrance to Asgard (the cluster edge), watching for instructions (Ingress resources). When a visitor arrives (HTTP request), Heimdall checks their destination (`Host` header) and path, consults the instructions (Ingress rules), and opens the Bifrost to route them to the correct internal service.

### 3. Ingress Resource: Runic Instructions for Heimdall

*   **What it is:** A Kubernetes object (`kind: Ingress`) that defines rules for how external HTTP/HTTPS traffic should be routed to internal Services. Rules are typically based on the requested hostname and URL path.
*   **Analogy:** The Ingress resource (`ingress.yaml`) contains the runic instructions given to Heimdall. It says, "If someone arrives asking for `hero-registry.komebacklab.local` (`spec.rules.host`), send them (`backend.service`) to the `hero-registry-service` on its port `80` (`backend.service.port.number`)."
*   `spec.ingressClassName`: Explicitly tells *which* Ingress controller (which Heimdall, if you had multiple) should handle these instructions. K3s usually uses `traefik`.
*   `spec.rules`: Contains the list of host-based rules.
*   `spec.rules.host`: The external hostname that this rule applies to.
*   `spec.rules.http.paths`: Rules for specific URL paths under that host.
    *   `path`: The URL path (e.g., `/`, `/api`, `/admin`).
    *   `pathType`: How the path should be matched (`Prefix`, `Exact`, `ImplementationSpecific`). `Prefix` is common.
    *   `backend.service.name`: The internal Service to route traffic to.
    *   `backend.service.port.number`: The port number exposed by the *Service* (not the Pod's `targetPort`).

### 4. DNS Configuration (External to Kubernetes)

*   **Crucial Point:** Kubernetes Ingress *only* handles routing *after* the traffic reaches the Ingress controller. It does **not** manage external DNS.
*   You need to configure your DNS server (the one managing `komebacklab.local`) so that the hostname used in the Ingress rule (`hero-registry.komebacklab.local`) resolves to the IP address where your Ingress controller is listening.
*   **How?** In a K3s setup, the Traefik Ingress controller typically runs as a `DaemonSet` or `Deployment` and is exposed via a `LoadBalancer` or `NodePort` Service provided by K3s itself (often using ports 80/443 on the nodes' IPs). You need to point your DNS A record for `hero-registry.komebacklab.local` to the IP address(es) of your K3s worker node(s) or a dedicated LoadBalancer IP if you have one configured in front of K3s.

## Practical Exercise: Exposing the Service

**Part 1: Prepare DNS**

1.  **Identify Ingress Controller IP(s):** Determine the IP address(es) where your K3s Ingress controller (Traefik) is listening for external traffic. This is often the IP address(es) of your K3s worker nodes. You might also have a LoadBalancer service for Traefik.
    *   Check the Traefik service: `kubectl get svc -n kube-system traefik` (Look for `EXTERNAL-IP` or `NODEPORT` mappings).
    *   If using Node IPs, get your worker node IPs: `kubectl get nodes -o wide`.
2.  **Configure DNS:** Go to your DNS server managing `komebacklab.local`. Create an **A record** (or CNAME if pointing to another name) for `hero-registry.komebacklab.local` pointing to the IP address(es) identified in the previous step.
    *   Example A Record: `hero-registry.komebacklab.local IN A 192.168.1.100` (Replace with your actual K3s node/LB IP).
3.  **Verify DNS (from your client machine):** Wait a moment for DNS propagation (should be fast in a local network) and test resolution:
    ```bash
    ping hero-registry.komebacklab.local
    # or
    nslookup hero-registry.komebacklab.local
    ```
    Ensure it resolves to the correct K3s node/LB IP address.

**Part 2: Apply Ingress Manifest**

1.  **Verify IngressClass:** Check the name of the IngressClass used by Traefik in your K3s cluster.
    ```bash
    kubectl get ingressclass
    # Look for a class named 'traefik' or similar.
    ```
    Ensure the `spec.ingressClassName` in `ingress.yaml` matches this name.

2.  **Navigate:** Open a terminal with `kubectl` configured and navigate to the `hero-academy/lesson-06-ingress` directory.

3.  **Apply Ingress:** Create the Ingress resource in your cluster.
    ```bash
    kubectl apply -f ingress.yaml --namespace=default
    ```
    *   Verify:
        ```bash
        kubectl get ingress hero-registry-ingress --namespace=default
        # Check ADDRESS (might show node IPs or LB IP), HOSTS, and PORTS (should show 80).
        ```

**Part 3: Test External Access**

1.  **Access via Browser/curl:** Open your web browser or use `curl` from a machine on your network (that can resolve `komebacklab.local` DNS) and navigate to:
    *   `http://hero-registry.komebacklab.local/` - Should show the greeting message.
    *   `http://hero-registry.komebacklab.local/heroes` - Should show the hero list.
    *   `http://hero-registry.komebacklab.local/docs` - Should show the FastAPI docs UI.
    *   *(Try adding a hero via POST again using the external URL)*
        ```bash
        curl -X POST http://hero-registry.komebacklab.local/heroes \
          -H "Content-Type: application/json" \
          -H "X-API-Key: s3cr3t-ap1-k3y" \
          -d '{"name": "Thor", "secret_identity": "Thor Odinson"}'
        ```
        Verify Thor appears in `http://hero-registry.komebacklab.local/heroes`.

## Problem-Solving Framework: Ingress Issues

1.  **Identify the Symptom:** Browser shows "Server Not Found" / DNS error? Browser shows timeout / connection refused? Browser shows 404 Not Found (from the Ingress Controller, not the app)? Browser shows 5xx Server Error (from Ingress Controller)? Application endpoint works but returns unexpected data?
2.  **Locate the Problem Area:**
    *   *"Server Not Found" / DNS Error:* Problem is **external DNS**.
        *   Did you create the A record for `hero-registry.komebacklab.local`?
        *   Does it point to the correct IP address(es) of your K3s nodes/LoadBalancer where the Ingress controller listens?
        *   Can your client machine resolve the name correctly (`ping`, `nslookup`)? Check client DNS settings.
    *   *Timeout / Connection Refused:* Network path issue or Ingress controller not running/exposed.
        *   Is the K3s node/LB IP address reachable from your client machine (firewalls)?
        *   Is the Ingress controller (Traefik) running? (`kubectl get pods -n kube-system -l app.kubernetes.io/name=traefik`)
        *   Is the Traefik service exposed correctly? (`kubectl get svc -n kube-system traefik`) Does it listen on port 80?
    *   *Ingress Controller 404 Not Found:* The Ingress controller received the request but couldn't find an Ingress rule matching the `Host` header (`hero-registry.komebacklab.local`) or path (`/`).
        *   Does the Ingress resource exist? (`kubectl get ingress hero-registry-ingress -n default`)
        *   Is the `host` field in `ingress.yaml` spelled correctly?
        *   Is the `ingressClassName` in `ingress.yaml` correct and matching the controller (`kubectl get ingressclass`)?
        *   Check Ingress controller logs for errors about processing the Ingress resource: `kubectl logs -n kube-system <traefik-pod-name>`
    *   *Ingress Controller 5xx Server Error (e.g., 502 Bad Gateway, 503 Service Unavailable):* The Ingress controller found the rule but failed to connect to the backend Service (`hero-registry-service`).
        *   Is the `backend.service.name` (`hero-registry-service`) in `ingress.yaml` correct?
        *   Is the `backend.service.port.number` (`80`) in `ingress.yaml` the port exposed by the *Service* (not the Pod's `targetPort`)? Check `kubectl get svc hero-registry-service -n default`.
        *   Is the `hero-registry-service` actually running and selecting healthy Pods? Check `kubectl describe svc hero-registry-service -n default` (look at the `Endpoints` section - should list Pod IPs).
        *   Are the application Pods running and healthy? (`kubectl get pods -l app=hero-registry -n default`) Check their logs (`kubectl logs <pod-name>`).
    *   *Application 404 / Incorrect Data:* The request reached your FastAPI application, but the app itself couldn't handle the request for that specific path or returned wrong data. Debugging shifts back to the application logic (`main.py`) and its state (data in `heroes.json`).

3.  **Consult the Blueprints/Manuals:**
    *   *`ingress.yaml`:* Check `apiVersion`, `kind`, `metadata.name`, `ingressClassName`, `rules.host`, `paths.path`, `paths.pathType`, `backend.service.name`, `backend.service.port.number`. YAML syntax.
    *   *`service.yaml`:* Check `metadata.name`, `spec.ports.port`.
    *   *`deployment.yaml`:* Check Pod labels (`spec.template.metadata.labels`) match Service selector.
    *   *`kubectl describe ingress <ingress-name>`:* Shows status, rules, backend details, events.
    *   *`kubectl describe service <service-name>`:* Shows selector, ports, endpoints.
    *   *Ingress Controller Logs (`kubectl logs -n kube-system <traefik-pod-name>`):* Very important for diagnosing routing issues.
    *   *Application Pod Logs (`kubectl logs <app-pod-name>`):* Check for errors if requests seem to reach the app but fail there.
    *   *DNS Server Configuration.*

4.  **Isolate and Test:**
    *   Can you still access the Service internally using `port-forward`? If yes, the problem is likely Ingress or DNS. If no, the problem is the Service or Pods.
    *   Try creating an Ingress rule for a simple, known-good service (like a basic nginx deployment) to test the Ingress controller and DNS setup independently.
    *   Use `curl -v <URL>` to see detailed HTTP request/response headers, which can help pinpoint where things fail.

5.  **Verify Assumptions:** Did you assume the DNS record was created correctly? Did you assume the `ingressClassName` was `traefik`? Did you assume the Service name/port in the Ingress matched the actual Service? Did you assume network connectivity exists between the client, K3s nodes, and Pods?

**The Bifrost is open! Your application is now accessible from your local network via its own hostname. In the next lesson, we'll secure this connection using HTTPS and certificates managed by Cert-Manager.**
