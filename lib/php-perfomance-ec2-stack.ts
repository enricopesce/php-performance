import * as cdk from "@aws-cdk/core";
import * as ec2 from "@aws-cdk/aws-ec2";
import * as s3 from "@aws-cdk/aws-s3";
import * as iam from "@aws-cdk/aws-iam";
import * as fs from "fs";

export class PhpPerfomanceEc2Stack extends cdk.Stack {
  constructor(
    scope: cdk.Construct,
    id: string,
    instanceType: string,
    bucket: s3.Bucket,
    key: string,
    vpcID: string,
    props?: cdk.StackProps
  ) {
    super(scope, id, props);
    const vpc = ec2.Vpc.fromLookup(this, "Vpc", {
      vpcId: vpcID,
    });

    const sg = new ec2.SecurityGroup(this, "sg", {
      vpc: vpc,
      allowAllOutbound: true,
    });

    sg.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), "Allows SSH access");

    const role = new iam.Role(this, "MyRole", {
      assumedBy: new iam.ServicePrincipal("ec2.amazonaws.com"),
    });

    role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: [bucket.bucketArn],
        actions: ["s3:ListBucket"],
      })
    );

    role.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        resources: [bucket.bucketArn + "/*"],
        actions: ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      })
    );

    let phpInstance: ec2.Instance;

    if (instanceType.startsWith("m6g") || instanceType.startsWith("c6g") || instanceType.startsWith("t4g")) {
      phpInstance = new ec2.Instance(this, "Instance", {
        instanceType: new ec2.InstanceType(instanceType),
        machineImage: ec2.MachineImage.latestAmazonLinux({
          cpuType: ec2.AmazonLinuxCpuType.ARM_64,
          generation: ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
        }),
        vpc: vpc,
        securityGroup: sg,
        keyName: "test",
        vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
        role: role,
      });
    } else {
      phpInstance = new ec2.Instance(this, "Instance", {
        instanceType: new ec2.InstanceType(instanceType),
        machineImage: ec2.MachineImage.latestAmazonLinux({
          cpuType: ec2.AmazonLinuxCpuType.X86_64,
          generation: ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
        }),
        vpc: vpc,
        securityGroup: sg,
        keyName: key,
        vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
        role: role,
      });
    }

    phpInstance.addUserData("sudo su -");

    phpInstance.addUserData('echo "export S3ENDPOINT=s3://' + bucket.bucketName + '" >> /root/.bashrc');
    phpInstance.addUserData(
      'echo "export TEST_RESULTS_NAME=ec2-php-' + instanceType.replace(".", "") + '" >> /root/.bashrc'
    );
    phpInstance.addUserData('echo "export TEST_RESULTS_DESCRIPTION=Testing" >> /root/.bashrc');
    phpInstance.addUserData("source ~/.bashrc");

    phpInstance.addUserData(fs.readFileSync("lib/user_script.sh", "utf8"));

    new cdk.CfnOutput(this, "instance", {
      value: phpInstance.instancePublicIp,
    });
  }
}
