#!/usr/bin/env python3
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

# Constants
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = "oleg-python-rg"
VM_NAME = "oleg-vm"
VNET_NAME = "oleg-vnet"
SUBNET_NAME = "oleg-subnet"
PUBLIC_IP_NAME = "oleg-public-ip"
NSG_NAME = "oleg-nsg"
NIC_NAME = "oleg-nic"

# Azure credentials from environment variables or CLI
credential = DefaultAzureCredential()
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)
compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

def delete_vm():
    try:
        print(f"Deleting VM {VM_NAME}...")
        compute_client.virtual_machines.begin_delete(RESOURCE_GROUP, VM_NAME).wait()
    except Exception as e:
        print(f"Error deleting VM: {e}")

def delete_nic():
    try:
        print(f"Deleting NIC {NIC_NAME}...")
        network_client.network_interfaces.begin_delete(RESOURCE_GROUP, NIC_NAME).wait()
    except Exception as e:
        print(f"Error deleting NIC: {e}")

def delete_public_ip():
    try:
        print(f"Deleting public IP {PUBLIC_IP_NAME}...")
        network_client.public_ip_addresses.begin_delete(RESOURCE_GROUP, PUBLIC_IP_NAME).wait()
    except Exception as e:
        print(f"Error deleting public IP: {e}")

def delete_nsg():
    try:
        print(f"Deleting NSG {NSG_NAME}...")
        network_client.network_security_groups.begin_delete(RESOURCE_GROUP, NSG_NAME).wait()
    except Exception as e:
        print(f"Error deleting NSG: {e}")

def delete_vnet():
    try:
        print(f"Deleting virtual network {VNET_NAME}...")
        network_client.virtual_networks.begin_delete(RESOURCE_GROUP, VNET_NAME).wait()
    except Exception as e:
        print(f"Error deleting VNet: {e}")

def delete_resource_group():
    try:
        print(f"Deleting resource group {RESOURCE_GROUP}...")
        resource_client.resource_groups.begin_delete(RESOURCE_GROUP).wait()
    except Exception as e:
        print(f"Error deleting resource group: {e}")

def main():
    delete_vm()
    delete_nic()
    delete_public_ip()
    delete_nsg()
    delete_vnet()
    delete_resource_group()
    print("All resources deleted successfully!")

if __name__ == "__main__":
    main()