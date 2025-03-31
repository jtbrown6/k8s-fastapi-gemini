# Lesson 4: Stark Industries R&D (ConfigMaps & Secrets)

**Objective:** Learn how to manage application configuration separately from the container image using Kubernetes ConfigMaps for non-sensitive data and Secrets for sensitive data like API keys or passwords. Inject these into our application Pods as environment variables.

**Analogy:** Our Iron Man suit (container image) shouldn't have mission details or classified access codes hardcoded inside it. That's inflexible and insecure! Instead, Stark Industries R&D (Kubernetes) provides separate data modules: public mission briefings (ConfigMaps) and classified access keycards (Secrets) that are given to the suit (Pod) only when it's deployed for a specific mission.

## Concepts Introduced

### 1. The Problem: Hardcoded Configuration

*   In Lesson 1, our hero list was hardcoded. If we wanted to change the greeting message or an API endpoint URL, we'd have to:
    1.  Modify the Python code (`main.py`).
    2.  Rebuild the Docker image (`docker build`).
    3.  Push the new image to the registry (Harbor).
    4.  Redeploy the application in Kubernetes to use the new image.
*   This is slow, inefficient, and mixes configuration with application logic. It's also terrible for sensitive data like passwords or API keys – you should **never** hardcode secrets in your image!

### 2. ConfigMaps: Public Mission Briefings

*   **What they are:** Kubernetes objects used to store non-sensitive configuration data in key-value pairs. They decouple configuration from the Pod/container.
*   **Analogy:** A ConfigMap is like a public mission briefing posted on the wall at Avengers HQ. It contains general information needed for the mission (like our `GREETING_MESSAGE` or `LOG_LEVEL`) that isn't secret. Any authorized personnel (Pods) can be configured to read this briefing. Defined in `configmap.yaml`.

### 3. Secrets: Classified Access Keycards

*   **What they are:** Kubernetes objects designed to hold small amounts of sensitive data, such as passwords, tokens, or keys. Data is stored base64-encoded by default (providing obscurity, not strong encryption at rest unless etcd encryption is enabled). Their primary security benefit comes from Kubernetes RBAC (Role-Based Access Control), which restricts who can read or modify them.
*   **Analogy:** A Secret is like a classified S.H.I.E.L.D. file or a Stark Industries access keycard (`API_KEY`, `DATABASE_PASSWORD`). It's sensitive information needed for specific operations. Access is restricted, and it's handed securely to the hero (Pod) that needs it. Defined in `secret.yaml`. **Remember:** Base64 is easily decoded; treat Secrets as sensitive and control access via RBAC.

### 4. Injecting Config into Pods (Environment Variables)

*   **How it works:** We modify the Deployment manifest (`deployment.yaml`) to tell Kubernetes: "When you create Pods for this Deployment, inject data from this ConfigMap and this Secret as environment variables inside the container."
*   **Methods:**
    *   `envFrom`: Injects *all* key-value pairs from a ConfigMap or Secret as environment variables. Convenient but less explicit.
    *   `env` with `valueFrom`: Injects a *specific* key from a ConfigMap (`configMapKeyRef`) or Secret (`secretKeyRef`) as a specific environment variable. More verbose but clearer control.
*   **Analogy:** This is like programming the Iron Man suit's systems (container environment) to automatically load the mission briefing (`envFrom: configMapRef`) and the access codes (`envFrom: secretRef`) when the suit powers up. The application code (`main.py`) can then simply read these environment variables (`os.getenv(...)`).

## Practical Exercise: Applying Configuration

**Part 1: Update Code & Image (CI/CD)**

