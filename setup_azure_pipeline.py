import subprocess
import os
import sys
import random

# Configuration
AZURE_SUBSCRIPTION = "3f79a68d-cf0d-4291-a31f-185897f7fda1"
AZURE_DEVOPS_ORG = "markveltzer"
AZURE_DEVOPS_PROJECT = "training"
RESOURCE_GROUP = "OlegResourceGroup"
LOCATION = "eastus"
ACR_NAME = f"olegacrr5423"
REPO_NAME = "oleg_script_rep2"
PIPELINE_NAME = "oleg_pipeline2"
SERVICE_CONNECTION_NAME = "olegconnect"
SP_APP_ID = "8ecdf10e-c3e0-4349-b9f2-ef531b1222a5"
SP_TENANT_ID = "d12c5e26-8134-4d75-adb9-89c53343dc6b"
SUBSCRIPTION_NAME = "Basic"

AZ_CLI_PATH = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
PAT = "8Jn2eT7mTIDEmEGorlvbwQW7GMeAdUafKx2J8JOR23vh7oQrNsNHJQQJ99BCACAAAAAAAAAAAAASAZDO2nJg"  # Your PAT

# Function to run shell commands with debug output
def run_command(command, shell=True):
    if command[0] == "az":
        command = [AZ_CLI_PATH] + command[1:]
    print(f"Executing: {' '.join(command)}")
    try:
        result = subprocess.run(command, shell=shell, check=True, text=True, capture_output=True)
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error Output: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}")
        print(f"Exit code: {e.returncode}")
        print(f"Error: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

# Set Azure subscription
print("Setting Azure subscription...")
run_command(["az", "account", "set", "--subscription", AZURE_SUBSCRIPTION])

print("Verifying active subscription...")
run_command(["az", "account", "show", "--output", "table"])

# Create resource group
print(f"Creating resource group {RESOURCE_GROUP}...")
run_command(["az", "group", "create", "--name", RESOURCE_GROUP, "--location", LOCATION])

# Create Azure Container Registry
print(f"Creating Azure Container Registry {ACR_NAME}...")
run_command(["az", "acr", "create", "--resource-group", RESOURCE_GROUP, "--name", ACR_NAME, "--sku", "Basic"])

# Configure Azure DevOps CLI
print("Configuring Azure DevOps CLI...")
run_command(["az", "devops", "configure", "--defaults",
             f"organization=https://dev.azure.com/{AZURE_DEVOPS_ORG}",
             f"project={AZURE_DEVOPS_PROJECT}"])

# Create a new repository in Azure Repos
print(f"Creating repository {REPO_NAME}...")
run_command(["az", "repos", "create", "--name", REPO_NAME])

# Clone the repository locally and upload sample code
print("Cloning repository and uploading sample code...")
repo_url = f"https://{PAT}@dev.azure.com/{AZURE_DEVOPS_ORG}/{AZURE_DEVOPS_PROJECT}/_git/{REPO_NAME}"
run_command(["git", "clone", repo_url])
os.chdir(REPO_NAME)

# Create a sample Dockerfile
with open("Dockerfile", "w") as f:
    f.write("FROM alpine\n")
    f.write('CMD ["echo", "Hello from my container!"]\n')

# Git commands to commit and push
run_command(["git", "add", "."])
run_command(["git", "commit", "-m", "Initial commit with sample Dockerfile"])
run_command(["git", "push", f"https://{PAT}@dev.azure.com/{AZURE_DEVOPS_ORG}/{AZURE_DEVOPS_PROJECT}/_git/{REPO_NAME}", "master"])

# Create the pipeline YAML file
pipeline_yaml = f"""\
trigger:
- master
pool:
  vmImage: 'ubuntu-latest'
variables:
  dockerRegistryServiceConnection: '{SERVICE_CONNECTION_NAME}'
  imageRepository: 'myimage'
  tag: '$(Build.BuildId)'
steps:
- task: Docker@2
  displayName: 'Build and push Docker image'
  inputs:
    command: 'buildAndPush'
    repository: '$(imageRepository)'
    dockerfile: '$(Build.SourcesDirectory)/Dockerfile'
    containerRegistry: '$(dockerRegistryServiceConnection)'
    tags: '$(tag)'
"""
with open("azure-pipelines.yml", "w") as f:
    f.write(pipeline_yaml)

# Commit and push the pipeline file
run_command(["git", "add", "azure-pipelines.yml"])
run_command(["git", "commit", "-m", "Add pipeline configuration"])
run_command(["git", "push", f"https://{PAT}@dev.azure.com/{AZURE_DEVOPS_ORG}/{AZURE_DEVOPS_PROJECT}/_git/{REPO_NAME}", "master"])

# Create and run the pipeline
print(f"Creating pipeline {PIPELINE_NAME}...")
run_command([
    "az", "pipelines", "create",
    "--name", PIPELINE_NAME,
    "--repository", REPO_NAME,
    "--branch", "master",
    "--yaml-path", "azure-pipelines.yml",
    "--repository-type", "tfsgit"  
])

print(f"Triggering pipeline {PIPELINE_NAME} run...")
run_command(["az", "pipelines", "run", "--name", PIPELINE_NAME])

print("Script completed successfully!")