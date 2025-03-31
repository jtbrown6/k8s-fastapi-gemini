# Lesson 8: S.H.I.E.L.D. Clearance (RBAC & Auth)

**Objective:** Understand Kubernetes Role-Based Access Control (RBAC) and how to define permissions using Roles and RoleBindings to control what users or processes can do within the cluster. Discuss patterns for integrating external authentication systems like Active Directory.

**Analogy:** Not everyone in S.H.I.E.L.D. has access to everything. Director Fury has Level 10 clearance, while a new recruit might only have Level 1. RBAC is the system S.H.I.E.L.D. uses to define these clearance levels (Roles/ClusterRoles) and assign them to specific agents (Users), teams (Groups), or automated systems (ServiceAccounts) for specific departments (Namespaces) or the entire Helicarrier (Cluster).

## Concepts Introduced

### 1. Authentication (AuthN) vs. Authorization (AuthZ)

*   **Authentication (Who are you?):** The process of verifying the identity of a user, process, or device. Kubernetes itself *does not* handle user creation or authentication directly (except for ServiceAccounts). It relies on external methods like client certificates, bearer tokens (e.g., from OIDC providers like Keycloak linked to AD), or static password files (less common). K3s often uses client certificates for the initial `admin` user.
*   **Authorization (What are you allowed to do?):** The process of determining if an *authenticated* subject (user, group, service account) has permission to perform a specific action (verb) on a specific resource (e.g., Pods, Services) in a specific scope (namespace or cluster-wide). **Kubernetes RBAC is primarily focused on Authorization.**
*   **Analogy:** Authentication is like showing your S.H.I.E.L.D. ID badge at the checkpoint to prove you are Agent Coulson. Authorization is the system checking if Agent Coulson's clearance level allows him to enter the restricted R&D lab he's trying to access.

### 2. Subjects: Who is Acting?

*   RBAC rules grant permissions to **subjects**. There are three kinds:
    *   **User:** Represents a human user. Users are not managed by Kubernetes objects; they are assumed to be managed externally (e.g., Active Directory, certificates). The name used in RBAC bindings (`name: jane`) must match the username provided during authentication.
    *   **Group:** Represents a collection of users. Like Users, Groups are not managed by Kubernetes objects and rely on the authentication mechanism to provide group information for a user.
    *   **ServiceAccount:** Represents an identity for processes running *inside* Pods within the cluster. ServiceAccounts *are* Kubernetes objects, managed by the API. They are often used to grant permissions to applications that need to interact with the Kubernetes API (e.g., CI/CD tools running in-cluster, custom controllers).
*   **Analogy:** Subjects are the agents (Users), teams (Groups), or drones/robots (ServiceAccounts) trying to perform actions.

### 3. Roles & ClusterRoles: Defining Permissions (Clearance Levels)

*   **Role:** Contains rules that represent a set of permissions **within a specific namespace**. A Role defines *what* actions (`verbs`) can be performed on *which* resources (`resources`) within that namespace. Defined in `pod-reader-role.yaml`.
*   **ClusterRole:** Similar to a Role, but the permissions are **cluster-wide**. ClusterRoles can grant access to:
    *   Cluster-scoped resources (like Nodes, PersistentVolumes, ClusterRoles themselves).
    *   Namespaced resources (like Pods, Services) across *all* namespaces.
    *   Non-resource endpoints (like `/healthz`).
*   **Analogy:** A `Role` is like a departmental clearance level (e.g., "R&D Lab Access - Level 4"). A `ClusterRole` is like a Helicarrier-wide clearance (e.g., "Command Deck Access - Level 8" or "Global Asset Management - Level 7").

### 4. RoleBindings & ClusterRoleBindings: Assigning Permissions

*   **RoleBinding:** Grants the permissions defined in a `Role` to a set of subjects (Users, Groups, or ServiceAccounts) **within a specific namespace**. It links a Role to subjects for that namespace only. Defined in `jane-read-pods-binding.yaml`.
*   **ClusterRoleBinding:** Grants the permissions defined in a `ClusterRole` to a set of subjects **across the entire cluster**. It can grant cluster-wide access or access to resources in all namespaces, depending on the ClusterRole definition.
*   **Analogy:** A `RoleBinding` is the act of assigning Agent Jane Foster the "R&D Lab Access - Level 4" clearance specifically for the 'default' department. A `ClusterRoleBinding` is like assigning Captain America the "Command Deck Access - Level 8" clearance, valid everywhere on the Helicarrier.

