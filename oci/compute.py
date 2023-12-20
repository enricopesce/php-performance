import oci
import os.path


class computeDeploy:
    OPERATING_SYSTEM = 'Oracle Linux'
    OPERATING_SYSTEM_VERSION = '8'
    WAIT_TIME = 900
    OCPU = 1
    RAM = 16
    COMPARTMENT_ID = ""

    def __init__(self, cpu, ram, compartment_id):
        self.OCPU = cpu
        self.RAM = ram
        self.COMPARTMENT_ID = compartment_id
        cidr_block = "10.0.0.0/24"
        with open(os.path.expandvars(os.path.expanduser("id_rsa.pub")), mode='r') as file:
            ssh_public_key = file.read()
        config = {}

        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        identity_client = oci.identity.IdentityClient(config, signer=signer)
        compute_client = oci.core.ComputeClient(config, signer=signer)
        compute_client_composite_operations = oci.core.ComputeClientCompositeOperations(compute_client, signer=signer)
        virtual_network_client = oci.core.VirtualNetworkClient(config, signer=signer)
        virtual_network_composite_operations = oci.core.VirtualNetworkClientCompositeOperations(virtual_network_client, signer=signer)
        work_request_client = oci.work_requests.WorkRequestClient(config, signer=signer)
        object_storage_client = oci.object_storage.ObjectStorageClient(config, signer=signer)
        
        availability_domain = self.get_availability_domain()
        shape = self.get_shape(compute_client, compartment_id, availability_domain)
        image = self.get_image(compute_client, compartment_id, shape)

        vcn = None
        subnet = None
        internet_gateway = None
        network_security_group = None
        instance = None
        instance_via_work_requests = None
        instance_with_network_security_group = None
        source_volume = None
        destination_volume = None
        source_volume_attachment = None
        destination_volume_attachment = None

        try:
            vcn = self.create_vcn(virtual_network_composite_operations, compartment_id, cidr_block)
            subnet = self.create_subnet(virtual_network_composite_operations, vcn, availability_domain)
            internet_gateway = self.create_internet_gateway(virtual_network_composite_operations, vcn)
            self.add_route_rule_to_default_route_table_for_internet_gateway(
                virtual_network_client, virtual_network_composite_operations, vcn, internet_gateway
            )
            network_security_group = self.create_network_security_group(virtual_network_composite_operations, compartment_id, vcn)
            self.add_network_security_group_security_rules(virtual_network_client, network_security_group)
            launch_instance_details = self.get_launch_instance_details(
                compartment_id, availability_domain, shape, image, subnet, ssh_public_key
            )
            launch_instance_details.create_vnic_details.nsg_ids = [network_security_group.id]
            instance_with_network_security_group = self.launch_instance(
                compute_client_composite_operations, launch_instance_details
            )
            self.print_instance_details(compute_client, virtual_network_client, instance_with_network_security_group)

        except Exception as e:
            print(e)
        finally:
            print('Cleaning resources')
            print('================================================')
            print()

            if instance_with_network_security_group:
                terminate_instance(compute_client_composite_operations, instance_with_network_security_group)
            if instance_via_work_requests:
                terminate_instance(compute_client_composite_operations, instance_via_work_requests)
            if instance:
                terminate_instance(compute_client_composite_operations, instance)

            # The network security group needs to be deleted before we can remove the subnet and vcn
            if network_security_group:
                remove_network_security_group_security_rules(virtual_network_client, network_security_group)
                delete_network_security_group(virtual_network_composite_operations, network_security_group)

            if internet_gateway:
                # Because the internet gateway is referenced by a route rule, the rule needs to be deleted before
                # we can remove the internet gateway
                clear_route_rules_from_default_route_table(virtual_network_composite_operations, vcn)
                delete_internet_gateway(virtual_network_composite_operations, internet_gateway)

            if subnet:
                delete_subnet(virtual_network_composite_operations, subnet)

            if vcn:
                delete_vcn(virtual_network_composite_operations, vcn)


    def get_availability_domain():
        list_availability_domains_response = oci.pagination.list_call_get_all_results(
            identity_client.list_availability_domains,
            compartment_id
        )
        # For demonstration, we just return the first availability domain but for Production code you should
        # have a better way of determining what is needed
        availability_domain = list_availability_domains_response.data[0].name

        print()
        print('Running in Availability Domain: {}'.format(availability_domain))

        return availability_domain


    def get_shape(compute_client, compartment_id, availability_domain):
        list_shapes_response = oci.pagination.list_call_get_all_results(
            compute_client.list_shapes,
            compartment_id,
            availability_domain=availability_domain
        )
        shapes = list_shapes_response.data
        if len(shapes) == 0:
            raise RuntimeError('No available shape was found.')
        
        vm_shapes = list(filter(lambda shape: shape.shape.startswith("VM.Standard.E4.Flex"), shapes))
        if len(vm_shapes) == 0:
            raise RuntimeError('No available VM shape was found.')

        # For demonstration, we just return the first shape but for Production code you should have a better
        # way of determining what is needed
        shape = vm_shapes[0]

        print('Found Shape: {}'.format(shape.shape))

        return shape


    def get_image(compute, compartment_id, shape):
        # Listing images is a paginated call, so we can use the oci.pagination module to get all results
        # without having to manually handle page tokens
        #
        # In this case, we want to find the image for the operating system we want to run, and which can
        # be used for the shape of instance we want to launch
        list_images_response = oci.pagination.list_call_get_all_results(
            compute.list_images,
            compartment_id,
            operating_system=OPERATING_SYSTEM,
            operating_system_version=OPERATING_SYSTEM_VERSION,
            shape=shape.shape
        )
        images = list_images_response.data
        if len(images) == 0:
            raise RuntimeError('No available image was found.')
        
        # Oracle-Linux-8.8-2023.09.26-0

        # For demonstration, we just return the first image but for Production code you should have a better
        # way of determining what is needed
        image = images[0]

        print('Found Image: {}'.format(image.display_name))
        print()

        return image


    def create_vcn(virtual_network_composite_operations, compartment_id, cidr_block):
        vcn_name = 'py_sdk_example_vcn'
        create_vcn_details = oci.core.models.CreateVcnDetails(
            cidr_block=cidr_block,
            display_name=vcn_name,
            compartment_id=compartment_id
        )
        create_vcn_response = virtual_network_composite_operations.create_vcn_and_wait_for_state(
            create_vcn_details,
            wait_for_states=[oci.core.models.Vcn.LIFECYCLE_STATE_AVAILABLE]
        )
        vcn = create_vcn_response.data

        print('Created VCN: {}'.format(vcn.id))
        print('{}'.format(vcn))
        print()

        return vcn


    def delete_vcn(virtual_network_composite_operations, vcn):
        virtual_network_composite_operations.delete_vcn_and_wait_for_state(
            vcn.id,
            wait_for_states=[oci.core.models.Vcn.LIFECYCLE_STATE_TERMINATED]
        )

        print('Deleted VCN: {}'.format(vcn.id))
        print()


    def create_subnet(virtual_network_composite_operations, vcn, availability_domain):
        subnet_name = 'py_sdk_example_subnet'
        create_subnet_details = oci.core.models.CreateSubnetDetails(
            compartment_id=vcn.compartment_id,
            availability_domain=availability_domain,
            display_name=subnet_name,
            vcn_id=vcn.id,
            cidr_block=vcn.cidr_block
        )
        create_subnet_response = virtual_network_composite_operations.create_subnet_and_wait_for_state(
            create_subnet_details,
            wait_for_states=[oci.core.models.Subnet.LIFECYCLE_STATE_AVAILABLE]
        )
        subnet = create_subnet_response.data

        print('Created Subnet: {}'.format(subnet.id))
        print('{}'.format(subnet))
        print()

        return subnet


    def delete_subnet(virtual_network_composite_operations, subnet):
        virtual_network_composite_operations.delete_subnet_and_wait_for_state(
            subnet.id,
            wait_for_states=[oci.core.models.Subnet.LIFECYCLE_STATE_TERMINATED]
        )

        print('Deleted Subnet: {}'.format(subnet.id))
        print()


    def create_internet_gateway(virtual_network_composite_operations, vcn):
        internet_gateway_name = 'py_sdk_example_ig'
        create_internet_gateway_details = oci.core.models.CreateInternetGatewayDetails(
            display_name=internet_gateway_name,
            compartment_id=vcn.compartment_id,
            is_enabled=True,
            vcn_id=vcn.id
        )
        create_internet_gateway_response = virtual_network_composite_operations.create_internet_gateway_and_wait_for_state(
            create_internet_gateway_details,
            wait_for_states=[oci.core.models.InternetGateway.LIFECYCLE_STATE_AVAILABLE]
        )
        internet_gateway = create_internet_gateway_response.data

        print('Created internet gateway: {}'.format(internet_gateway.id))
        print('{}'.format(internet_gateway))
        print()

        return internet_gateway


    def delete_internet_gateway(virtual_network_composite_operations, internet_gateway):
        virtual_network_composite_operations.delete_internet_gateway_and_wait_for_state(
            internet_gateway.id,
            wait_for_states=[oci.core.models.InternetGateway.LIFECYCLE_STATE_TERMINATED]
        )

        print('Deleted Internet Gateway: {}'.format(internet_gateway.id))
        print()


    def add_route_rule_to_default_route_table_for_internet_gateway(
            virtual_network_client, virtual_network_composite_operations, vcn, internet_gateway):
        get_route_table_response = virtual_network_client.get_route_table(vcn.default_route_table_id)
        route_rules = get_route_table_response.data.route_rules

        print('Current Route Rules For VCN')
        print('===========================')
        print('{}'.format(route_rules))
        print()

        # Updating route rules will totally replace any current route rules with what we send through.
        # If we wish to preserve any existing route rules, we need to read them out first and then send
        # them back to the service as part of any update
        route_rule = oci.core.models.RouteRule(
            cidr_block=None,
            destination='0.0.0.0/0',
            destination_type='CIDR_BLOCK',
            network_entity_id=internet_gateway.id
        )
        route_rules.append(route_rule)
        update_route_table_details = oci.core.models.UpdateRouteTableDetails(route_rules=route_rules)
        update_route_table_response = virtual_network_composite_operations.update_route_table_and_wait_for_state(
            vcn.default_route_table_id,
            update_route_table_details,
            wait_for_states=[oci.core.models.RouteTable.LIFECYCLE_STATE_AVAILABLE]
        )
        route_table = update_route_table_response.data

        print('Updated Route Rules For VCN')
        print('===========================')
        print('{}'.format(route_table.route_rules))
        print()

        return route_table


    def clear_route_rules_from_default_route_table(virtual_network_composite_operations, vcn):
        update_route_table_details = oci.core.models.UpdateRouteTableDetails(route_rules=[])
        virtual_network_composite_operations.update_route_table_and_wait_for_state(
            vcn.default_route_table_id,
            update_route_table_details,
            wait_for_states=[oci.core.models.RouteTable.LIFECYCLE_STATE_AVAILABLE]
        )

        print('Cleared Route Rules from Route Table: {}'.format(vcn.default_route_table_id))
        print()


    def create_network_security_group(virtual_network_composite_operations, compartment_id, vcn):
        network_security_group_name = 'py_sdk_example_network_security_group'
        create_network_security_group_details = oci.core.models.CreateNetworkSecurityGroupDetails(
            display_name=network_security_group_name,
            compartment_id=compartment_id,
            vcn_id=vcn.id
        )
        create_network_security_group_response = virtual_network_composite_operations.create_network_security_group_and_wait_for_state(
            create_network_security_group_details,
            wait_for_states=[oci.core.models.RouteTable.LIFECYCLE_STATE_AVAILABLE]
        )
        network_security_group = create_network_security_group_response.data

        print('Created Network Security Group: {}'.format(network_security_group.id))
        print('{}'.format(network_security_group))
        print()

        return network_security_group


    def create_object_storage(object_storage_client):
        namespace = object_storage_client.get_namespace().data
        create_bucket_response = object_storage_client.create_bucket(
            namespace,
            oci.object_storage.models.CreateBucketDetails(
                name="poronix-results",
                compartment_id=compartment_id,
            )
        ).data

        print('Created storage bucket:\n{}'.format(create_bucket_response))
        print('\n=========================\n')

        return create_bucket_response


    def delete_object_storage(object_storage_client):
        namespace = object_storage_client.get_namespace().data
        create_bucket_response = object_storage_client.create_bucket(
            namespace,
            oci.object_storage.models.CreateBucketDetails(
                name="poronix-results",
                compartment_id=compartment_id,
            )
        ).data

        print('Created storage bucket:\n{}'.format(create_bucket_response))
        print('\n=========================\n')

        return create_bucket_response


    def delete_network_security_group(virtual_network_composite_operations, network_security_group):
        virtual_network_composite_operations.delete_network_security_group_and_wait_for_state(
            network_security_group.id,
            wait_for_states=[oci.core.models.RouteTable.LIFECYCLE_STATE_TERMINATED]
        )

        print('Deleted Network Security Group: {}'.format(network_security_group.id))
        print()


    def add_network_security_group_security_rules(virtual_network_client, network_security_group):
        list_security_rules_response = virtual_network_client.list_network_security_group_security_rules(
            network_security_group.id
        )
        security_rules = list_security_rules_response.data

        print('Current Security Rules in Network Security Group')
        print('================================================')
        print('{}'.format(security_rules))
        print()

        add_security_rule_details = oci.core.models.AddSecurityRuleDetails(
            description="Incoming HTTP connections",
            direction="INGRESS",
            is_stateless=False,
            protocol="6",  # 1: ICMP, 6: TCP, 17: UDP, 58: ICMPv6
            source="0.0.0.0/0",
            source_type="CIDR_BLOCK",
            tcp_options=oci.core.models.TcpOptions(
                destination_port_range=oci.core.models.PortRange(min=80, max=80)
            )
        )
        add_security_rules_details = oci.core.models.AddNetworkSecurityGroupSecurityRulesDetails(
            security_rules=[add_security_rule_details]
        )
        virtual_network_client.add_network_security_group_security_rules(
            network_security_group.id,
            add_security_rules_details
        )

        list_security_rules_response = virtual_network_client.list_network_security_group_security_rules(
            network_security_group.id
        )
        security_rules = list_security_rules_response.data

        print('Updated Security Rules in Network Security Group')
        print('================================================')
        print('{}'.format(security_rules))
        print()


    def remove_network_security_group_security_rules(virtual_network_client, network_security_group):
        list_security_rules_response = virtual_network_client.list_network_security_group_security_rules(
            network_security_group.id
        )
        security_rules = list_security_rules_response.data
        security_rule_ids = [security_rule.id for security_rule in security_rules]
        remove_security_rules_details = oci.core.models.RemoveNetworkSecurityGroupSecurityRulesDetails(
            security_rule_ids=security_rule_ids
        )
        virtual_network_client.remove_network_security_group_security_rules(
            network_security_group.id,
            remove_security_rules_details
        )

        print('Removed all Security Rules in Network Security Group: {}'.format(network_security_group.id))
        print()


    def get_launch_instance_details(compartment_id, availability_domain, shape, image, subnet, ssh_public_key):

        # We can use instance metadata to specify the SSH keys to be included in the
        # ~/.ssh/authorized_keys file for the default user on the instance via the special "ssh_authorized_keys" key.
        #
        # We can also provide arbitrary string keys and string values. If you are providing these, you should consider
        # whether defined and freeform tags on an instance would better meet your use case. See:
        # https://docs.cloud.oracle.com/Content/Identity/Concepts/taggingoverview.htm for more information
        # on tagging
        instance_metadata = {
            'ssh_authorized_keys': ssh_public_key,
            'some_metadata_item': 'some_item_value'
        }

        # We can also provide a user_data key in the metadata that will be used by Cloud-Init
        # to run custom scripts or provide custom Cloud-Init configuration. The contents of this
        # key should be Base64-encoded data and the SDK offers a convenience function to transform
        # a file at a given path to that encoded data
        #
        # See: https://docs.cloud.oracle.com/api/#/en/iaas/20160918/datatypes/LaunchInstanceDetails
        # for more information
        instance_metadata['user_data'] = oci.util.file_content_as_launch_instance_user_data(
            'user_data.sh'
        )

        # Extended metadata differs from normal metadata in that it can support nested maps/dicts. If you are providing
        # these, you should consider whether defined and freeform tags on an instance would better meet your use case.
        instance_extended_metadata = {
            'string_key_1': 'string_value_1',
            'map_key_1': {
                'string_key_2': 'string_value_2',
                'map_key_2': {
                    'string_key_3': 'string_value_3'
                },
                'empty_map_key': {}
            }
        }

        instance_name = 'py_sdk_example_instance'
        instance_source_via_image_details = oci.core.models.InstanceSourceViaImageDetails(
            image_id=image.id
        )
        create_vnic_details = oci.core.models.CreateVnicDetails(
            subnet_id=subnet.id
        )
        launch_instance_details = oci.core.models.LaunchInstanceDetails(
            display_name=instance_name,
            compartment_id=compartment_id,
            availability_domain=availability_domain,
            shape=shape.shape,
            metadata=instance_metadata,
            extended_metadata=instance_extended_metadata,
            source_details=instance_source_via_image_details,
            create_vnic_details=create_vnic_details,
            shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
                            ocpus=OCPU,
                            memory_in_gbs=RAM)
        )
        return launch_instance_details


    def launch_instance(compute_client_composite_operations, launch_instance_details):
        launch_instance_response = compute_client_composite_operations.launch_instance_and_wait_for_state(
            launch_instance_details,
            wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_RUNNING]
        )
        instance = launch_instance_response.data

        print('Launched Instance: {}'.format(instance.id))
        print('{}'.format(instance))
        print()

        return instance


    def launch_instance_and_wait_for_work_request(compute_client_composite_operations, launch_instance_details):
        work_request_response = compute_client_composite_operations.launch_instance_and_wait_for_work_request(
            launch_instance_details
        )
        work_request = work_request_response.data

        # Now retrieve the instance details from the information in the work request resources
        instance_id = work_request.resources[0].identifier
        get_instance_response = compute_client_composite_operations.client.get_instance(instance_id)
        instance = get_instance_response.data

        return instance, work_request.id


    def terminate_instance(compute_client_composite_operations, instance):
        print('Terminating Instance: {}'.format(instance.id))
        compute_client_composite_operations.terminate_instance_and_wait_for_state(
            instance.id,
            wait_for_states=[oci.core.models.Instance.LIFECYCLE_STATE_TERMINATED]
        )

        print('Terminated Instance: {}'.format(instance.id))
        print()


    def print_instance_details(compute_client, virtual_network_client, instance):
        # We can find the private and public IP address of the instance by getting information on its VNIC(s). This
        # relationship is indirect, via the VnicAttachments of an instance

        # Note that listing VNIC attachments is a paginated operation so we can use the oci.pagination module to avoid
        # having to manually deal with page tokens.
        #
        # Since we're only interested in our specific instance, we can pass that as a filter to the list operation
        list_vnic_attachments_response = oci.pagination.list_call_get_all_results(
            compute_client.list_vnic_attachments,
            compartment_id,
            instance_id=instance.id
        )
        vnic_attachments = list_vnic_attachments_response.data

        vnic_attachment = vnic_attachments[0]
        get_vnic_response = virtual_network_client.get_vnic(vnic_attachment.vnic_id)
        vnic = get_vnic_response.data

        print('Virtual Network Interface Card')
        print('==============================')
        print('{}'.format(vnic))
        print()


    def print_work_request_details(work_request_client, work_request_id):
        get_work_request_response = work_request_client.get_work_request(work_request_id)
        work_request_details = get_work_request_response.data

        list_errors_response = work_request_client.list_work_request_errors(work_request_id)
        work_request_errors = list_errors_response.data

        print('Work Request Details')
        print('====================')
        print('{}'.format(work_request_details))
        print()

        print('Work Request Errors')
        print('===================')
        if len(work_request_errors) > 0:
            print('{}'.format(work_request_errors))
        else:
            print('No errors occurred.')
        print()

        print('Work Request Logs')
        print('=================')

        # Limit to 20 log entries
        log_limit = 20
        page_size = 5
        resp = oci.pagination.list_call_get_up_to_limit(work_request_client.list_work_request_logs, log_limit, page_size, work_request_id)
        for work_request_log in resp.data:
            print('{}'.format(work_request_log))
        print()


    if __name__ == "__main__":
