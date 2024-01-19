# Testing PHP performance on the EC2 instances
I have used AWS CDK and the Phoronix test suite.

Tests were executed into M, C, and T instances, all in the large type configuration (the smaller), 

  "m5n.large",
  "m5a.large",
  "m5zn.large",
  "m5ad.large",
  "m5dn.large",
  "m5nl.large",
  "m5.large",
  "m5d.large",
  "m6g.large",
  "c5.large",
  "c5n.large",
  "c5d.large",
  "c5ad.large",
  "c5a.large",
  "c6gd.large",
  "c6g.large",
  "c6gn.large",
  "t3.large",
  "t3a.large",
  "t2.large",
  "t4g.large"

## Start the tests
cdk deploy --all --require-approval never