### 5. Verbs, Resources, and API Groups

*   **Verbs:** The actions allowed (e.g., `get`, `list`, `watch`, `create`, `update`, `patch`, `delete`).
*   **Resources:** The objects the verbs apply to (e.g., `pods`, `services`, `deployments`, `configmaps`, `secrets`). Use `kubectl api-resources` to see available resource types.
*   **API Groups:** Kubernetes resources are organized into API groups (e.g., core `""`, `apps`, `batch`, `networking.k8s.io`, `rbac.authorization.k8s.io`). You specify the group when defining rules.

## Practical Exercise: Basic RBAC

**Objective:** Create a Role that allows reading Pods in the `default` namespace and bind it to a hypothetical user `jane`.

1.  **Navigate:** Open a terminal with `kubectl` configured and navigate to the `hero-academy/lesson-08-rbac` directory.
2.  **Apply Role:** Create the `pod-reader` Role.
    ```bash
    kubectl apply -f pod-reader-role.yaml
    ```
    *   Verify: `kubectl get role pod-reader -n default -o yaml`
3.  **Apply RoleBinding:** Create the `jane-read-pods-binding` RoleBinding.
    ```bash
    kubectl apply -f jane-read-pods-binding.yaml
    ```
    *   Verify: `kubectl get rolebinding jane-read-pods-binding -n default -o yaml`

**Testing the Binding (Conceptual):**

*   Actually testing this requires authenticating to the Kubernetes API *as* the user `jane`. How you do this depends heavily on your cluster's authentication setup.
*   **If using client certificates:** You would need to generate a certificate signing request (CSR) for `jane`, get it signed by the cluster's CA, and create a `kubeconfig` file using that certificate and key.
*   **If using an OIDC provider (like Keycloak linked to AD):** You would configure Kubernetes API server flags to trust Keycloak, log in via Keycloak to get an ID token, and use that token in your `kubeconfig`.
*   **Simulating with `kubectl auth can-i`:** Kubernetes provides a command to check if a user *would* be allowed to perform an action, without needing to fully authenticate as them (requires admin privileges to run the check).
    ```bash
    # Check if user 'jane' can 'get' pods in the 'default' namespace
    kubectl auth can-i get pods --namespace=default --as=jane

    # Check if user 'jane' can 'delete' pods in the 'default' namespace
    kubectl auth can-i delete pods --namespace=default --as=jane

    # Check if user 'jane' can 'get' services in the 'default' namespace
    kubectl auth can-i get services --namespace=default --as=jane
    ```
    You should see `yes` for getting pods and `no` for deleting pods or getting services, based on our Role.

## Discussion: Integrating with Active Directory

Integrating Kubernetes `kubectl` access with your existing Domain Controller (Active Directory) typically involves an intermediary **OIDC (OpenID Connect) provider** that can authenticate users against AD and then issue tokens that Kubernetes can understand.

**Common Pattern:**

1.  **Identity Provider (IdP):** You need a service that:
    *   Can talk to Active Directory (LDAP or Kerberos) to verify user credentials.
    *   Acts as an OIDC Provider, issuing JWT (JSON Web Tokens) like ID Tokens after successful authentication.
    *   Examples:
        *   **Keycloak:** Open-source identity and access management, can connect to LDAP/AD. You'd run Keycloak somewhere accessible to users and your K8s cluster.
        *   **ADFS (Active Directory Federation Services):** Microsoft's solution, can act as an OIDC provider.
        *   Other commercial IdPs (Okta, Azure AD - though Azure AD requires extra steps for on-prem AD).

2.  **Kubernetes API Server Configuration:** You configure the K8s API server (via flags or K3s configuration files) to trust the OIDC provider:
    *   `--oidc-issuer-url`: URL of your OIDC provider (e.g., `https://keycloak.komebacklab.local/auth/realms/your-realm`).
    *   `--oidc-client-id`: Client ID registered in the OIDC provider for Kubernetes.
    *   `--oidc-username-claim`: Which claim in the ID token represents the username (e.g., `preferred_username`, `email`). This **must match** the user name used in RBAC bindings (e.g., `jane`).
    *   `--oidc-groups-claim`: (Optional) Which claim represents the user's groups. This allows binding Roles to AD groups.
    *   `--oidc-ca-file`: (Optional) Path to the CA certificate file if the OIDC provider uses TLS signed by a custom CA (like yours).

