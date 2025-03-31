# Lesson 10: The Ancient One's Spellbook (Helm)

**Objective:** Learn about Helm, the package manager for Kubernetes, and package our Hero Registry application's Kubernetes manifests (Deployment, Service, Ingress, etc.) into a reusable and configurable Helm chart.

**Analogy:** Instead of manually casting individual spells (applying separate YAML files like `deployment.yaml`, `service.yaml`, `ingress.yaml`) every time we want to conjure our Hero Registry application, we'll use the Ancient One's Spellbook (Helm). This spellbook contains pre-written, customizable incantations (Helm chart templates) that bundle all the necessary spells together. With a single command (`helm install`), we can invoke the entire complex enchantment (deploy the application), customizing specific parameters (values) like the image tag or replica count as needed.

## Concepts Introduced

### 1. The Problem: Managing Many YAML Files

*   As applications grow, managing individual Kubernetes YAML files becomes cumbersome.
*   Deploying or upgrading requires applying multiple files in the correct order.
*   Customizing deployments for different environments (dev, staging, prod) often involves copying and modifying YAML files, leading to duplication and potential errors.
*   Sharing and versioning application deployments is difficult.

### 2. Helm: The Kubernetes Package Manager

*   **What it is:** Helm helps you define, install, and upgrade even the most complex Kubernetes applications. It packages applications into **Charts**.
*   **Analogy:** Helm is like `apt`, `yum`, or `brew` for Kubernetes. It provides tooling to manage application packages (Charts) instead of individual configuration files.

### 3. Helm Charts: The Spellbook / Application Package

*   **What it is:** A collection of files organized in a specific directory structure that describes a related set of Kubernetes resources. It contains templates for your manifests and default configuration values.
*   **Key Files/Directories:**
    *   `Chart.yaml`: Metadata about the chart (name, version, appVersion).
    *   `values.yaml`: Default configuration values for the chart. These can be overridden during installation/upgrade.
    *   `templates/`: Directory containing the templated Kubernetes manifest files (e.g., `deployment.yaml`, `service.yaml`).
    *   `templates/_helpers.tpl`: Contains reusable template snippets (helpers).
    *   `templates/NOTES.txt`: Text displayed after successful installation.
    *   `.helmignore`: Specifies files to ignore when packaging the chart.
    *   `charts/`: Optional directory for chart dependencies (subcharts).
*   **Analogy:** The chart directory (`hero-registry-chart/`) is the spellbook itself. `Chart.yaml` is the cover title and version. `values.yaml` lists the default magic words (variables). `templates/` holds the actual spell templates, written in a magical language (Go templates + Sprig functions) that allows for customization.

### 4. Helm Templates: Customizable Spells

