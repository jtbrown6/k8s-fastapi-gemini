# Lesson 5: The Power Stone (Persistent Storage)

**Objective:** Provide persistent storage to our application so that hero data survives Pod restarts and redeployments. We'll use Kubernetes PersistentVolumes (PVs), PersistentVolumeClaims (PVCs), and your existing NFS StorageClass.

**Analogy:** Our heroes (Pods) are currently ephemeral. If Iron Man's suit (Pod) is destroyed and replaced, his memory banks (application data) are wiped clean. We need to give him access to the Power Stone (a Persistent Volume) – an external, durable source of power/memory that exists independently of the suit itself. When a new suit comes online, it reconnects to the Power Stone to retrieve its persistent data.

## Concepts Introduced

### 1. The Problem: Ephemeral Pods

*   Containers (and the Pods that run them) are designed to be stateless and ephemeral. Their local filesystems are temporary.
*   When a Pod crashes or is deleted (e.g., during a deployment update), its filesystem is destroyed. Any data written directly inside the container is lost.
*   Our hero list in Lesson 4 was still only stored in memory (loaded from defaults if the file didn't exist), so restarting the Pod would reset the list.

### 2. Volumes: Attachable Storage Devices

*   **What they are:** A directory, possibly with some data in it, which is accessible to the Containers in a Pod. How that directory comes to be, the medium that backs it, and its contents are determined by the volume type used.
*   **Analogy:** Think of Volumes as different types of attachable storage devices or power sources for the Iron Man suit – like an external battery pack (`emptyDir`), a connection to the main Stark Tower power grid (network storage like NFS, Ceph), or a specific classified data chip (`secret`, `configMap`). The key is that the *lifetime* of the Volume can be independent of the Pod.

### 3. PersistentVolumes (PVs): The Power Stone Itself

*   **What they are:** A piece of storage in the cluster that has been provisioned by an administrator or dynamically provisioned using StorageClasses. It's a cluster resource, just like a Node. PVs have a lifecycle independent of any individual Pod that uses the PV.
*   **Analogy:** A PersistentVolume is like one of the Infinity Stones (e.g., the Power Stone) existing within the universe (the cluster). It represents a real piece of available storage (like a specific NFS export or a cloud disk) waiting to be claimed. It has properties like capacity and access modes. You usually don't create PVs directly when using dynamic provisioning.

### 4. StorageClasses: Infinity Stone Types / Provisioners

*   **What they are:** Describe the "classes" of storage offered. Different classes might map to quality-of-service levels, backup policies, or arbitrary policies determined by the cluster administrator. Each StorageClass has a provisioner (like your `nfs-subdir-external-provisioner`) that determines what volume plugin is used for provisioning PVs.
*   **Analogy:** A StorageClass defines the *type* of Infinity Stone available (Power Stone, Space Stone) and specifies the entity responsible for creating it when requested (e.g., The Collector for Power Stones, Asgard for Space Stones). Your `nfs-subdir-external-provisioner` is the entity responsible for creating NFS-based storage when requested via its associated StorageClass. You find the name using `kubectl get storageclass`.

### 5. PersistentVolumeClaims (PVCs): Requesting the Power Stone

*   **What they are:** A request for storage by a user (or application/Pod). It's similar to a Pod consuming Node resources; PVCs consume PV resources. Pods request specific sizes and access modes (e.g., ReadWriteOnce, ReadWriteMany). When a PVC is created requesting a specific StorageClass, the provisioner automatically creates a matching PV and binds them together.
*   **Analogy:** A PersistentVolumeClaim is the official request form submitted by Tony Stark to S.H.I.E.L.D. or The Collector, saying "I need access to a Power Stone (`storageClassName`) of at least 1 Gigabyte capacity (`resources.requests.storage`) that I can read and write (`accessModes`)." Defined in `pvc.yaml`.

### 6. Volume Mounts: Connecting the Stone to the Gauntlet

*   **What they are:** Defined within the Pod/Deployment specification, `volumeMounts` tell the container *where* inside its filesystem the requested Volume (defined in the Pod's `volumes` section, which references the PVC) should be made accessible.
*   **Analogy:** Once Tony Stark's request (PVC) for the Power Stone (PV) is approved and granted, the `volumeMounts` section in the suit's blueprint (Deployment) specifies exactly which slot in the Infinity Gauntlet (`mountPath: /data`) the Power Stone (`name: hero-data-storage`) should be connected to.

## Practical Exercise: Adding Persistent Storage

**Part 1: Update Code & Image (CI/CD)**

1.  **Update Local Code:**
    *   Replace the content of `hero-academy/lesson-01-recruit/main.py` with the content from `hero-academy/lesson-05-storage/main.py`.
    *   *(Optional but Recommended)* Update the image tag in your `.gitlab-ci.yml` (e.g., `hero-registry:lesson-05`) and update the `image:` line in `lesson-05-storage/deployment.yaml` accordingly. We'll assume you stick with `:latest`.
2.  **Commit & Push:** Add the changes to Git and push to GitLab.
    ```bash
    # Assuming you copied the new main.py over the old one
    git add hero-academy/lesson-01-recruit/main.py
    # Add the new lesson 5 manifests
    git add hero-academy/lesson-05-storage/
    git commit -m "Feat: Update app for Lesson 5 (Storage) and add manifests"
    git push
    ```
3.  **Monitor CI/CD:** Ensure the pipeline builds the new image (with file I/O logic) and pushes it to Harbor.

**Part 2: Apply Kubernetes Manifests**

1.  **Identify StorageClass:** Find the name of the StorageClass associated with your NFS provisioner.
    ```bash
    kubectl get storageclass
    ```
    Note the exact name (e.g., `nfs-client`, `managed-nfs-storage`).

2.  **Update PVC Manifest:** Edit `hero-academy/lesson-05-storage/pvc.yaml` and replace `your-nfs-storageclass-name` with the actual name you found. Also, ensure `accessModes` (e.g., `ReadWriteMany`) is appropriate for your NFS setup.
    ```yaml
    # In pvc.yaml
    spec:
      storageClassName: actual-nfs-storageclass-name # <-- CHANGE THIS
      accessModes:
        - ReadWriteMany # Or RWO if needed
      resources:
        requests:
          storage: 1Gi
    ```

3.  **Navigate:** Open a terminal with `kubectl` configured and navigate to the `hero-academy/lesson-05-storage` directory.

4.  **Apply PVC:** Create the PersistentVolumeClaim. Kubernetes (via your NFS provisioner) should now dynamically create a corresponding PersistentVolume and bind them together.
    ```bash
    kubectl apply -f pvc.yaml --namespace=default
    ```
    *   Verify: Check the PVC status. It should become `Bound`.
        ```bash
        kubectl get pvc hero-registry-data-pvc --namespace=default
        # STATUS should change from Pending to Bound
        ```
    *   *(Optional)* Check the dynamically created PV:
        ```bash
        kubectl get pv
        # Look for a PV bound to default/hero-registry-data-pvc
        ```

5.  **Apply Updated Deployment:** Apply the modified deployment file (`lesson-05-storage/deployment.yaml`), which now includes the `volumes` and `volumeMounts` sections referencing the PVC. Kubernetes will perform a rolling update.
    ```bash
    # Make sure the image tag and project name in deployment.yaml are correct!
    kubectl apply -f deployment.yaml --namespace=default
    ```

**Part 3: Verify Persistence**

1.  **Check Deployment Rollout:** Ensure the new Pod (replica count is now 1) is created and running.
    ```bash
    kubectl rollout status deployment/hero-registry-deployment --namespace=default
    kubectl get pods --selector=app=hero-registry --namespace=default
    ```
    *   Get the name of the new Pod:
        ```bash
        POD_NAME=$(kubectl get pods --selector=app=hero-registry -n default -o jsonpath='{.items[0].metadata.name}')
        echo "Using Pod: $POD_NAME"
        ```

2.  **Check Logs:** View the logs to see if the application loaded/created the `heroes.json` file in `/data`.
    ```bash
    kubectl logs $POD_NAME --namespace=default
    # Look for "Loaded X heroes from /data/heroes.json" or "Hero file not found. Initializing..."
    ```

3.  **Add a Hero:** Use `port-forward` and `curl` (or your browser) to add a new hero via the POST endpoint.
    ```bash
    # Start port-forward in one terminal
    kubectl port-forward service/hero-registry-service 8080:80 --namespace=default

    # In another terminal, send a POST request (replace API key if you enabled it)
    curl -X POST http://localhost:8080/heroes \
      -H "Content-Type: application/json" \
      -H "X-API-Key: s3cr3t-ap1-k3y" \
      -d '{"name": "Spider-Man", "secret_identity": "Peter Parker"}'

    # Check the response, should be the new hero with an ID (e.g., 4)
    ```

4.  **Verify Hero Added:** Get the list of heroes.
    ```bash
    curl -H "X-API-Key: s3cr3t-ap1-k3y" http://localhost:8080/heroes
    # You should see Spider-Man in the list now.
    ```
    *   Stop the port-forward (`Ctrl+C`).

5.  **Simulate Pod Restart:** Delete the running Pod. The Deployment will automatically create a new one.
    ```bash
    echo "Deleting Pod: $POD_NAME"
    kubectl delete pod $POD_NAME --namespace=default
    ```
    *   Wait for the new Pod to start:
        ```bash
        kubectl get pods --selector=app=hero-registry --namespace=default -w # Use -w to watch changes
        # Wait until the new pod shows STATUS Running, then press Ctrl+C
        ```
    *   Get the name of the *new* Pod:
        ```bash
        NEW_POD_NAME=$(kubectl get pods --selector=app=hero-registry -n default -o jsonpath='{.items[0].metadata.name}')
        echo "New Pod: $NEW_POD_NAME"
        ```

6.  **Verify Data Persistence:** Check the logs of the *new* Pod and then check the hero list again.
    ```bash
    kubectl logs $NEW_POD_NAME --namespace=default
    # Should show "Loaded 4 heroes from /data/heroes.json" (or similar count)

    # Start port-forward again
    kubectl port-forward service/hero-registry-service 8080:80 --namespace=default

    # Check heroes list in another terminal
    curl -H "X-API-Key: s3cr3t-ap1-k3y" http://localhost:8080/heroes
    # Spider-Man should STILL be in the list! The data persisted on the NFS volume.
    ```
    *   Stop the port-forward.

## Problem-Solving Framework: Storage Issues

1.  **Identify the Symptom:** PVC stuck in `Pending`? Pod stuck in `Pending` or `ContainerCreating` (with volume mount errors)? Application logs show errors reading/writing to the mount path (`/data`)? Data not persisting after Pod restart?
2.  **Locate the Problem Area:**
    *   *PVC `Pending`:*
        *   Is the `storageClassName` in `pvc.yaml` correct and does it exist (`kubectl get sc`)?
        *   Is the storage provisioner (NFS subdir provisioner) running correctly? Check its logs (`kubectl logs -n <namespace-of-provisioner> <provisioner-pod-name>`).
        *   Does the provisioner have the necessary permissions to create directories on the NFS share?
        *   Are the `accessModes` in the PVC compatible with what the StorageClass/PV supports?
    *   *Pod `Pending` / `ContainerCreating` (Volume Errors):*
        *   Check `kubectl describe pod <pod-name> -n <namespace>`. Look for Events like `FailedMount`.
        *   Is the PVC `Bound`? If it's still `Pending`, the Pod can't start.
        *   Is the `persistentVolumeClaim.claimName` in the Deployment's `volumes` section spelled correctly and matches the PVC name?
        *   Are there Node-level issues mounting the underlying storage (NFS)? Check K3s agent logs on the worker node where the Pod is scheduled.
    *   *Application Errors Reading/Writing to Mount Path (`/data`):*
        *   Permissions Issue: Does the user ID the container runs as have permission to write to the directory created by the NFS provisioner on the NFS share? Sometimes you need to configure `fsGroup` in the Pod's `securityContext` or ensure the NFS export has appropriate permissions (e.g., `anonuid`/`anongid`).
        *   Incorrect `mountPath`: Is the path in `volumeMounts` (`/data`) the same path the application (`main.py`) is trying to use (`DATA_DIR = "/data"`)?
        *   Volume Not Mounted: Did the mount actually fail silently? (Check `describe pod` events).
    *   *Data Not Persisting:*
        *   Is the application *actually* writing data to the correct file (`/data/heroes.json`)? Check logs, double-check file paths in code.
        *   Is the volume mount read-only (`readOnly: true` in `volumeMounts`) when it shouldn't be? (Ours is read-write by default).
        *   Are you sure you're checking the data *after* the Pod has fully restarted and re-read the file?

3.  **Consult the Blueprints/Manuals:**
    *   *`pvc.yaml`:* Check `storageClassName`, `accessModes`, `resources.requests.storage`.
    *   *`deployment.yaml`:* Check `volumes.persistentVolumeClaim.claimName`, `volumeMounts.name`, `volumeMounts.mountPath`. Check `replicas` count (relevant for RWX/RWO).
    *   *`main.py`:* Check the `DATA_DIR` and `HERO_FILE` paths. Check file I/O logic.
    *   *`kubectl describe pvc <pvc-name>` / `kubectl describe pv <pv-name>`:* Shows binding status, events.
    *   *`kubectl describe pod <pod-name>`:* Shows volume mount status, events.
    *   *Storage Provisioner Logs:* Crucial for PVC `Pending` issues.
    *   *NFS Server Logs/Configuration:* Check export permissions.

4.  **Isolate and Test:**
    *   Can you manually create a file in the mount path from inside the Pod? (`kubectl exec <pod-name> -- touch /data/test.txt`)
    *   Try a simpler volume type like `emptyDir` first. Does the app write data correctly to that (though it won't persist Pod restarts)? This isolates storage backend issues.
    *   Simplify the application code to just write "hello" to a file in `/data`.

5.  **Verify Assumptions:** Did you assume the StorageClass name was correct? Did you assume the access modes matched? Did you assume the container user had write permissions on the NFS mount? Did you assume the mount path in the Deployment matched the path in the code?

**Success! Your application now wields the Power Stone – its data persists across restarts, stored safely on your NFS share. Next, we'll open the Bifrost and allow external access using Ingress.**
