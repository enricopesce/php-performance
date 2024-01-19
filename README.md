# Testing PHP performance over different cloud providers

This test aims to assess the enhancements made to internal PHP functions, focusing specifically on their performance. It does not replicate a real web workload or involve testing a LAMP stack; rather, its emphasis lies in gauging the speed and efficiency of these functions.

I am conducting single-thread tests rather than testing multicore workloads since PHP is not designed for multi-threading or multi-core processing. The objective of my testing is to determine the execution time of a single PHP script, essentially gauging the performance of a web page in terms of low Time To First Byte (TTFB) and optimal User Experience (UX).

In my view, focusing on testing a single script is not a drawback; rather, it serves the purpose of pinpointing the most efficient hardware for script execution. If you looking for the maximum performance this fundamental concept is pivotal, as it constitutes the primary criterion for selecting and scaling real workload traffic.

Test are executed by "Phoronix test suite" 

The tests are the following

https://openbenchmarking.org/test/pts/php
https://openbenchmarking.org/test/pts/phpbench

 The AWS test was conducted in 2021 is outdated and requires an update. You can find the results in the [aws](aws) folder.
 
A test was done on Oracle Cloud Infrastructure (OCI) in 2024 you can find the results on [oci](oci)folder