# Lesson 3: Assembling the Team (Intro to Kubernetes)

**Objective:** Deploy our containerized "Hero Registry" application, built and pushed in the previous lessons, onto your K3s Kubernetes cluster.

**Analogy:** Mission Control (GitLab) has built the suits (Docker images) and stored them in the armory (Harbor). Now it's time for Nick Fury (you, using `kubectl`) to officially assemble the team (deploy the application) onto the active Helicarrier (your K3s Kubernetes cluster).

## Concepts Introduced

### 1. Kubernetes (K8s): The Helicarrier/Avengers HQ

*   **What it is:** An open-source container orchestration platform designed to automate the deployment, scaling, and management of containerized applications. Your K3s is a lightweight, certified Kubernetes distribution.
*   **Analogy:** Kubernetes is like the S.H.I.E.L.D. Helicarrier or the Avengers Compound. It's a massive, complex system that manages all your deployed heroes (containers), ensuring they have the resources they need, replacing them if they fall (crash), managing their communication networks, and scaling the team up or down based on the mission's demands.

### 2. `kubectl`: The Mission Control Console

*   **What it is:** The command-line tool for interacting with the Kubernetes cluster's API server. You use it to deploy applications, inspect resources, view logs, and manage the cluster.
*   **Analogy:** `kubectl` is your command console, like Nick Fury's interface to manage S.H.I.E.L.D. operations or Tony Stark's interface to control his suits and the Tower's systems. You issue commands (`kubectl apply`, `kubectl get pods`, `kubectl logs`) to tell Kubernetes what to do.

### 3. Nodes: Helicarrier Sections / Quinjet Landing Pads

*   **What they are:** The worker machines (virtual or physical) in your cluster where your containers actually run. Your K3s setup has control plane nodes (management) and worker nodes (running applications).
*   **Analogy:** Nodes are like the different sections or hangars of the Helicarrier, or the designated landing pads for Quinjets. They provide the actual compute power (CPU, RAM) where the heroes (Pods/containers) operate. Kubernetes decides which Node is best suited for each Pod.

### 4. Pods: The Heroes (or Hero Teams)

*   **What they are:** The smallest deployable units in Kubernetes. A Pod represents a single instance of your running application. It can contain one or more tightly coupled containers that share storage and network resources. Usually, it's one main container per Pod.
*   **Analogy:** A Pod is like an individual Avenger (e.g., Iron Man in his suit) deployed on a mission. It contains the core application (Tony Stark in the suit) and potentially helper containers (like JARVIS running diagnostics - though we only have one container for now). Pods are *ephemeral* – they can be destroyed and replaced by Kubernetes.

### 5. Deployments: The Team Strategy

*   **What it is:** A Kubernetes object that manages a set of identical Pods (ReplicaSet). It ensures that a specified number of Pods (`replicas`) are running and healthy. It handles updates (rolling updates, recreate) and rollbacks.
*   **Analogy:** A Deployment is the strategic plan for a specific team or type of hero. It dictates how many Iron Man suits (`replicas: 2`) should be active, what version of the suit they should wear (`spec.template.spec.containers[0].image`), and how to update them to a new version without disrupting the overall mission (update strategy). If a suit gets damaged (Pod crashes), the Deployment automatically deploys a replacement. Defined in `deployment.yaml`.

### 6. Services: Communication Lines / Team Radio Frequency

*   **What it is:** An abstraction that defines a logical set of Pods (usually selected by labels) and a policy by which to access them. It provides a stable IP address and DNS name within the cluster, regardless of individual Pod IPs which can change.
*   **Analogy:** A Service is like a dedicated, stable communication channel or radio frequency for a specific team (e.g., "Avengers Alpha Team, report on frequency 10.0.0.5"). Even if individual heroes (Pods) are replaced, other teams or Mission Control can still reach "Avengers Alpha Team" using that stable frequency (the Service IP/DNS name). It directs incoming requests to one of the available, healthy Pods matching its `selector`. Defined in `service.yaml`. We used `type: ClusterIP`, meaning this frequency is only for internal cluster communication for now.

### 7. Namespaces: HQ Departments / Security Zones

*   **What they are:** A way to divide cluster resources between multiple users or teams. They provide a scope for names; resource names must be unique within a namespace but not across namespaces.
*   **Analogy:** Namespaces are like different departments within Avengers HQ (e.g., R&D, Operations, Medical) or different security zones on the Helicarrier. They help organize resources and control access. We'll deploy our app into the `default` namespace for now, but creating dedicated namespaces is good practice for larger projects.

### 8. ImagePullSecrets: Armory Access Keys

