#! /bin/bash
export OCI_CLI_AUTH=instance_principal

# stop cpu tasks
systemctl stop dnf-makecache.timer
systemctl stop dnf-system-upgrade.service
systemctl stop dnf-system-upgrade-cleanup.service
systemctl stop dnf-makecache.service
systemctl stop oracle-cloud-agent.service
systemctl stop oracle-cloud-agent-updater.service

# update dependencies
dnf -y install oraclelinux-developer-release-el8 python36-oci-cli

# install and configure phoronix
cd /root
wget https://phoronix-test-suite.com/releases/phoronix-test-suite-10.8.4.tar.gz
tar xzvf phoronix-test-suite-10.8.4.tar.gz
cd phoronix-test-suite/
./install-sh

touch /etc/phoronix-test-suite.xml
chmod 666 /etc/phoronix-test-suite.xml

echo '<?xml version="1.0"?>
<!--Phoronix Test Suite v10.8.4-->
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

# export SKIP_EXTERNAL_DEPENDENCIES=1
export TEST_RESULTS_NAME=$(oci-metadata --get TEST_RESULTS_NAME --value)

# Install PHP 7.2
export TEST_RESULTS_IDENTIFIER="php72"
dnf module switch-to php:7.2 -y
dnf install php-cli php-pdo php-fpm php-json php-mysqlnd php-dom php-gd php-process -y
phoronix-test-suite batch-benchmark pts/php
dnf remove 'php*' -y

# Install PHP 7.3
export TEST_RESULTS_IDENTIFIER="php73"
dnf module switch-to php:7.3 -y
dnf install php-cli php-pdo php-fpm php-json php-mysqlnd php-dom php-gd php-process -y
phoronix-test-suite batch-benchmark pts/php
dnf remove 'php*' -y

# Install PHP 7.4
export TEST_RESULTS_IDENTIFIER="php74"
dnf module switch-to php:7.4 -y
dnf install php-cli php-pdo php-fpm php-json php-mysqlnd php-dom php-gd php-process -y
phoronix-test-suite batch-benchmark pts/php
dnf remove 'php*' -y

# Install PHP 8.0
export TEST_RESULTS_IDENTIFIER="php80"
dnf module switch-to php:8.0 -y
dnf install php-cli php-pdo php-fpm php-json php-mysqlnd php-dom php-gd php-process -y
phoronix-test-suite batch-benchmark pts/php

phoronix-test-suite result-file-to-csv $TEST_RESULTS_NAME

oci os object put --force --bucket-name phoronix --file /root/$TEST_RESULTS_NAME.csv

#oci compute instance action --instance-id $(oci-metadata --get id --value-only) --action SOFTSTOP