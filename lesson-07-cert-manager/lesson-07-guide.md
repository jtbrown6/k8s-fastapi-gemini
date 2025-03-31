# Lesson 7: Odin's Blessing (Cert-Manager & Custom CA)

**Objective:** Secure the external access to our "Hero Registry" application using HTTPS/TLS. We will install Cert-Manager in the cluster and configure it to automatically issue TLS certificates for our Ingress hostname (`hero-registry.komebacklab.local`) using your existing custom Certificate Authority (CA).

**Analogy:** The Bifrost (Ingress) is open, but the connection is currently unencrypted (HTTP), like shouting across the bridge – anyone nearby could potentially listen in. We need Odin's Blessing (TLS encryption) to create a secure, private communication channel. Cert-Manager acts like Odin's ravens, automatically handling the process of requesting and applying the official Asgardian seal of approval (TLS certificate signed by your CA) to the Bifrost connection whenever needed.

## Concepts Introduced

### 1. TLS/HTTPS: The Secure Channel

*   **What it is:** Transport Layer Security (TLS) is the standard protocol for encrypting communication between a client (like your browser) and a server (like our application via the Ingress controller). HTTPS is simply HTTP running over a TLS-secured connection.
*   **Why use it:** Protects data privacy (prevents eavesdropping) and integrity (prevents tampering) and helps verify the server's identity. Essential for any web application handling potentially sensitive data or logins.
*   **Analogy:** TLS creates a secure, encrypted subspace tunnel between the visitor (browser) and Heimdall (Ingress controller). Only the sender and receiver can understand the messages passed through it.

### 2. Certificate Authority (CA): Odin's Authority