*   **What it is:** A type of Kubernetes Secret specifically used to store credentials (like username/password or tokens) for accessing private container registries (like your Harbor).
*   **Analogy:** Since your Harbor armory is private, Kubernetes needs the correct access key (`imagePullSecret`) to retrieve the suit designs (Docker images). Without it, the Deployment can't pull the image to create the Pods.

## Practical Exercise: Deploying to K3s

**Part 1: Prepare Kubernetes**

1.  **Configure `kubectl`:** Ensure your `kubectl` command-line tool is configured to talk to your K3s cluster. If you installed K3s, it usually places a `kubeconfig` file at `/etc/rancher/k3s/k3s.yaml`. You might need to copy this to `~/.kube/config` or set the `KUBECONFIG` environment variable:
    ```bash
    # Example (adjust path if needed, run on a machine with kubectl access)
    # sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
    # sudo chown $(id -u):$(id -g) ~/.kube/config # Fix permissions
    # OR
    # export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
    ```
    *   Verify connection:
        ```bash
        kubectl cluster-info
        kubectl get nodes
        ```

2.  **Create Harbor Secret:** Kubernetes needs credentials to pull from `harbor.komebacklab.local`. Create a secret named `harbor-creds`. **Run this command on your machine where `kubectl` is configured.**
    *   Replace `<your-harbor-user>` with your Harbor username or robot account name (e.g., `robot$your-project+gitlab`).
    *   Replace `<your-harbor-password>` with your Harbor password or robot account token.
    *   Replace `<your-harbor-email>` with any email address (it's required by the command but often not strictly used by Harbor).
    *   *(Optional)* Replace `default` with a specific namespace if you create one (`kubectl create namespace your-namespace-name`).
    ```bash
    kubectl create secret docker-registry harbor-creds \
      --docker-server=harbor.komebacklab.local \
      --docker-username='<your-harbor-user>' \
      --docker-password='<your-harbor-password>' \
      --docker-email='<your-harbor-email>' \
      --namespace=default # Or your specific namespace
    ```
    *   Verify the secret was created:
        ```bash
        kubectl get secret harbor-creds --namespace=default -o yaml
        ```

3.  **Update Manifests (If Needed):**
    *   **Crucially, ensure the `image:` line in `deployment.yaml` points to the correct image path in your Harbor registry**, including your actual Harbor project name:
        ```yaml
        # In deployment.yaml
        image: harbor.komebacklab.local/your-actual-harbor-project/hero-registry:latest
        ```
    *   Ensure the `imagePullSecrets.name` in `deployment.yaml` matches the secret name you just created (`harbor-creds`).
    *   Ensure the `selector.app` in `service.yaml` matches the `labels.app` in `deployment.yaml` (`app: hero-registry`).

**Part 2: Apply Manifests**

1.  **Navigate:** Open a terminal on the machine where `kubectl` is configured and navigate to the `hero-academy/lesson-03-k8s-intro` directory containing `deployment.yaml` and `service.yaml`.
2.  **Apply Deployment:** Tell Kubernetes to create the resources defined in the deployment file.
    ```bash
    kubectl apply -f deployment.yaml --namespace=default
    ```
    You should see `deployment.apps/hero-registry-deployment created` (or configured).
3.  **Apply Service:** Tell Kubernetes to create the Service.
    ```bash
    kubectl apply -f service.yaml --namespace=default
    ```
    You should see `service/hero-registry-service created` (or configured).

**Part 3: Verify Deployment**

1.  **Check Deployment Status:** See if the Deployment is progressing and the desired number of replicas are ready.
    ```bash
    kubectl get deployment hero-registry-deployment --namespace=default
    # Look for READY column matching DESIRED (e.g., 2/2)
    ```
2.  **Check Pods:** List the Pods created and managed by the Deployment. They should have status `Running`.
    ```bash
    kubectl get pods --selector=app=hero-registry --namespace=default
    # You should see two Pods (e.g., hero-registry-deployment-xxxx-yyyy) with STATUS Running
    ```
    *   If Pods are stuck in `Pending` or `ImagePullBackOff`, check the secret (`harbor-creds`) and the image path in `deployment.yaml`. Use `kubectl describe pod <pod-name> -n default` to see detailed events and errors.
3.  **Check Service:** Verify the Service was created and got a ClusterIP.
    ```bash
    kubectl get service hero-registry-service --namespace=default
    # Note the CLUSTER-IP assigned (e.g., 10.43.x.x) and PORT(S) (80/TCP)
    ```

**Part 4: Access the Service (Internal)**

Since the Service is `ClusterIP`, it's only directly reachable *within* the cluster. Here are two ways to test it:

1.  **Port Forwarding (Easiest):** `kubectl` can forward a local port on your machine directly to a Pod or Service in the cluster.
    *   Forward local port 8080 to the Service's port 80:
        ```bash
        kubectl port-forward service/hero-registry-service 8080:80 --namespace=default
        ```
    *   Keep this command running. Now, open your **local** web browser and go to:
        *   `http://localhost:8080/heroes`
        *   `http://localhost:8080/docs`
    *   Press `Ctrl+C` in the terminal to stop forwarding.

2.  **(Alternative) Run a temporary Pod:** Create a temporary Pod inside the cluster and use `curl` from there.
    ```bash
    kubectl run tmp-curl --image=curlimages/curl:latest --rm -it -- /bin/sh
    # Once inside the temporary pod's shell:
    curl http://hero-registry-service/heroes # Use the Service name (DNS works internally)
    curl http://hero-registry-service/docs
    exit
    ```

## Problem-Solving Framework: K8s First Deployment Issues

Deploying to Kubernetes adds new layers for potential problems.

1.  **Identify the Symptom:** What failed? `kubectl apply` error? Pods not starting (`Pending`, `ImagePullBackOff`, `CrashLoopBackOff`)? Service not reachable?
2.  **Locate the Problem Area:**
    *   *`kubectl apply` errors:* Often YAML syntax errors (indentation!), incorrect `apiVersion`/`kind`, or missing required fields. Use `kubectl apply --validate=true ...` or online YAML validators. Also check if `kubectl` is configured correctly (`kubectl cluster-info`).
    *   *Pods `Pending`:* Usually means the scheduler can't find a Node with enough resources (CPU/memory) or matching node selectors/taints (less likely in a simple K3s setup). Use `kubectl describe pod <pod-name> -n <namespace>` and look at the `Events` section.
    *   *Pods `ImagePullBackOff` / `ErrImagePull`:* Kubernetes cannot pull the container image.
        *   Is the image path in `deployment.yaml` (`image: ...`) **exactly** correct (registry/project/name:tag)?
        *   Does the `imagePullSecrets` section exist in `deployment.yaml`?
        *   Does the secret named (`harbor-creds`) exist in the **same namespace**? (`kubectl get secret harbor-creds -n <namespace>`)
        *   Are the credentials *inside* the secret correct? (You might need to decode it: `kubectl get secret harbor-creds -n <namespace> -o jsonpath='{.data.\.dockerconfigjson}' | base64 --decode`)
        *   Can the K3s nodes actually reach `harbor.komebacklab.local` (DNS, network connectivity)?
    *   *Pods `CrashLoopBackOff`:* The container starts but then immediately crashes, repeatedly. Kubernetes keeps trying, hence the "loop".
        *   The issue is *inside* your container/application. Check the logs: `kubectl logs <pod-name> -n <namespace>`.
        *   If logs are empty or brief, try getting logs from the *previous* crashed container: `kubectl logs <pod-name> -n <namespace> --previous`.
        *   Common causes: Application errors on startup, incorrect configuration passed via env vars/configmaps (later lessons), missing files inside the container, incorrect `CMD` in Dockerfile.
    *   *Service not reachable (e.g., via `port-forward`):*
        *   Does the Service `selector` (`app: hero-registry`) exactly match the Pod labels in the Deployment's `template.metadata.labels`? Use `kubectl get pods --show-labels -n <namespace>` and `kubectl describe service <service-name> -n <namespace>` (check the `Selector` and `Endpoints` fields).
        *   Is the `targetPort` in the Service (e.g., 8000) the same port the container is actually listening on (`containerPort` in Deployment)?
        *   Are the Pods actually running and healthy? (`kubectl get pods -n <namespace>`)

3.  **Consult the Blueprints/Manuals:**
    *   *`deployment.yaml` / `service.yaml`:* Check `apiVersion`, `kind`, `metadata.name`, `spec.replicas`, `spec.selector`, `spec.template.metadata.labels`, `spec.template.spec.containers[0].image`, `ports`, `imagePullSecrets`. YAML indentation is critical!
    *   *`kubectl describe <resource-type> <resource-name> -n <namespace>`:* Provides detailed status and events. Essential for debugging Pods, Deployments.
    *   *`kubectl logs <pod-name> -n <namespace>`:* Shows the standard output/error from your container.
    *   *Kubernetes Documentation:* Official docs are excellent for understanding resource types and fields.

4.  **Isolate and Test:**
    *   Can you pull the image manually from a K3s node? (`docker pull harbor.komebacklab.local/...`)
    *   Try deploying a simpler image first (e.g., `nginx`). Does that work?
    *   Reduce replicas to 1 in the Deployment. Does that single Pod start?

5.  **Verify Assumptions:** Did you assume the namespace was correct everywhere? Did you assume the labels matched? Did you assume the Harbor credentials were correct? Did you assume the port numbers matched?

**Congratulations! You've deployed your first application to Kubernetes. The team is assembled on the Helicarrier. Next, we'll learn how to manage configuration using ConfigMaps and Secrets.**
