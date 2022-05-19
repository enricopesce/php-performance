# Testing PHP performance on the EC2 instances

Inspired by the test published by AWS [Improving performance of PHP for Arm64 and impact on AWS Graviton2 based EC2 instances](https://aws.amazon.com/blogs/compute/improving-performance-of-php-for-arm64-and-impact-on-amazon-ec2-m6g-instances/) I was curious to know the performance of the PHP language on the existing EC2 instances.

I'm not a performance engineer, exactly for this reason I share this project transparently to share my discoveries and get feedback (GitHub issue).

I have created this tool principally to test PHP performance over some EC2 instances. 

To do this, I have used AWS CDK and the Phoronix test suite.

AWS CDK creates an S3 bucket and the EC2 instances and injects via Cloud Formation the Phoronix commands, all simple.

The results are stored inside the S3 bucket, is there a big shortage in this part you need to copy the results and create your report manually! I'm sorry :)

The tests are the following

https://openbenchmarking.org/test/pts/php
https://openbenchmarking.org/test/pts/phpbench

## DISCLAIMER :)
My point of view (probably wrong):

This test is used to identify the improvements of internal PHP functions, it is not a real web workload, I don't test a LAMP stack but how fast these functions are! (Maybe, is it not similar to a mix of PHP scripts executed in a real workload?)

I'm not testing multicore workload, these tests are single-thread tests, PHP is not multi-thread or multi-core and the scope of my test is to identify how much time needs a single PHP script to be executed, in other words, a web page to be executed (low TTFB, best UX, etc)

Yes, maybe it is the best scenario, not really in a production environment, but if PHP is not multi-core and multi-thread, if you need more power you need to scale horizontally, not replacing the CPU with a new best multi-core CPU, in this case, you need a new CPU with higher Mhz, usually, the PHP scripts are small executions and busy a CPU for a very small time.

After these ruminations, in my opinion, it is not bad to test only a single script on small EC2 instance types, I need the fastest execution and the scaling is another aspect served by a balancer over tons of instances.

Finally, the tests were executed into M, C, and T instances, all in the large type configuration (the smaller), 

The results are stored in the results directory.

Some links that inspired me:

https://www.klik-mall.com/web/development/2-new-php-performance-numbers-for-a-better-estimate-of-real-life-performance-by-a-specific-cpu/5087

## Start the tests

    cdk deploy --all --require-approval never --context vpcid=YOURVPCID --context accountid=YOURACCOUNTID --context region=AWSREGION --context ec2key=YOURKEYNAME


## Sponsor 

Thanks so much to [Soisy S.p.A.](https://www.soisy.it/) for the sponsorship of this project!