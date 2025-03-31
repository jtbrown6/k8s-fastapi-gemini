# Lesson 2: Mission Control (GitLab, CI/CD & Harbor Registry)

**Objective:** Set up version control for our project using Git, create a project in GitLab, and configure a basic CI/CD pipeline to automatically build our Docker image and push it to your Harbor container registry whenever changes are made.

**Analogy:** We've built our first suit prototype (Lesson 1). Now, we need a secure R&D lab (Git repository) to track changes and blueprints, and an automated assembly line (CI/CD pipeline) managed by Mission Control (GitLab) to build and store the finished suits (Docker images) in a secure armory (Harbor Registry).

## Concepts Introduced

### 1. Git & Version Control: The Lab Notebook

*   **What it is:** A distributed version control system for tracking changes in source code during software development. It allows multiple developers to collaborate and keeps a history of all changes.
*   **Analogy:** Git is like Tony Stark's detailed digital lab notebook. Every experiment, every modification to the suit design is recorded (`git commit`). You can go back to previous versions (`git checkout`), see exactly what changed (`git diff`), and work on new features in separate drafts (`git branch`) before merging them into the main design (`git merge`).

### 2. GitLab: Mission Control Headquarters

*   **What it is:** A web-based DevOps platform that provides Git repository management, CI/CD pipelines, issue tracking, and more. We're using your self-hosted instance at `gitlab.komebacklab.local`.
*   **Analogy:** GitLab is the S.H.I.E.L.D. Helicarrier or Avengers Tower – the central hub (Mission Control) where project blueprints (Git repositories) are stored, missions (CI/CD pipelines) are planned and executed, and team communication happens.

### 3. CI/CD: Automated Assembly Line

*   **What it is:**
    *   **Continuous Integration (CI):** The practice of frequently merging code changes into a central repository, after which automated builds and tests run.
    *   **Continuous Deployment/Delivery (CD):** The practice of automatically deploying code changes to production (or other environments) after the CI stage passes.
*   **Why use it:** Automates the build, test, and deployment process, leading to faster feedback, reduced errors, and more frequent releases.
*   **Analogy:** CI/CD is the automated suit assembly line in Stark Industries.
    *   **CI:** When a new blueprint change is submitted (`git push`), the system automatically runs diagnostics and builds a new prototype (builds the Docker image).
    *   **CD:** If the build is successful, the system automatically ships the finished suit to the armory (pushes the image to Harbor). Our pipeline currently does CI and the "delivery" part of CD (delivering the image to the registry). Actual deployment to Kubernetes comes later.

### 4. Container Registry (Harbor): The Armory

*   **What it is:** A storage system for Docker container images. It allows you to store, manage, and distribute your built images. We're using your self-hosted Harbor instance at `harbor.komebacklab.local`.
*   **Analogy:** Harbor is like Iron Man's Hall of Armor or Asgard's Vault. It's a secure, organized place to store all the different versions and models of your suits (container images) after they've been built by the assembly line (CI/CD). When you need to deploy a specific suit (image), you retrieve it from the armory (registry).

### 5. `.gitlab-ci.yml`: The Assembly Line Instructions

*   **What it is:** The configuration file used by GitLab CI/CD to define the pipeline's stages, jobs, and scripts.
*   **Analogy:** This file is the detailed instruction set for the automated assembly line. It tells GitLab:
    *   `stages`: The overall phases of assembly (`build`, `push`).
    *   `jobs` (like `build_image`, `push_image`): Specific tasks within each stage.
    *   `image`/`services`: The tools and environment needed for the job (using Docker itself to build Docker images - "Docker-in-Docker" or dind).
    *   `variables`: Configurable parameters for the job (like the image name, registry location).
    *   `before_script`/`script`: The exact commands to run (login to Harbor, run `docker build`, run `docker push`).
    *   `rules`: When to run the job (e.g., only on the `main` branch).

## Practical Exercise: Setting Up GitLab & CI/CD

**Part 1: Project Setup (Local & GitLab)**