*   **What it is:** An entity trusted to sign and issue digital certificates. In this case, it's your own CA running on Windows Server for the `komebacklab.local` domain. Browsers or systems need to trust this CA to validate the certificates it issues.
*   **Analogy:** The CA is like Odin himself, the ultimate authority in Asgard (`komebacklab.local`). His signature (CA signature) on a document (TLS certificate) verifies its authenticity within his realm. For external visitors (browsers) to trust this signature, they must first trust Odin (have the CA's root certificate installed).

### 3. TLS Certificates: The Official Seal

*   **What they are:** Digital files containing a public key, information about the identity (e.g., hostname like `hero-registry.komebacklab.local`), and the digital signature of a CA. The client uses the public key to encrypt data that only the server (holding the corresponding private key) can decrypt. The client also verifies the CA's signature using the CA's public certificate.
*   **Analogy:** A TLS certificate is the official, magically sealed scroll issued by Odin (CA) specifically for the `hero-registry.komebacklab.local` Bifrost route. It contains the public key (a magic rune for encryption) and Odin's signature, proving its legitimacy within Asgard.

### 4. Cert-Manager: Odin's Ravens (Automated Certificate Management)

*   **What it is:** A popular Kubernetes add-on that automates the management and issuance of TLS certificates. It watches for Ingress resources (and other custom resources) and interacts with different certificate issuers (like Let's Encrypt, HashiCorp Vault, or a custom CA) to obtain and renew certificates automatically.
*   **Analogy:** Cert-Manager is like Odin's ravens, Huginn and Muninn. They constantly watch over Asgard (the cluster) for requests for official seals (certificate requests triggered by Ingress annotations/TLS sections). When they see a request, they fly to Odin (the CA Issuer), get the seal (certificate), bring it back, and ensure Heimdall (Ingress controller) uses it correctly, even replacing it before it expires.

### 5. Issuer / ClusterIssuer: Defining the Certificate Source

*   **What they are:** Kubernetes Custom Resources (CRDs) defined by Cert-Manager that represent certificate authorities capable of signing certificates.
    *   `Issuer`: Namespaced - can only issue certificates for resources within its own namespace.
    *   `ClusterIssuer`: Cluster-wide - can issue certificates for resources in any namespace. (We are using this).
*   **How we use it:** We define a `ClusterIssuer` (`clusterissuer.yaml`) that tells Cert-Manager how to use your custom CA. It references a Kubernetes Secret containing your CA's certificate and private key.
*   **Analogy:** The `ClusterIssuer` resource is the official decree establishing Odin (`komebacklab-ca-issuer`) as a recognized authority for issuing seals throughout all of Asgard (the cluster) and specifying where his signing key is kept (`secretName: komebacklab-ca-key-pair`).

### 6. Ingress TLS Configuration & Annotations

*   **How it works:** We modify the Ingress resource (`ingress.yaml`):
    *   Add a `tls:` section specifying the hostname(s) to secure and the name of the Secret where Cert-Manager should store the resulting certificate (`secretName: hero-registry-tls-secret`).
    *   Add the `cert-manager.io/cluster-issuer: komebacklab-ca-issuer` annotation to tell Cert-Manager to act on this Ingress using our specific ClusterIssuer.
*   **The Flow:**
    1.  You apply the updated Ingress.
    2.  Cert-Manager sees the `tls:` section and the annotation.
    3.  It creates a `CertificateRequest` based on the Ingress details.
    4.  It uses the referenced `ClusterIssuer` (`komebacklab-ca-issuer`).
    5.  The ClusterIssuer uses the CA key/cert from the `komebacklab-ca-key-pair` Secret to sign the request.
    6.  Cert-Manager receives the signed certificate and stores it (along with the key) in the `hero-registry-tls-secret`.
    7.  The Ingress Controller (Traefik) detects the `hero-registry-tls-secret` referenced in the Ingress's `tls:` section and automatically loads it to serve HTTPS traffic for `hero-registry.komebacklab.local`.

## Practical Exercise: Enabling HTTPS with Cert-Manager

**Part 1: Install Cert-Manager**

1.  **Install using Helm (Recommended) or Manifests:** Follow the official Cert-Manager installation documentation: [https://cert-manager.io/docs/installation/](https://cert-manager.io/docs/installation/)
    *   **Helm:** This is generally the easiest way.
        ```bash
        # Add the Jetstack Helm repository
        helm repo add jetstack https://charts.jetstack.io
        helm repo update

        # Install the cert-manager Helm chart (CRDs are installed automatically)
        # It's good practice to install it into its own namespace
        helm install cert-manager jetstack/cert-manager \
          --namespace cert-manager \
          --create-namespace \
          --version v1.14.5 # Use a specific, recent version
          # --set installCRDs=true # Usually not needed with recent Helm versions
        ```
    *   **Manifests:** Alternatively, download and apply the static manifests:
        ```bash
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.5/cert-manager.yaml
        ```
2.  **Verify Installation:** Wait a few minutes for the Cert-Manager pods to start in the `cert-manager` namespace.
    ```bash
    kubectl get pods --namespace cert-manager
    # Look for pods like cert-manager-xxx, cert-manager-cainjector-xxx, cert-manager-webhook-xxx to be Running.
    ```

**Part 2: Create CA Secret**

1.  **Get CA Files:** Ensure you have the CA's certificate file (e.g., `ca.crt`) and its private key file (e.g., `ca.key`) accessible on the machine where you run `kubectl`. **Protect the private key file carefully!**
2.  **Create Kubernetes Secret:** Create the secret that the `ClusterIssuer` will reference. It *must* contain keys named `tls.crt` and `tls.key`. Cert-Manager needs to be able to read this secret. Often, it's placed in the `cert-manager` namespace or `kube-system`. Let's use `cert-manager`.
    ```bash
    kubectl create secret tls komebacklab-ca-key-pair \
      --cert=/path/to/your/ca.crt \
      --key=/path/to/your/ca.key \
      --namespace=cert-manager # Place secret where cert-manager can access it
    ```
    *   Replace `/path/to/your/ca.crt` and `/path/to/your/ca.key` with the actual paths.
    *   Verify: `kubectl get secret komebacklab-ca-key-pair --namespace=cert-manager`

**Part 3: Apply ClusterIssuer and Updated Ingress**

1.  **Navigate:** Open a terminal with `kubectl` configured and navigate to the `hero-academy/lesson-07-cert-manager` directory.
2.  **Apply ClusterIssuer:** Create the issuer resource.
    ```bash
    kubectl apply -f clusterissuer.yaml
    ```
    *   Verify: Wait a moment and check its status. It should become `Ready`.
        ```bash
        kubectl get clusterissuer komebacklab-ca-issuer
        kubectl describe clusterissuer komebacklab-ca-issuer # Look for Ready condition
        ```
3.  **Apply Updated Ingress:** Apply the modified Ingress file (`lesson-07-cert-manager/ingress.yaml`).
    ```bash
    kubectl apply -f ingress.yaml --namespace=default
    ```

**Part 4: Verify Certificate Issuance and HTTPS**

1.  **Check Certificate Resource:** Cert-Manager should automatically create a `Certificate` resource based on the Ingress.
    ```bash
    kubectl get certificate --namespace=default
    # Look for 'hero-registry-tls-secret', should eventually show READY=True
    ```
2.  **Check CertificateRequest:** You might briefly see a `CertificateRequest` resource.
    ```bash
    kubectl get certificaterequest --namespace=default
    ```
3.  **Check Secret:** Verify that Cert-Manager created the target secret specified in the Ingress's `tls` section.
    ```bash
    kubectl get secret hero-registry-tls-secret --namespace=default
    # It should exist now.
    ```
4.  **Describe Ingress:** Check if the Ingress controller (Traefik) recognized the TLS configuration.
    ```bash
    kubectl describe ingress hero-registry-ingress --namespace=default
    # Look for TLS section referencing 'hero-registry-tls-secret' for the host.
    # Check Events for any errors related to TLS or the secret.
    ```
5.  **Test HTTPS Access:**
    *   **Trust Your CA:** Ensure the client machine you are testing from (e.g., your laptop) **trusts your custom CA**. You usually need to import the `ca.crt` file into your operating system's or browser's trust store. If you don't do this, you'll get certificate warnings in your browser.
    *   **Access via Browser:** Open your browser and navigate to:
        `https://hero-registry.komebacklab.local` (Note the **HTTPS**)
        You should see the application, and the browser should indicate a secure connection (e.g., a padlock icon) without warnings (if your CA is trusted).
    *   **Access via `curl`:**
        ```bash
        # If your system trusts the CA:
        curl https://hero-registry.komebacklab.local/heroes

        # If your system DOES NOT trust the CA, you might need -k (INSECURE! Only for testing):
        # curl -k https://hero-registry.komebacklab.local/heroes

        # To test with specific CA cert:
        # curl --cacert /path/to/your/ca.crt https://hero-registry.komebacklab.local/heroes
        ```

## Problem-Solving Framework: Cert-Manager & TLS Issues

1.  **Identify the Symptom:** Cert-Manager pods not running? ClusterIssuer not Ready? Certificate resource stuck in `Pending` or shows `False` for Ready? Secret `hero-registry-tls-secret` not created? Browser shows certificate warning (invalid CA, hostname mismatch, expired)? Browser shows connection refused/timeout for HTTPS? Ingress controller logs show TLS errors?
2.  **Locate the Problem Area:**
    *   *Cert-Manager Pods Not Running:* Installation issue. Check `kubectl get pods -n cert-manager`, `kubectl describe pod -n cert-manager <pod-name>`, `kubectl logs -n cert-manager <pod-name>`. RBAC issues? Network issues pulling images?
    *   *ClusterIssuer Not Ready:*
        *   Check `kubectl describe clusterissuer <name>`. Look at Status and Events.
        *   Did you create the CA secret (`komebacklab-ca-key-pair`)?
        *   Is it in the correct namespace (`cert-manager`)?
        *   Does it contain the correct keys (`tls.crt`, `tls.key`)? (`kubectl get secret -n cert-manager <secret-name> -o yaml`)
        *   Are the cert/key files valid?
        *   Does Cert-Manager have RBAC permissions to read Secrets in that namespace? (Usually configured by default installation).
    *   *Certificate Stuck Pending / Not Ready:*
        *   Check `kubectl describe certificate -n default hero-registry-tls-secret`. Look at Status and Events. It often points to an issue with the Issuer or the CertificateRequest.
        *   Check `kubectl get certificaterequest -n default`. Describe any relevant requests. Status/Events might show errors from the Issuer (e.g., failed to sign using the CA key).
        *   Is the `cert-manager.io/cluster-issuer` annotation on the Ingress correct?
        *   Is the ClusterIssuer Ready?
    *   *Secret `hero-registry-tls-secret` Not Created:* Certificate issuance failed. See previous point.
    *   *Browser Certificate Warnings:*
        *   *Untrusted CA:* The browser/OS testing from does not trust your custom `komebacklab.local` CA. Import the `ca.crt` into the trust store.
        *   *Hostname Mismatch:* The hostname in the browser URL (`hero-registry.komebacklab.local`) does not match any hostname listed *inside* the certificate's Subject Alternative Names (SANs). Ensure the `tls.hosts` list in `ingress.yaml` is correct. Check the issued certificate details: `kubectl get secret -n default hero-registry-tls-secret -o jsonpath='{.data.tls\.crt}' | base64 --decode | openssl x509 -text -noout` (Look for SANs).
        *   *Expired Certificate:* Cert-Manager should handle renewals, but check the certificate's validity dates (using the `openssl` command above). Check Cert-Manager logs for renewal errors.
    *   *HTTPS Connection Refused/Timeout:*
        *   Is the Ingress controller (Traefik) configured to listen on the HTTPS port (usually 443)? Check the Traefik service (`kubectl get svc -n kube-system traefik`).
        *   Are there any firewalls blocking port 443 between your client and the K3s nodes/LB?
        *   Did you add the Traefik annotations (`router.entrypoints: websecure`, `router.tls: "true"`) to the Ingress? Check Traefik logs for errors loading the router/TLS config.
        *   Does the `hero-registry-tls-secret` actually exist and contain valid data?

3.  **Consult the Blueprints/Manuals:**
    *   *`clusterissuer.yaml`:* Check `apiVersion`, `kind`, `metadata.name`, `spec.ca.secretName`.
    *   *`ingress.yaml`:* Check annotations (`cert-manager.io/cluster-issuer`, Traefik annotations), `spec.tls.hosts`, `spec.tls.secretName`.
    *   *CA Secret (`komebacklab-ca-key-pair`):* Check namespace, keys (`tls.crt`, `tls.key`), validity of cert/key.
    *   *Generated Cert Secret (`hero-registry-tls-secret`):* Check if it exists, decode/inspect the certificate inside.
    *   *Cert-Manager Pod Logs (`kubectl logs -n cert-manager <pod-name>`):* Essential for debugging issuance problems.
    *   *Ingress Controller Logs (`kubectl logs -n kube-system <traefik-pod-name>`):* Essential for debugging TLS termination/routing problems.
    *   *`kubectl describe clusterissuer|certificate|certificaterequest|ingress|secret`*

4.  **Isolate and Test:**
    *   Try creating a simple `Certificate` resource manually, referencing the `ClusterIssuer`. Does that get issued correctly?
    *   Temporarily remove the `tls:` section and annotations from the Ingress. Does HTTP still work?
    *   Use `openssl s_client -connect hero-registry.komebacklab.local:443 -servername hero-registry.komebacklab.local` to test the TLS connection and view the certificate presented by the server.

5.  **Verify Assumptions:** Did you assume Cert-Manager was installed correctly? Did you assume the CA secret was created correctly in the right namespace with the right keys? Did you assume the ClusterIssuer was Ready? Did you assume your client trusts the CA? Did you assume the Ingress controller was configured for HTTPS?

**Odin's Blessing is bestowed! Your application is now served securely over HTTPS using automatically managed certificates from your own CA. Next, we delve into S.H.I.E.L.D. Clearance with Kubernetes RBAC.**