3.  **`kubectl` Authentication:** Users authenticate using an OIDC helper tool (like `kubelogin`, `dex`, or custom scripts):
    *   The tool initiates an OIDC login flow (often opening a browser to the IdP login page).
    *   User logs in with AD credentials.
    *   The tool receives an ID token from the IdP.
    *   The tool configures `kubectl` to use this token for authenticating to the Kubernetes API server.

4.  **Kubernetes Authorization (RBAC):**
    *   When `kubectl` makes a request using the token, the API server validates the token against the configured OIDC provider.
    *   It extracts the username (and groups, if configured) from the token claims.
    *   It then uses standard RBAC to check if that username (e.g., `jane`) or any of their groups have the necessary permissions (via RoleBindings/ClusterRoleBindings) for the requested action.

**Considerations:**

*   **Complexity:** Setting up OIDC and integrating it with AD and Kubernetes requires careful configuration on multiple systems.
*   **Token Management:** Users need a way to obtain and refresh tokens for `kubectl`.
*   **RBAC Mapping:** You still need to create the Kubernetes RoleBindings/ClusterRoleBindings to map AD users/groups (as identified by token claims) to Kubernetes permissions.

*Since implementing the full OIDC/AD integration is complex and outside the scope of just creating the app, we focused on the core Kubernetes RBAC concepts (Role, RoleBinding) in this lesson's practical exercise.*

## Problem-Solving Framework: RBAC Issues

1.  **Identify the Symptom:** User receives an authorization error (`Error from server (Forbidden): pods is forbidden: User "jane" cannot list resource "pods" in API group "" in the namespace "default"`). `kubectl auth can-i` returns `no` unexpectedly.
2.  **Locate the Problem Area:** The issue lies in the RBAC configuration – either the permissions defined (Role/ClusterRole) or how they are assigned (RoleBinding/ClusterRoleBinding).
3.  **Consult the Blueprints/Manuals:**
    *   **Check the Binding:** (`kubectl get rolebinding <binding-name> -n <namespace> -o yaml`)
        *   Does the `subjects` section correctly identify the user (`kind: User`, `name: jane`)? Is the name exactly correct (case-sensitive)?
        *   Does the `roleRef` section correctly point to the intended Role (`kind: Role`, `name: pod-reader`)? Is the name correct? Is it pointing to a `Role` (for RoleBinding) or `ClusterRole` (for ClusterRoleBinding)?
        *   Is the binding in the correct `namespace`?
    *   **Check the Role:** (`kubectl get role <role-name> -n <namespace> -o yaml`)
        *   Do the `rules` actually grant the permission being denied?
        *   Does the `verbs` list include the action being attempted (e.g., `list`, `get`, `delete`)?
        *   Does the `resources` list include the resource type being accessed (e.g., `pods`, `services`)? Remember pluralization matters.
        *   Is the `apiGroups` list correct for the resource (e.g., `""` for core, `apps` for deployments)?
    *   **Check Authentication:** Is the user authenticating with the correct username that matches the binding? (Less relevant for `auth can-i`, but critical for real access).
    *   **Namespace Scope:** Is the user trying to access a resource in a namespace where they don't have a binding? (RoleBindings are namespaced). Are they trying to access a cluster-scoped resource using only a namespaced Role?
    *   **ClusterRole vs Role:** Are you using a RoleBinding to bind a ClusterRole? (This is allowed, but only grants the ClusterRole's permissions *within* the RoleBinding's namespace). Are you using a ClusterRoleBinding to bind a Role? (This is *not* allowed).

4.  **Isolate and Test:**
    *   Use `kubectl auth can-i` extensively with different verbs, resources, namespaces, and `--as=<user>` flags.
    *   Create a very simple Role with one permission (e.g., `get pods`) and bind it. Does that work?
    *   Try binding a default ClusterRole (like `view` or `edit`) to the user temporarily. Does that grant broader access as expected? (Remember to remove it afterwards).

5.  **Verify Assumptions:** Did you assume the username provided by the auth system matches the name in the binding? Did you assume the Role contained the right permissions? Did you assume the binding was in the right namespace?

**You now understand how S.H.I.E.L.D. manages clearance levels! RBAC is fundamental to securing your Kubernetes cluster. Next, we'll equip our application with monitoring capabilities using the Eye of Agamotto (Prometheus) and logging with Fluentd.**