1.  **Initialize Git Locally:**
    *   Navigate to the root `hero-academy` directory in your terminal (the one containing `lesson-01-recruit` and `lesson-02-mission-control`).
    *   Initialize a Git repository:
        ```bash
        cd .. # Go up one level from lesson-01-recruit if you are still there
        git init
        ```
    *   Create a `.gitignore` file in the `hero-academy` root to exclude common Python and temporary files:
        ```bash
        # Example .gitignore content:
        __pycache__/
        *.pyc
        *.pyo
        *.pyd
        .Python
        env/
        venv/
        *.env
        .vscode/
        ```
        *(You can use `write_to_file` to create this or create it manually)*
    *   Add all the lesson files created so far and make your first commit:
        ```bash
        git add .
        git commit -m "Initial commit: Lesson 1 files"
        ```

2.  **Create GitLab Project:**
    *   Go to your GitLab instance (`https://gitlab.komebacklab.local`).
    *   Create a new **blank project**. Name it something like `hero-academy`. Make it **private** unless you want it public. **Do NOT** initialize it with a README (we already have our code).
    *   GitLab will show you instructions for pushing an existing repository. Copy the commands under the "Push an existing folder" section. They will look something like this (use the ones GitLab provides with your specific URL):
        ```bash
        # Example commands from GitLab - use YOUR project's URL
        git remote add origin https://gitlab.komebacklab.local/your-username/hero-academy.git
        git branch -M main # Or master, depending on your default
        git push -u origin main # Or master
        ```
    *   Execute these commands in your local `hero-academy` terminal.

3.  **Add Lesson 2 Files:**
    *   Copy the `.gitlab-ci.yml` file from `lesson-02-mission-control` to the **root** of your `hero-academy` repository. The CI file needs to be in the root.
    *   Copy the `lesson-02-guide.md` into a `docs` or `lessons/lesson-02` directory within your repository (or keep it separate for reference).
    *   Add the new files and commit:
        ```bash
        # Assuming .gitlab-ci.yml is now in the root
        git add .gitlab-ci.yml
        # Add the guide if you placed it inside the repo
        # git add docs/lesson-02-guide.md
        git commit -m "Add Lesson 2 GitLab CI configuration and guide"
        ```
    *   *(Do not push yet! We need to configure secrets first.)*

**Part 2: Configure GitLab & Harbor**

1.  **Harbor Project:** Ensure you have a project created in your Harbor instance (`https://harbor.komebacklab.local`). Note the **project name**. Update the `HARBOR_PROJECT_NAME` variable in `.gitlab-ci.yml` with this name.
    ```yaml
    variables:
      HARBOR_PROJECT_NAME: "your-actual-harbor-project-name" # <-- CHANGE THIS
      # ... rest of variables
    ```
    *   Commit this change:
        ```bash
        git add .gitlab-ci.yml
        git commit -m "Update HARBOR_PROJECT_NAME in .gitlab-ci.yml"
        ```

2.  **Harbor User (Robot Account Recommended):** It's best practice to create a "Robot Account" in Harbor specifically for CI/CD.
    *   In Harbor, go to `Robot Accounts` and create one within your project.
    *   Give it permissions to `push` and `pull` repositories.
    *   **Securely copy the robot account name (e.g., `robot$your-project+gitlab`) and the secret token.**

3.  **GitLab CI/CD Variables:** Configure GitLab to securely provide the Harbor credentials to the pipeline.
    *   In your GitLab project (`hero-academy`), go to `Settings` -> `CI/CD`.
    *   Expand the `Variables` section.
    *   Add two variables:
        *   **Key:** `HARBOR_USER`
            *   **Value:** *Paste the full Harbor robot account name here*
            *   **Flags:** Ensure `Protect variable` is **unchecked** (unless your main branch is protected and runners are configured for protected branches) and `Mask variable` is **checked**.
        *   **Key:** `HARBOR_PASSWORD`
            *   **Value:** *Paste the Harbor robot account secret token here*
            *   **Flags:** Ensure `Protect variable` is **unchecked** and `Mask variable` is **checked**.

**Part 3: Run the Pipeline**

1.  **Push Changes:** Now that the secrets are configured in GitLab, push your latest commits:
    ```bash
    git push
    ```
