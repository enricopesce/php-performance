#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "@aws-cdk/core";
import { PhpPerfomanceEc2Stack } from "../lib/php-perfomance-ec2-stack";
import { PhpPerfomanceS3Stack } from "../lib/php-perfomance-s3-stack";

const app = new cdk.App();

const env_us_east_1 = {
  account: "ACCOUNT_ID",
  region: "us-east-1",
};

const bucket = new PhpPerfomanceS3Stack(app, "PhpPerformance-S3", { env: env_us_east_1 });

const instances = [
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
  "t4g.large",
]; 


for (const instance of instances) {
  new PhpPerfomanceEc2Stack(
    app,
    "PhpPerformance-" + instance.replace(".", "-"),
    instance,
    bucket.myBucket,
    "KEYNAME",
    "VPCID",
    {
      env: env_us_east_1,
    }
  );
}
