provider "oci" {
  region = var.region
}

variable "shape_list" {
  type    = list(string)
  default = ["VM.Standard.E5.Flex", "VM.Standard.E4.Flex", "VM.Standard3.Flex", "VM.Optimized3.Flex", "VM.Standard.A1.Flex"]
}

locals {
  nodes = {
    for i, val in var.shape_list :
    i => {
      node_name = format("node%d", i)
      shape     = val
      testname  = lower(replace(val, ".", ""))
    }
  }
  memory = 16
  ocpu   = 1
}

resource "random_uuid" "test_id" {}

resource "oci_core_vcn" "test_vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_id
  display_name   = "vcn-${var.application_name}"
}

resource "oci_core_subnet" "public_subnet" {
  cidr_block     = "10.0.100.0/24"
  compartment_id = var.compartment_id
  display_name   = "public_subnet"
  vcn_id         = oci_core_vcn.test_vcn.id
  route_table_id = oci_core_vcn.test_vcn.default_route_table_id
  security_list_ids = [
    oci_core_vcn.test_vcn.default_security_list_id,
  ]
}

resource "oci_core_internet_gateway" "internet_gateway" {
  compartment_id = var.compartment_id
  display_name   = "internet_gateway"
  vcn_id         = oci_core_vcn.test_vcn.id
}

resource "oci_core_default_route_table" "default_route_table" {
  manage_default_resource_id = oci_core_vcn.test_vcn.default_route_table_id
  route_rules {
    network_entity_id = oci_core_internet_gateway.internet_gateway.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "images" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  for_each                 = local.nodes
  shape                    = each.value.shape
}

resource "oci_core_instance" "instance" {
  for_each            = local.nodes
  display_name        = each.value.node_name
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_id
  shape               = each.value.shape
  create_vnic_details {
    subnet_id = oci_core_subnet.public_subnet.id
  }
  agent_config {
    is_management_disabled = true
    is_monitoring_disabled = true
  }
  shape_config {
    memory_in_gbs = local.memory
    ocpus         = local.ocpu
  }
  source_details {
    source_id   = data.oci_core_images.images[each.key].images[0].id
    source_type = "image"
  }
  metadata = {
    ssh_authorized_keys = "${file("./id_rsa.pub")}"
    user_data           = "${base64encode(file("./user_data.sh"))}"
    TEST_RESULTS_NAME   = each.value.testname
    TEST_ID             = random_uuid.test_id.result
  }
  preserve_boot_volume = false
}


output "ip" {
  value = values(oci_core_instance.instance).*.public_ip
}