2.  **Monitor Pipeline:** Go to your GitLab project's `CI/CD` -> `Pipelines` section. You should see a new pipeline running (or pending).
    *   Click on the pipeline status to see the stages (`build`, `push`).
    *   Click on individual jobs (`build_image`, `push_image`) to see the live log output.
3.  **Verify in Harbor:** If the pipeline succeeds, go to your Harbor instance, navigate to your project, and you should see a new repository named `hero-registry` (or your `APP_NAME`) containing images tagged with the commit SHA and `latest`.

## Problem-Solving Framework: Debugging Mission Control

CI/CD pipelines introduce new places where things can break.

1.  **Identify the Symptom:** Where did it fail?
    *   *Pipeline doesn't start:* Is `.gitlab-ci.yml` in the repository root? Is the syntax valid (use GitLab's CI Lint tool under `CI/CD` -> `Pipelines`)? Are your GitLab Runners configured and active for the project?
    *   *Job fails (e.g., `build_image`):* Click the job in the GitLab UI and examine the logs carefully.
2.  **Locate the Problem Area (based on logs):**
    *   *Permission Denied / Authentication Errors (during `docker login` or `docker push`):* Double-check the `HARBOR_USER` and `HARBOR_PASSWORD` variables in GitLab CI/CD settings. Are they correct? Are they masked? Does the Harbor robot account have the correct permissions (push/pull) in Harbor? Is `harbor.komebacklab.local` reachable from your GitLab Runner?
    *   *Docker Daemon Not Ready / Cannot connect to Docker daemon:* Issues with the Docker-in-Docker service setup in `.gitlab-ci.yml`. Check the `services`, `variables` (like `DOCKER_HOST`), and `before_script` waiting logic. Ensure your GitLab Runner is configured to allow dind (may require `privileged = true` in the runner's config.toml, depending on setup).
    *   *`docker build` fails:* Usually the same reasons as local builds (Dockerfile errors, missing files, `requirements.txt` issues), but check paths carefully. The CI job runs from the repo root, so paths in the `docker build` command (`-f ./lesson-01-recruit/Dockerfile ./lesson-01-recruit`) must be relative to the root.
    *   *`docker push` fails (after build succeeds):* Usually authentication/permission issues (see above) or network issues connecting to Harbor.
    *   *Variable errors (`unknown variable ${...}`):* Typo in the variable name in `.gitlab-ci.yml` or the variable wasn't defined in GitLab settings.
3.  **Consult the Blueprints/Manuals:**
    *   *`.gitlab-ci.yml`:* Check syntax, stage/job definitions, variable names, script commands, paths.
    *   *GitLab CI/CD Variables:* Verify keys, values, and flags (masked/protected).
    *   *Harbor Project/Robot Account:* Check permissions.
    *   *GitLab Runner Configuration:* Ensure it's active, tagged correctly (if using tags in `.gitlab-ci.yml`), and capable of running Docker-in-Docker if needed.
4.  **Isolate and Test:**
    *   Can you manually run the `docker build` and `docker push` commands (with credentials) from a machine that *can* reach Harbor (like your local machine)? This helps isolate runner/network issues.
    *   Simplify the `.gitlab-ci.yml`. Try a job that just does `echo "Hello"`. Does that run? Gradually add complexity back.
5.  **Verify Assumptions:** Did you assume the runner has internet access? Did you assume the Harbor project name was correct? Did you assume the branch name (`main`/`master`) matched the `rules`?

**Example Scenario:** The `push_image` job fails with `denied: requested access to the resource is denied`.

*   **Symptom:** Access denied during push.
*   **Location:** Authentication/Authorization issue with Harbor.
*   **Check:**
    *   Verify `HARBOR_USER` and `HARBOR_PASSWORD` in GitLab CI/CD variables *exactly* match the Harbor robot account credentials.
    *   Verify the Harbor robot account has **push** permissions for the specific project (`your-harbor-project`) in Harbor.
    *   Verify the image name being pushed (`harbor.komebacklab.local/your-harbor-project/hero-registry:sha`) matches the Harbor project structure. Is `your-harbor-project` spelled correctly?

**You've now established Mission Control! Your code changes are tracked, and an automated system builds and stores your container images securely. Next lesson, we deploy our container to the Kubernetes cluster!**