1.  **Update Local Code:**
    *   Replace the content of `hero-academy/lesson-01-recruit/main.py` with the content from `hero-academy/lesson-04-config-secrets/main.py`. (We're evolving the app in place for simplicity, though separate lesson branches in Git would be better practice).
    *   *(Optional but Recommended)* Update the `APP_NAME` or add a version tag in your `.gitlab-ci.yml` to reflect Lesson 4, e.g., `hero-registry:lesson-04`. If you change the tag, make sure to update the `image:` line in `lesson-04-config-secrets/deployment.yaml` accordingly. For now, we'll assume you stick with `:latest` and overwrite it.
2.  **Commit & Push:** Add the changes to Git and push them to GitLab.
    ```bash
    # Assuming you copied the new main.py over the old one
    git add hero-academy/lesson-01-recruit/main.py
    # Add the new lesson 4 manifests (if you want them in git)
    git add hero-academy/lesson-04-config-secrets/
    git commit -m "Feat: Update app for Lesson 4 (ConfigMaps/Secrets) and add manifests"
    git push
    ```
3.  **Monitor CI/CD:** Go to GitLab (`CI/CD` -> `Pipelines`) and ensure the pipeline runs successfully, building the new image (with the code that reads environment variables) and pushing it to Harbor (e.g., `harbor.komebacklab.local/your-project/hero-registry:latest`).

**Part 2: Apply Kubernetes Manifests**

1.  **Navigate:** Open a terminal with `kubectl` configured and navigate to the `hero-academy/lesson-04-config-secrets` directory.
2.  **Apply ConfigMap:** Create the ConfigMap resource in your cluster.
    ```bash
    kubectl apply -f configmap.yaml --namespace=default
    ```
    *   Verify: `kubectl get configmap hero-registry-config -n default -o yaml`
3.  **Apply Secret:** Create the Secret resource.
    ```bash
    kubectl apply -f secret.yaml --namespace=default
    ```
    *   Verify: `kubectl get secret hero-registry-secret -n default -o yaml` (Note the base64 encoded data).
4.  **Apply Updated Deployment:** Apply the modified deployment file. Kubernetes will detect the changes (like the added `envFrom` sections) and perform a rolling update, creating new Pods with the new configuration and terminating the old ones.
    ```bash
    # Make sure the image tag in deployment.yaml matches what CI/CD pushed!
    # And ensure your-harbor-project is correct.
    kubectl apply -f deployment.yaml --namespace=default
    ```

**Part 3: Verify Configuration Injection**

1.  **Check Deployment Rollout:** Ensure the new Pods are created and running.
    ```bash
    kubectl rollout status deployment/hero-registry-deployment --namespace=default
    kubectl get pods --selector=app=hero-registry --namespace=default
    ```
2.  **Inspect Pod Environment:** Exec into one of the running Pods and check its environment variables.
    ```bash
    # Get a pod name (replace xxxx-yyyy with actual ID)
    POD_NAME=$(kubectl get pods --selector=app=hero-registry -n default -o jsonpath='{.items[0].metadata.name}')
    echo "Inspecting Pod: $POD_NAME"

    # Exec into the pod and print environment variables
    kubectl exec -it $POD_NAME --namespace=default -- /bin/sh -c 'echo "--- Environment Variables ---"; printenv | grep -E "GREETING_MESSAGE|LOG_LEVEL|API_KEY|DATABASE_PASSWORD"; echo "---------------------------"'
    ```
    You should see the `GREETING_MESSAGE`, `LOG_LEVEL`, `API_KEY`, and `DATABASE_PASSWORD` variables listed with the values from your ConfigMap and Secret.

3.  **Check Application Logs:** See the startup messages printed by the updated `main.py`.
    ```bash
    kubectl logs $POD_NAME --namespace=default
    ```
    You should see the "--- Configuration Loaded ---" block with the greeting message and masked secrets printed when the container started.

4.  **Test API Endpoints:**
    *   Use `kubectl port-forward` as in Lesson 3:
        ```bash
        kubectl port-forward service/hero-registry-service 8080:80 --namespace=default
        ```
    *   Open your browser or use `curl`:
        *   `http://localhost:8080/` - Should show the greeting message from the ConfigMap!
        *   `http://localhost:8080/heroes` - Should still work (API key check is currently bypassed in the code).
        *   *(Optional)* Try sending the key: `curl -H "X-API-Key: s3cr3t-ap1-k3y" http://localhost:8080/heroes` (Check Pod logs to see if the key was received).

## Problem-Solving Framework: Config & Secret Issues

1.  **Identify the Symptom:** Pods crashing (`CrashLoopBackOff`)? Application not using the expected configuration values? `kubectl apply` errors for ConfigMap/Secret/Deployment? Pods not starting (`CreateContainerConfigError`)?
2.  **Locate the Problem Area:**
    *   *`kubectl apply` errors:* YAML syntax errors in `configmap.yaml`, `secret.yaml`, or `deployment.yaml`. Invalid keys or structure. For Secrets, ensure data values are base64 encoded.
    *   *Pods `CreateContainerConfigError`:* Kubernetes cannot find the referenced ConfigMap or Secret when trying to create the container.
        *   Does the ConfigMap/Secret exist in the **same namespace** as the Pod? (`kubectl get configmap <name> -n <namespace>`, `kubectl get secret <name> -n <namespace>`)
        *   Are the names in the Deployment's `envFrom` (`configMapRef.name`, `secretRef.name`) or `env.valueFrom` (`configMapKeyRef.name`, `secretKeyRef.name`) spelled correctly and match the actual ConfigMap/Secret names?
    *   *Pods `CrashLoopBackOff` / App behaving incorrectly:* The application started but isn't getting or using the environment variables correctly.
        *   Verify injection: Use `kubectl exec <pod-name> -- printenv` (as shown above) to confirm the environment variables *are* actually set inside the container. Check spelling and case.
        *   Check application code (`main.py`): Is it reading the correct environment variable names (`os.getenv('VAR_NAME')`)? Is there a typo? Is the default value being used unexpectedly?
        *   Check Pod logs (`kubectl logs <pod-name>`) for any errors related to configuration loading or usage.
    *   *Secrets not working:* Remember data values in the `secret.yaml` *must* be base64 encoded. If you put plain text there, the application will receive the base64 *encoded* version of that plain text as the environment variable value, which is usually wrong. Use `echo -n 'value' | base64` to encode.

3.  **Consult the Blueprints/Manuals:**
    *   *`configmap.yaml`/`secret.yaml`:* Check `apiVersion`, `kind`, `metadata.name`, `data` keys. Ensure Secret data is base64 encoded.
    *   *`deployment.yaml`:* Check `envFrom` or `env.valueFrom` sections. Ensure `name` references are correct.
    *   *`main.py`:* Check `os.getenv()` calls for correct variable names.
    *   *`kubectl describe pod <pod-name>`:* Look for events related to mounting ConfigMaps/Secrets or container creation errors.
    *   *`kubectl logs <pod-name>`:* Check application output.

4.  **Isolate and Test:**
    *   Temporarily replace `secretRef` with `configMapRef` pointing to a dummy ConfigMap to rule out Secret-specific issues (like base64 encoding).
    *   Inject a simple, known key-value pair. Does that specific variable appear via `printenv`?
    *   Simplify the application code to just print the environment variable on startup.

5.  **Verify Assumptions:** Did you assume the ConfigMap/Secret was in the correct namespace? Did you assume the keys inside the ConfigMap/Secret matched the environment variable names expected by the app? Did you correctly base64 encode Secret values?

**Excellent! You've decoupled configuration from your application image, making deployments more flexible and secure. Next, we'll give our application persistent memory using Volumes.**
