#!/usr/bin/env python3
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

# Constants
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = "oleg-python-rg"
LOCATION = "East US"
VM_NAME = "oleg-vm"
VNET_NAME = "oleg-vnet"
SUBNET_NAME = "oleg-subnet"
PUBLIC_IP_NAME = "oleg-public-ip"
NSG_NAME = "oleg-nsg"
NIC_NAME = "oleg-nic"
SSH_KEY_PATH = os.path.expanduser("~/.ssh/azure_key.pub")

# Azure credentials from environment variables or CLI
credential = DefaultAzureCredential()
resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
network_client = NetworkManagementClient(credential, SUBSCRIPTION_ID)
compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

def create_resource_group():
    print("Creating resource group...")
    resource_client.resource_groups.create_or_update(
        RESOURCE_GROUP,
        {"location": LOCATION}
    )

def create_virtual_network():
    print("Creating virtual network and subnet...")
    vnet_params = {
        "location": LOCATION,
        "address_space": {"address_prefixes": ["10.0.0.0/16"]}
    }
    vnet_result = network_client.virtual_networks.begin_create_or_update(
        RESOURCE_GROUP, VNET_NAME, vnet_params
    ).result()

    subnet_params = {
        "address_prefix": "10.0.1.0/24"
    }
    subnet_result = network_client.subnets.begin_create_or_update(
        RESOURCE_GROUP, VNET_NAME, SUBNET_NAME, subnet_params
    ).result()
    return subnet_result.id

def create_public_ip():
    print("Creating public IP...")
    public_ip_params = {
        "location": LOCATION,
        "public_ip_allocation_method": "Static",
        "sku": {"name": "Standard"}
    }
    public_ip_result = network_client.public_ip_addresses.begin_create_or_update(
        RESOURCE_GROUP, PUBLIC_IP_NAME, public_ip_params
    ).result()
    return public_ip_result.id

def create_nsg():
    print("Creating network security group...")
    nsg_params = {
        "location": LOCATION,
        "security_rules": [
            {
                "name": "SSH",
                "protocol": "Tcp",
                "source_port_range": "*",
                "destination_port_range": "22",
                "source_address_prefix": "*",
                "destination_address_prefix": "*",
                "access": "Allow",
                "priority": 1001,
                "direction": "Inbound"
            }
        ]
    }
    print("NSG params being sent:", nsg_params)
    try:
        nsg_result = network_client.network_security_groups.begin_create_or_update(
            RESOURCE_GROUP, NSG_NAME, nsg_params
        ).result()
        return nsg_result.id
    except Exception as e:
        print(f"Exception details: {e}")
        raise

def create_nic(subnet_id, public_ip_id, nsg_id):
    print("Creating network interface...")
    nic_params = {
        "location": LOCATION,
        "ip_configurations": [
            {
                "name": "my-nic-config",
                "subnet": {"id": subnet_id},
                "public_ip_address": {"id": public_ip_id}
            }
        ],
        "network_security_group": {"id": nsg_id}
    }
    nic_result = network_client.network_interfaces.begin_create_or_update(
        RESOURCE_GROUP, NIC_NAME, nic_params
    ).result()
    return nic_result.id

def create_vm(nic_id):
    print("Creating VM...")
    with open(SSH_KEY_PATH, "r") as f:
        ssh_public_key = f.read().strip()

    vm_params = {
        "location": LOCATION,
        "hardware_profile": {"vm_size": "Standard_B1s"},
        "storage_profile": {
            "image_reference": {
                "publisher": "Canonical",
                "offer": "UbuntuServer",
                "sku": "18.04-LTS",
                "version": "latest"
            },
            "os_disk": {
                "create_option": "FromImage",
                "name": "my-os-disk",
                "caching": "ReadWrite",
                "managed_disk": {"storage_account_type": "Standard_LRS"}
            }
        },
        "os_profile": {
            "computer_name": VM_NAME,
            "admin_username": "azureuser",
            "linux_configuration": {
                "disable_password_authentication": True,
                "ssh": {
                    "public_keys": [
                        {"path": "/home/azureuser/.ssh/authorized_keys", "key_data": ssh_public_key}
                    ]
                }
            }
        },
        "network_profile": {
            "network_interfaces": [{"id": nic_id}]
        }
    }
    vm_result = compute_client.virtual_machines.begin_create_or_update(
        RESOURCE_GROUP, VM_NAME, vm_params
    ).result()
    print(f"VM {VM_NAME} created successfully!")

def main():
    create_resource_group()
    subnet_id = create_virtual_network()
    public_ip_id = create_public_ip()
    nsg_id = create_nsg()
    nic_id = create_nic(subnet_id, public_ip_id, nsg_id)
    create_vm(nic_id)

    # Get public IP for SSH
    public_ip = network_client.public_ip_addresses.get(RESOURCE_GROUP, PUBLIC_IP_NAME)
    print(f"SSH to VM: ssh -i ~/.ssh/azure_key azureuser@{public_ip.ip_address}")

if __name__ == "__main__":
    main()