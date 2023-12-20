#! /bin/bash

echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# update dependencies
yum -y update
yum groupinstall "Development Tools" -y

# install and configure phoronix
wget https://phoronix-test-suite.com/releases/phoronix-test-suite-10.4.0.tar.gz
tar xzvf phoronix-test-suite-10.4.0.tar.gz
cd phoronix-test-suite/
./install-sh

echo '<?xml version="1.0"?>
<!--Phoronix Test Suite v10.4.0-->
<PhoronixTestSuite>
  <Options>
    <OpenBenchmarking>
      <AnonymousUsageReporting>TRUE</AnonymousUsageReporting>
      <IndexCacheTTL>3</IndexCacheTTL>
      <AlwaysUploadSystemLogs>FALSE</AlwaysUploadSystemLogs>
      <AllowResultUploadsToOpenBenchmarking>TRUE</AllowResultUploadsToOpenBenchmarking>
    </OpenBenchmarking>
    <General>
      <DefaultBrowser></DefaultBrowser>
      <UsePhodeviCache>TRUE</UsePhodeviCache>
      <DefaultDisplayMode>DEFAULT</DefaultDisplayMode>
      <PhoromaticServers></PhoromaticServers>
      <FullOutput>FALSE</FullOutput>
      <ColoredConsole>AUTO</ColoredConsole>
    </General>
    <Modules>
      <AutoLoadModules>toggle_screensaver, update_checker, perf_tips, ob_auto_compare, load_dynamic_result_viewer</AutoLoadModules>
    </Modules>
    <Installation>
      <RemoveDownloadFiles>FALSE</RemoveDownloadFiles>
      <SearchMediaForCache>TRUE</SearchMediaForCache>
      <SymLinkFilesFromCache>FALSE</SymLinkFilesFromCache>
      <PromptForDownloadMirror>FALSE</PromptForDownloadMirror>
      <EnvironmentDirectory>~/.phoronix-test-suite/installed-tests/</EnvironmentDirectory>
      <CacheDirectory>~/.phoronix-test-suite/download-cache/</CacheDirectory>
    </Installation>
    <Testing>
      <SaveSystemLogs>TRUE</SaveSystemLogs>
      <SaveInstallationLogs>TRUE</SaveInstallationLogs>
      <SaveTestLogs>TRUE</SaveTestLogs>
      <RemoveTestInstallOnCompletion></RemoveTestInstallOnCompletion>
      <ResultsDirectory>~/.phoronix-test-suite/test-results/</ResultsDirectory>
      <AlwaysUploadResultsToOpenBenchmarking>FALSE</AlwaysUploadResultsToOpenBenchmarking>
      <AutoSortRunQueue>TRUE</AutoSortRunQueue>
      <ShowPostRunStatistics>TRUE</ShowPostRunStatistics>
    </Testing>
    <TestResultValidation>
      <DynamicRunCount>TRUE</DynamicRunCount>
      <LimitDynamicToTestLength>20</LimitDynamicToTestLength>
      <StandardDeviationThreshold>2.5</StandardDeviationThreshold>
      <ExportResultsTo></ExportResultsTo>
      <MinimalTestTime>10</MinimalTestTime>
      <DropNoisyResults>FALSE</DropNoisyResults>
    </TestResultValidation>
    <ResultViewer>
      <WebPort>RANDOM</WebPort>
      <LimitAccessToLocalHost>TRUE</LimitAccessToLocalHost>
      <AccessKey></AccessKey>
      <AllowSavingResultChanges>TRUE</AllowSavingResultChanges>
      <AllowDeletingResults>TRUE</AllowDeletingResults>
    </ResultViewer>
    <BatchMode>
      <SaveResults>TRUE</SaveResults>
      <OpenBrowser>FALSE</OpenBrowser>
      <UploadResults>FALSE</UploadResults>
      <PromptForTestIdentifier>FALSE</PromptForTestIdentifier>
      <PromptForTestDescription>FALSE</PromptForTestDescription>
      <PromptSaveName>FALSE</PromptSaveName>
      <RunAllTestCombinations>TRUE</RunAllTestCombinations>
      <Configured>TRUE</Configured>
    </BatchMode>
    <Networking>
      <NoInternetCommunication>FALSE</NoInternetCommunication>
      <NoNetworkCommunication>FALSE</NoNetworkCommunication>
      <Timeout>20</Timeout>
      <ProxyAddress></ProxyAddress>
      <ProxyPort></ProxyPort>
      <ProxyUser></ProxyUser>
      <ProxyPassword></ProxyPassword>
    </Networking>
    <Server>
      <RemoteAccessPort>RANDOM</RemoteAccessPort>
      <Password></Password>
      <WebSocketPort>RANDOM</WebSocketPort>
      <AdvertiseServiceZeroConf>TRUE</AdvertiseServiceZeroConf>
      <AdvertiseServiceOpenBenchmarkRelay>TRUE</AdvertiseServiceOpenBenchmarkRelay>
      <PhoromaticStorage>~/.phoronix-test-suite/phoromatic/</PhoromaticStorage>
    </Server>
  </Options>
</PhoronixTestSuite>' > /etc/phoronix-test-suite.xml


# Install PHP 7.1
amazon-linux-extras enable php7.1
yum clean metadata
yum install php-cli php-pdo php-fpm php-json php-mysqlnd php-dom php-gd -y
TEST_RESULTS_IDENTIFIER=php71 phoronix-test-suite batch-benchmark pts/php
yum remove php* -y
amazon-linux-extras disable php7.1

# Install PHP 7.2
amazon-linux-extras enable php7.2
yum clean metadata
yum install php-cli php-pdo php-fpm php-json php-mysqlnd php-dom php-gd -y
TEST_RESULTS_IDENTIFIER=php72 phoronix-test-suite batch-benchmark pts/php
yum remove php* -y
amazon-linux-extras disable php7.2

# Install PHP 7.4
amazon-linux-extras enable php7.4
yum clean metadata
yum install php-cli php-pdo php-fpm php-json php-mysqlnd php-dom php-gd -y
TEST_RESULTS_IDENTIFIER=php74 phoronix-test-suite batch-benchmark pts/php
yum remove php* -y
amazon-linux-extras disable php7.4

# Install PHP 8.0
amazon-linux-extras enable php8.0
yum clean metadata
yum install php-cli php-pdo php-fpm php-json php-mysqlnd php-dom php-gd -y
TEST_RESULTS_IDENTIFIER=php8 phoronix-test-suite batch-benchmark pts/php

phoronix-test-suite result-file-to-csv $TEST_RESULTS_NAME

aws s3 cp /var/lib/phoronix-test-suite/$TEST_RESULTS_NAME.csv $S3ENDPOINT

shutdown -h now