*   **What they are:** Kubernetes manifest files written with placeholders and logic using the Go template language ([https://pkg.go.dev/text/template](https://pkg.go.dev/text/template)) and functions from the Sprig library ([http://masterminds.github.io/sprig/](http://masterminds.github.io/sprig/)).
*   **How they work:** Helm reads the templates in the `templates/` directory and renders them using values provided from:
    1.  The chart's `values.yaml` file (defaults).
    2.  Values passed via the command line (`--set key=value`).
    3.  Values passed via additional YAML files (`-f my-values.yaml`).
    4.  Built-in Helm objects (`.Release`, `.Chart`, `.Values`, `.Capabilities`).
*   **Example:** In `templates/deployment.yaml`, `{{ .Values.replicaCount }}` is replaced by the value of `replicaCount` from `values.yaml` (or overridden values). `{{ include "hero-registry-chart.fullname" . }}` calls a helper template to generate a resource name.
*   **Analogy:** Templates are like spell scrolls with blanks or variables. `{{ .Values.image.repository }}` is a blank space where you write the specific magic ingredient (image repository URL) before casting the spell. Helpers (`{{ include ... }}`) are like invoking standard magical phrases for common tasks like naming conventions.

### 5. Values (`values.yaml` & Overrides): Customizing the Spell

*   **What they are:** Provide the parameters to customize a chart's templates. Defaults are in `values.yaml`.
*   **Why use them:** Allows users to configure the chart for their specific needs (e.g., image tag, replica count, ingress hostname, resource limits) without modifying the templates directly.
*   **Analogy:** `values.yaml` contains the default ingredients and incantations for the spell. Using `--set` or `-f` is like substituting a different ingredient (e.g., `--set replicaCount=3`) or using an entirely different page of modifications (`-f production-values.yaml`) when casting the spell.

### 6. Releases: Cast Spells / Deployed Instances

*   **What it is:** An instance of a chart running in a Kubernetes cluster. When you run `helm install`, Helm creates a **Release** with a specific name. You can have multiple releases of the same chart (e.g., for different environments or configurations).
*   **Analogy:** A Release is a specific instance of the enchantment cast from the spellbook (Chart). You might cast the "Hero Registry" spell once for testing (`helm install test-registry ./hero-registry-chart`) and again for production (`helm install prod-registry ./hero-registry-chart -f prod-values.yaml`). Each is a separate Release. `helm upgrade` modifies an existing Release, while `helm uninstall` removes it.

## Practical Exercise: Using the Helm Chart

**Prerequisites:**

*   Delete the Kubernetes resources created manually in previous lessons to avoid conflicts with Helm management.
    ```bash
    # Be careful! This deletes the running application.
    kubectl delete ingress hero-registry-ingress -n default
    kubectl delete service hero-registry-service -n default
    kubectl delete deployment hero-registry-deployment -n default
    # Keep the PVC, ConfigMap, Secret as the chart uses existing ones by default
    # kubectl delete pvc hero-registry-data-pvc -n default
    # kubectl delete configmap hero-registry-config -n default
    # kubectl delete secret hero-registry-secret -n default
    # kubectl delete secret hero-registry-tls-secret -n default # Cert-Manager will recreate this
    ```

**Part 1: Configure Chart Values**

1.  **Edit `values.yaml`:** Open `hero-academy/lesson-10-helm/hero-registry-chart/values.yaml`.
2.  **Set Mandatory Values:** You **must** set the `image.repository`. Find the commented-out line and update it with your Harbor details:
    ```yaml
    image:
      repository: harbor.komebacklab.local/your-actual-harbor-project/hero-registry # <-- SET THIS
      pullPolicy: Always
      tag: "" # Uses Chart.appVersion (0.4.0) by default
    ```
3.  **Verify Other Values:** Check that other values match your environment:
    *   `ingress.hosts[0].host`: Should be `hero-registry.komebacklab.local` (or your chosen hostname).
    *   `ingress.tls[0].hosts[0]`: Should match the ingress host.
    *   `ingress.tls[0].secretName`: Should be `hero-registry-tls-secret`.
    *   `ingress.annotations."cert-manager.io/cluster-issuer"`: Should be `komebacklab-ca-issuer`.
    *   `persistence.existingClaim`: Should be `hero-registry-data-pvc`.
    *   `configMapName`: Should be `hero-registry-config`.
    *   `secretName`: Should be `hero-registry-secret`.

**Part 2: Lint and Template (Optional but Recommended)**

1.  **Navigate:** Open a terminal with `helm` and `kubectl` configured. Navigate to the directory containing the chart: `hero-academy/lesson-10-helm/`.
2.  **Lint:** Check the chart for syntax errors and best practice violations:
    ```bash
    helm lint ./hero-registry-chart
    ```
3.  **Template:** Render the templates locally to see the final YAML that Helm *would* apply to the cluster. This is great for debugging templates without actually deploying.
    ```bash
    # Render templates using default values
    helm template my-release ./hero-registry-chart

    # Render templates overriding a value
    helm template my-release ./hero-registry-chart --set replicaCount=2

    # Render templates saving output to a file
    helm template my-release ./hero-registry-chart > rendered-manifests.yaml
    ```
    Inspect the output YAML to ensure it looks correct and uses the values as expected.

**Part 3: Install the Chart**

1.  **Install:** Deploy the chart to your Kubernetes cluster, creating a new release named `hero-registry`.
    ```bash
    helm install hero-registry ./hero-registry-chart --namespace default
    ```
    *   You should see output indicating the release was deployed, followed by the content of `templates/NOTES.txt`.
2.  **Verify:** Check the status of the Helm release and the Kubernetes resources it created.
    ```bash
    helm list -n default # Should show 'hero-registry' with STATUS 'deployed'
    kubectl get deployment -n default # Should show 'hero-registry-hero-registry-chart' (or similar based on fullname template)
    kubectl get service -n default
    kubectl get ingress -n default
    kubectl get pods -n default
    # Check Certificate and Secret were created by Cert-Manager via Ingress
    kubectl get certificate -n default
    kubectl get secret hero-registry-tls-secret -n default
    ```
3.  **Test Access:** Use the URL provided in the `helm install` NOTES (e.g., `https://hero-registry.komebacklab.local`) to access the application in your browser. Everything should work as before.

**Part 4: Upgrade the Chart (Example)**

1.  **Modify `values.yaml`:** Let's say you want to change the greeting message. You could modify the `hero-registry-config` ConfigMap directly, OR you could modify the chart to manage the ConfigMap itself (more advanced). For a simpler example, let's just change the image tag (pretend we pushed `lesson-10` tag). Edit `values.yaml`:
    ```yaml
    image:
      repository: harbor.komebacklab.local/your-actual-harbor-project/hero-registry
      pullPolicy: Always
      tag: "lesson-10" # Change the tag
    ```
2.  **Upgrade:** Apply the changes to the existing release.
    ```bash
    helm upgrade hero-registry ./hero-registry-chart --namespace default
    ```
3.  **Verify:** Check the deployment rollout and inspect the Pod to see it's using the new image tag.
    ```bash
    kubectl rollout status deployment/hero-registry-hero-registry-chart -n default
    kubectl describe pod -l app.kubernetes.io/instance=hero-registry -n default | grep Image:
    ```

**Part 5: Uninstall the Chart**

1.  **Uninstall:** Remove the release and all associated Kubernetes resources created by Helm.
    ```bash
    helm uninstall hero-registry --namespace default
    ```
2.  **Verify:** Check that the Deployment, Service, Ingress, etc., are gone.
    ```bash
    kubectl get deployment,service,ingress,pod -l app.kubernetes.io/instance=hero-registry -n default
    # Should show "No resources found"
    ```
    *Note: Helm typically does *not* delete PVCs or Secrets created outside the chart (like our existing ones) or Secrets created *by* the chart unless specific annotations are used.*

## Problem-Solving Framework: Helm Issues

1.  **Identify the Symptom:** `helm lint` errors? `helm template` errors or incorrect output? `helm install/upgrade` fails? Resources not created/updated as expected? Incorrect values used in deployed resources?
2.  **Locate the Problem Area:**
    *   *`helm lint` errors:* Syntax errors in `Chart.yaml`, `values.yaml`, or templates. Chart structure issues. Deprecated API versions used in templates.
    *   *`helm template` / `helm install/upgrade` Template Errors:* Go template syntax errors in `templates/*.yaml` or `_helpers.tpl`. Referencing non-existent values (`.Values.some.nonexistent.key`). Incorrect function usage (e.g., wrong arguments for `include`). Logic errors in conditionals (`if`/`else`). YAML indentation errors *within* the templates. Use `helm template --debug` or `helm install --dry-run --debug` to get more detailed error messages.
    *   *`helm install/upgrade` Fails (Post-Template Rendering):* The rendered YAML is valid according to Helm, but Kubernetes rejected it. This usually means the generated Kubernetes manifest is invalid (e.g., incorrect `apiVersion`, `kind`, missing required fields, invalid label selectors, resource already exists with immutable fields changed). Examine the error message from Kubernetes provided by Helm. Use `helm template` to inspect the exact YAML being sent.
    *   *Resources Not Created/Updated Correctly:* Check Helm status (`helm status <release-name>`). Check Kubernetes events (`kubectl get events -n <namespace>`). Did the template logic (`if .Values.ingress.enabled`) prevent resource creation? Did the upgrade fail mid-way? Is the resource name different than expected (check `_helpers.tpl` and fullname/name overrides)?
    *   *Incorrect Values Used:* Did you override values correctly (`--set`, `-f`)? Check precedence rules (command line overrides files, which override `values.yaml`). Is there a typo in the key path (`--set image.repo=...` instead of `image.repository=...`)? Use `helm get values <release-name>` to see the computed values used for the release.

3.  **Consult the Blueprints/Manuals:**
    *   *Helm Documentation:* ([https://helm.sh/docs/](https://helm.sh/docs/)) Covers chart structure, templating functions, commands.
    *   *Sprig Function Documentation:* ([http://masterminds.github.io/sprig/](http://masterminds.github.io/sprig/)) Lists available template functions.
    *   *`Chart.yaml`, `values.yaml`, `templates/*` files:* Review syntax, logic, value references.
    *   *`helm lint`, `helm template --debug`, `helm install --dry-run --debug` output.*
    *   *`helm status <release-name>`, `helm get manifest <release-name>`, `helm get values <release-name>`.*
    *   *Kubernetes resource definitions (`kubectl explain <resource-type>`).*

4.  **Isolate and Test:**
    *   Comment out sections of templates or `values.yaml` to isolate the problematic part.
    *   Use `helm template` frequently to check the output of specific template sections.
    *   Add `{{ fail "My debug message" }}` in templates to stop rendering at a certain point and print a message.
    *   Test individual template functions using simple values.

5.  **Verify Assumptions:** Did you assume a value existed when it didn't (use `default` function)? Did you assume the correct context (`.`) within includes or ranges? Did you assume correct YAML indentation would be generated by the template?

**You've mastered the Ancient One's Spellbook! Packaging your application as a Helm chart makes deployments repeatable, configurable, and easier to manage. Next, we'll explore managing stateful applications like databases.**
