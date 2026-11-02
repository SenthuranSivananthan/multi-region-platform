---
title: Storage across regions
description: Plan Azure Storage high availability and disaster recovery by criticality tier, compare supported objects, and choose an illustrated replication pattern.
ms.date: 11/02/2026
ms.topic: conceptual
---

# Storage across regions

## Summary

- **High availability - within a region:** Default to [ZRS](#high-availability-scenarios) where supported for zonal read/write availability. Use the [replication patterns](#replication-patterns) to evaluate additional options: GZRS for regional recovery, RA-GZRS for secondary reads, or customer-managed and partner replication for workload-specific control.
- **High availability - across paired regions:** Use [GRS or one of its variants](#platform-native-geo-replication) (RA-GRS, GZRS, or RA-GZRS) for eligible account-wide replication to the Azure-assigned paired region. Choose GZRS for zonal HA as well, and a read-access variant for secondary reads. Geo-replication is asynchronous; secondary writes require failover.
- **Disaster recovery - across paired regions:** [Platform-native replication, account failover, and failback](#platform-native-geo-replication) are limited to Azure-assigned paired regions. Use GRS for eligible account-wide replication, or GZRS when zonal HA is also required. Read-access variants add eligible secondary reads during recovery. Plan and test potential data loss and recovery procedures; replication alone does not restore the workload.
- **Disaster recovery - customer chosen regions:** Use [Blob Object Replication](#storage-pattern-2) for eligible block blobs across multiple destination accounts, [customer-orchestrated copy](#storage-pattern-3) for supported Blob, ADLS Gen2, or Files datasets, and [customer-managed or partner replication](#storage-pattern-4) for service-specific needs, including Queues and Tables. For Databricks workloads, evaluate [workload-specific replication and recovery](#storage-pattern-5).
- **Recovery from unwanted changes:** Complement regional DR with [isolated vaulted backup](#complement-replication-with-isolated-backup) where supported, accounting for backup frequency and restore duration. [Operational backup](#operational-backup-for-blobs) provides local logical recovery, not an independent regional recovery copy.
- **Match protection to criticality:** Use the [HA](#high-availability-scenarios) and [DR](#disaster-recovery-scenarios) tier tables as planning candidates, not guarantees. Validate RTO, RPO, [endpoints, DNS, key dependencies, and cost](#design-consideration), and recovery procedures; asynchronous replication and scheduled backups do not establish near-zero regional RPO.

<a id="paired-region-options"></a>

## Platform-native geo-replication

GRS and GZRS asynchronously replicate an eligible storage account to the Azure-assigned paired region. The secondary is a replica of the same logical account, not an independently configured destination account. A region pair alone does not establish support: confirm account type, service, redundancy, and regional availability.

| Scenario | Storage-account-level failover and failback support |
| --- | --- |
| **Paired regions** | **Supported** for customer-managed and Microsoft-managed failover and failback, subject to account, service, and feature eligibility. Includes Blob, ADLS Gen2, Files, Queues, and Tables. |
| **Non-paired regions** | **Not Supported** for either customer-managed or Microsoft-managed storage-account-level failover and failback. Use independent accounts and a supported replication or copy pattern instead. |

Microsoft-managed failover is a Microsoft-directed regional disaster action, not an operation customers can request for an individual storage account. Use customer-managed failover and failback to plan and test workload recovery.

Read-access variants, RA-GRS and RA-GZRS, expose a separate secondary read endpoint for supported services. They do not make the secondary writable. Evaluate [customer-managed planned and unplanned failover and failback](https://learn.microsoft.com/azure/storage/common/storage-disaster-recovery-guidance) separately from replication; eligibility and recovery behavior vary.

<a id="high-availability"></a>

## High Availability scenarios

For Azure Storage, **high availability (HA)** means keeping reads and writes available through routine infrastructure faults and availability-zone disruptions within a region.

> [!NOTE]
> **Default to ZRS.** Start with **zone-redundant storage (ZRS)** where supported: it synchronously replicates data across availability zones. GZRS combines this zonal foundation with asynchronous cross-region replication. Design cross-region continuity only after within-region HA is addressed. See [Data redundancy - Azure Storage](https://learn.microsoft.com/azure/storage/common/storage-redundancy#zone-redundant-storage).
>
> The options below are organized by workload criticality tier to help you evaluate storage solutions in your own context. Assess each option against your business requirements, recovery objectives, supported storage services, cost, and operational capabilities; the tier alone does not determine the right solution. For further guidance, see [Develop a disaster recovery plan for multi-region deployments](https://learn.microsoft.com/azure/well-architected/design-guides/disaster-recovery).

| Criticality tier | Paired regions | Customer chosen regions |
| --- | --- | --- |
| **Tier 0 - Mission Critical**<br>RTO seconds / RPO near zero | <ul><li>[GZRS with Geo-Priority Replication](#storage-pattern-1) - combines zonal HA with prioritized paired-region replication where eligible; regional recovery still requires failover.</li><li>[RA-GZRS with Geo-Priority Replication](#storage-pattern-1) - adds eligible secondary reads to zonal HA and prioritized geo-replication, but not secondary writes.</li><li>[Workload-managed replication](#storage-pattern-4) - gives the application control over consistency and cutover; prove seconds-level RTO and near-zero RPO.</li></ul> | <ul><li>[Blob Object Replication with Priority](#storage-pattern-2) - prioritizes selected block-blob copies for regional continuity; its eligible 15-minute replication SLA does not meet near-zero RPO.</li><li>[Azure Storage partners](https://learn.microsoft.com/azure/storage/solution-integration/validated-partners/primary-secondary-storage/partner-overview) - evaluate specialist replication and failover capabilities against the workload's seconds-level RTO and near-zero RPO.</li><li>[Workload-managed replication](#storage-pattern-4) - allows customer chosen regions and application-controlled consistency and cutover; validate the full Tier 0 recovery path.</li></ul> |
| **Tier 1 - Business Critical**<br>RTO / RPO minutes | <ul><li>[GZRS with Geo-Priority Replication](#storage-pattern-1) - combines zonal HA with prioritized regional replication where eligible; verify replication lag and failover against minutes-level targets.</li><li>[RA-GZRS with Geo-Priority Replication](#storage-pattern-1) - supports eligible secondary reads during primary-region disruption while write recovery follows the failover procedure.</li><li>[Workload-managed replication](#storage-pattern-4) - lets the application control change propagation and endpoint cutover to match its recovery objectives.</li></ul> | <ul><li>[Blob Object Replication with Priority](#storage-pattern-2) - provides prioritized block-blob copies with an eligible 15-minute replication SLA; use only when that window fits the workload's RPO.</li><li>[Azure Storage partners](https://learn.microsoft.com/azure/storage/solution-integration/validated-partners/primary-secondary-storage/partner-overview) - offers service-specific replication and failover approaches; verify that the chosen solution meets minutes-level objectives.</li><li>[Workload-managed replication](#storage-pattern-4) - enables application-specific regional copies and cutover behavior when native options do not fit.</li></ul> |
| **Tier 2 - Business Operational**<br>RTO / RPO hours | <ul><li>[GZRS](#storage-pattern-1) - retains zonal HA and adds Azure-managed regional recovery when replication lag and failover fit the allowed recovery window.</li><li>[RA-GZRS](#storage-pattern-1) - adds eligible secondary read continuity while writes wait for regional recovery actions.</li></ul> | <ul><li>[Blob Object Replication](#storage-pattern-2) - maintains an accessible copy of selected block blobs; measure replication lag and application cutover against hours-level targets.</li><li>[Storage Mover](#storage-mover) - supports batch seeding and refresh when the schedule fits the target; its 24-hour planning RPO must be validated.</li><li>[Data Factory](#azure-data-factory-synapse-pipelines) - schedules and monitors incremental copy workflows for supported datasets when job-based replication lag is acceptable.</li><li>[Azure Storage partners](https://learn.microsoft.com/azure/storage/solution-integration/validated-partners/primary-secondary-storage/partner-overview) - addresses service or operational requirements not covered by native tools; validate hours-level recovery and cost.</li><li>[AzCopy](#azcopy) - provides initial and incremental copies without a custom data-transfer engine; customers own scheduling, retries, and validation.</li></ul> |
| **Tier 3 - Administrative**<br>RTO hours-days / RPO hours | <ul><li>[GZRS](#storage-pattern-1) - combines zonal HA with an account-wide regional copy without customer-operated copy jobs.</li><li>[RA-GZRS](#storage-pattern-1) - adds eligible secondary reads when useful, while allowing a longer window for write recovery.</li></ul> | <ul><li>[Blob Object Replication](#storage-pattern-2) - provides policy-based block-blob copies without a customer-run copy schedule; validate lag against the required RPO.</li><li>[Storage Mover](#storage-mover) - supports batch-oriented data movement when longer recovery windows are acceptable; validate the 24-hour planning RPO.</li><li>[Data Factory](#azure-data-factory-synapse-pipelines) - automates scheduled copy workflows when pipeline development and operations are justified.</li><li>[Azure Storage partners](https://learn.microsoft.com/azure/storage/solution-integration/validated-partners/primary-secondary-storage/partner-overview) - provides validated service-specific alternatives; balance required protection against licensing and operational overhead.</li><li>[AzCopy](#azcopy) - supports scripting-based scheduled copies when the workload can tolerate the copy interval and customer-managed recovery.</li></ul> |

<a id="disaster-recovery"></a>

## Disaster Recovery scenarios

For Azure Storage, **disaster recovery (DR)** means restoring a usable data copy and application access after a regional outage, destructive change, or other major disruption. Regional DR typically involves cross-region replication, failover or endpoint redirection, recovery validation, and failback. Backup complements this by recovering a retained point in time; whether it can recover a regional outage depends on where recovery copies and supported restore targets are available.

> [!IMPORTANT]
> <a id="complement-replication-with-isolated-backup"></a>
> <a id="region-of-choice-backup-preview"></a>
>
> **Complement replication with isolated backup**
>
> Azure Backup provides vaulted backup for [ADLS Gen2](https://learn.microsoft.com/azure/backup/azure-data-lake-storage-backup-overview) and [Azure Blobs](https://learn.microsoft.com/azure/backup/blob-backup-overview). It provides an isolated, managed recovery copy with ransomware protection, administrative separation, long retention, and recovery to a retained point in time. This is a restore-based recovery option, not another live replication endpoint.
>
> Backup frequency determines the RPO, which is usually measured in hours or more. Recovery takes longer because data must be restored from the vault. The published [support matrix](https://learn.microsoft.com/azure/backup/azure-data-lake-storage-backup-support-matrix) requires the vault to be in the source account's region. Do not assume backup or recovery in arbitrary customer chosen regions; validate any separately offered preview and its terms before relying on it.
>
> <a id="operational-backup-for-blobs"></a>
>
> **Operational backup for blobs**
>
> [Operational backup](https://learn.microsoft.com/azure/backup/blob-backup-overview) uses point-in-time restore, soft delete, change feed, and blob versioning to retain supported block-blob changes locally in the source account. It does not copy data into an isolated backup vault. Use it for supported accidental-deletion or corruption recovery, alongside the regional recovery pattern, not as a substitute for one. Validate restore scope, retained recovery points, and recovery duration.

> [!NOTE]
> The options below are organized by workload criticality tier to help you evaluate storage solutions in your own context. Assess each option against your business requirements, recovery objectives, supported storage services, cost, and operational capabilities; the tier alone does not determine the right solution. For further guidance, see [Develop a disaster recovery plan for multi-region deployments](https://learn.microsoft.com/azure/well-architected/design-guides/disaster-recovery).

| Criticality tier | Paired regions | Customer chosen regions |
| --- | --- | --- |
| **Tier 0 - Mission Critical**<br>RTO seconds / RPO near zero | <ul><li>[GRS with Geo-Priority Replication](#storage-pattern-1) - prioritizes paired-region copies where eligible; asynchronous replication alone does not establish Tier 0 recovery.</li><li>[GZRS with Geo-Priority Replication](#storage-pattern-1) - combines zonal HA with prioritized regional copies; validate the full failover path against seconds-level RTO and near-zero RPO.</li><li>[RA-GZRS with Geo-Priority Replication](#storage-pattern-1) - adds eligible secondary reads during regional recovery; write access still requires failover.</li><li>[Azure Backup - Vaulted Backup for HNS and Blob](#complement-replication-with-isolated-backup) - isolates retained restore points for destructive changes; its 24-hour planning RPO complements, rather than meets, Tier 0 targets.</li><li>[Azure Backup - Operational Backup for Blob](#operational-backup-for-blobs) - recovers supported deletion or corruption locally, not a regional outage.</li></ul> | <ul><li>[Azure Databricks Managed Disaster Recovery](https://learn.microsoft.com/azure/databricks/admin/managed-disaster-recovery) - provides workload-specific recovery for supported Databricks workloads; validate scope and Tier 0 objectives.</li><li>[Azure Backup to customer chosen regions](#region-of-choice-backup-preview) - may address recovery-location requirements (**Limited preview**); validate restore-based recovery against Tier 0 objectives.</li><li>[Azure Storage partners](https://learn.microsoft.com/azure/storage/solution-integration/validated-partners/primary-secondary-storage/partner-overview) - evaluate specialist replication and failover for seconds-level RTO and near-zero RPO.</li></ul> |
| **Tier 1 - Business Critical**<br>RTO / RPO minutes | <ul><li>[GRS with Geo-Priority Replication](#storage-pattern-1) - prioritizes managed paired-region replication where eligible; measure lag and failover against minutes-level targets.</li><li>[GZRS with Geo-Priority Replication](#storage-pattern-1) - adds zonal HA to prioritized regional replication when both zone and region protection are needed.</li><li>[RA-GZRS with Geo-Priority Replication](#storage-pattern-1) - supports eligible secondary reads while the workload completes write failover and recovery.</li><li>[Azure Backup - Vaulted Backup for HNS and Blob](#complement-replication-with-isolated-backup) - adds isolated point-in-time recovery for unwanted changes; its 24-hour planning RPO does not meet minutes-level targets.</li><li>[Azure Backup - Operational Backup for Blob](#operational-backup-for-blobs) - complements regional replication with local recovery from supported deletion or corruption.</li></ul> | <ul><li>[Azure Databricks Managed Disaster Recovery](https://learn.microsoft.com/azure/databricks/admin/managed-disaster-recovery) - provides recovery tailored to supported Databricks workloads; verify minutes-level RTO and RPO.</li><li>[Azure Backup to customer chosen regions](#region-of-choice-backup-preview) - may provide a required restore location (**Limited preview**); verify recovery-point age and restore time.</li><li>[Azure Storage partners](https://learn.microsoft.com/azure/storage/solution-integration/validated-partners/primary-secondary-storage/partner-overview) - offers service-specific replication and failover when native recovery does not fit; validate minutes-level objectives.</li></ul> |
| **Tier 2 - Business Operational**<br>RTO / RPO hours | <ul><li>[GRS](#storage-pattern-1) - provides Azure-managed account-wide regional copies when replication lag and failover fit hours-level targets.</li><li>[GZRS](#storage-pattern-1) - adds zonal HA to the regional recovery copy without customer-operated replication jobs.</li><li>[Azure Backup - Vaulted Backup for HNS and Blob](#complement-replication-with-isolated-backup) - provides isolated retained restore points; validate the 24-hour planning RPO and restore duration against the required hours-level window.</li><li>[Azure Backup - Operational Backup for Blob](#operational-backup-for-blobs) - restores supported local changes without a separate vault restore; it is not an independent regional recovery copy.</li></ul> | <ul><li>[Azure Databricks Managed Disaster Recovery](https://learn.microsoft.com/azure/databricks/admin/managed-disaster-recovery) - uses a workload-specific recovery approach for supported Databricks deployments; validate hours-level recovery.</li><li>[Azure Backup to customer chosen regions](#region-of-choice-backup-preview) - may support restore-location requirements (**Limited preview**); assess backup frequency and restore duration.</li><li>[Azure Storage partners](https://learn.microsoft.com/azure/storage/solution-integration/validated-partners/primary-secondary-storage/partner-overview) - addresses service or region requirements beyond native options; validate hours-level recovery and cost.</li></ul> |
| **Tier 3 - Administrative**<br>RTO hours-days / RPO hours | <ul><li>[GRS](#storage-pattern-1) - provides managed regional replication when the workload can tolerate the tested failover window and data-loss exposure.</li><li>[GZRS](#storage-pattern-1) - retains zonal HA alongside regional DR when availability-zone resilience is also required.</li><li>[Azure Backup - Vaulted Backup for HNS and Blob](#complement-replication-with-isolated-backup) - supports retained-point recovery when longer restore windows are acceptable; validate the 24-hour planning RPO.</li><li>[Azure Backup - Operational Backup for Blob](#operational-backup-for-blobs) - provides local logical recovery alongside regional DR, without creating an independent regional copy.</li></ul> | <ul><li>[Azure Databricks Managed Disaster Recovery](https://learn.microsoft.com/azure/databricks/admin/managed-disaster-recovery) - provides recovery tailored to supported Databricks workloads when its scope and recovery windows fit.</li><li>[Azure Backup to customer chosen regions](#region-of-choice-backup-preview) - may address restore-location needs when longer recovery windows are acceptable (**Limited preview**).</li><li>[Azure Storage partners](https://learn.microsoft.com/azure/storage/solution-integration/validated-partners/primary-secondary-storage/partner-overview) - offers validated service-specific alternatives; balance recovery needs against licensing and operational overhead.</li></ul> |

For independent accounts, [Blob Object Replication](#storage-pattern-2), [customer-orchestrated copy](#storage-pattern-3), and [customer-managed replication](#storage-pattern-4) are also DR candidates for supported objects. Choose them using the [replication patterns](#replication-patterns) below, then prove the workload's RPO, RTO, and failback behavior.

<a id="evaluate-native-storage-data-replication-options"></a>

## Replication patterns

<a id="geo-priority-eligibility"></a>

### Pattern 1: Geo-redundant storage {#storage-pattern-1}

- **Deployment:** One eligible account using GRS or GZRS, with an Azure-assigned paired secondary region.
- **Objects:** Blob, ADLS Gen2, Files, Queues, and Tables, subject to account and redundancy eligibility.
- **Distribution:** Azure-managed, asynchronous replication of account data. The destination region is fixed and replication is account-wide.
- **During an outage:** Follow the supported storage-account failover procedure. RA-GRS and RA-GZRS allow secondary reads for supported services before failover, not secondary writes.
- **Best for / watch for:** Simple account-wide protection when the paired destination is acceptable. Validate replication lag, failover eligibility, data-loss exposure, and application recovery separately.

:::image type="content" source="./media/storage-geo-redundancy.svg" alt-text="One logical storage account spans a primary region and an Azure-assigned paired secondary region. Azure asynchronously replicates account data. The primary serves reads and writes; the secondary permits reads only for supported read-access configurations. Account failover and application recovery are separate actions.":::

*Storage - Pattern 1: Azure manages replication within one logical account; the recovery procedure determines when and how applications resume.*

See [Azure Storage redundancy](https://learn.microsoft.com/azure/storage/common/storage-redundancy#geo-redundant-storage) and [failover and failback guidance](https://learn.microsoft.com/azure/storage/common/storage-disaster-recovery-guidance). Evaluate [Geo-Priority Replication](https://docs.azure.cn/en-us/storage/common/storage-redundancy-priority-replication?tabs=portal) where available for a predictable RPO SLA; this reference applies to Azure operated by 21Vianet, so confirm applicability to your cloud.

<a id="priority-replication-eligibility"></a>

### Pattern 2: Blob Object Replication {#storage-pattern-2}

- **Deployment:** One source account and multiple independent destination accounts in customer chosen, supported regions. The destinations can be in different regions.
- **Objects:** Block blobs only; not append blobs, page blobs, hierarchical namespace-enabled accounts, Files, Queues, or Tables.
- **Distribution:** Azure asynchronously copies selected containers or datasets through object replication policies, with one policy per destination account. Enable change feed on the source and blob versioning on all participating accounts.
- **During an outage:** The customer redirects applications to the selected destination and follows the service's procedure to enable writes. Configure and validate reverse replication before failback.
- **Best for / watch for:** Selective replication for resiliency, latency, or regulatory requirements across multiple accounts and regions. Destination accounts already exist, but configuration, endpoint redirection, write enablement, and recovery validation remain customer responsibilities.

:::image type="content" source="./media/storage-object-replication.svg" alt-text="One source storage account in region A asynchronously replicates selected block blobs to multiple independent destination accounts in customer chosen regions, with regions B and C shown as examples. Each destination has its own replication policy and endpoint. The customer selects a recovery destination and manages application redirection, destination write enablement, validation, and failback.":::

*Storage - Pattern 2: one source account replicates selected block blobs to multiple destination accounts, which can be in different regions; the customer owns recovery across independent endpoints.*

See [Object replication for block blobs](https://learn.microsoft.com/azure/storage/blobs/object-replication-overview). For eligible workloads, evaluate [Priority Replication](https://learn.microsoft.com/azure/storage/blobs/object-replication-priority-replication?tabs=portal) for a predictable RPO SLA.

<a id="evaluate-custom-replication"></a>

### Pattern 3: Customer-orchestrated copy {#storage-pattern-3}

- **Deployment:** Separate regional accounts and a scheduled copy process using AzCopy, Azure Data Factory / Synapse, or a supported Storage Mover transfer.
- **Objects:** Blob, ADLS Gen2, and Azure Files datasets, subject to each tool's source, destination, protocol, and metadata support. Storage Mover support described below is specific to Blob and ADLS Gen2 transfers.
- **Distribution:** Initial seeding followed by scheduled or incremental copies. Define change detection, deletion handling, retries, and destination validation.
- **During an outage:** Recover from the last successfully copied and validated data. The customer redirects applications and manages failback.
- **Best for / watch for:** Bulk movement, region expansion, planned relocation, or recovery objectives compatible with the copy schedule. A scheduled copy is not continuous low-RPO replication.

:::image type="content" source="./media/storage-orchestrated-copy.svg" alt-text="AzCopy copies data directly between accounts in two regions using server-to-server APIs. A customer-managed execution host submits and monitors copy jobs without carrying the copied data. Scheduling, credentials, retries, validation, and application recovery remain customer-owned. Other pipeline and mover tools have service-specific execution and data paths.":::

*Storage - Pattern 3: the AzCopy example separates the server-to-server data path from the customer-managed control path.*

#### AzCopy

[AzCopy](https://learn.microsoft.com/azure/storage/common/storage-use-azcopy-v10) is a command-line tool built and maintained by the Azure Storage team. It is a strong fit for petabyte-scale bulk seeding and scheduled incremental copies to customer chosen regions, especially for ADLS Gen2. Account-to-account copies use server-to-server APIs, so data does not pass through the client.

The customer deploys and maintains the execution environment, such as a VM, and owns authentication, scheduling, monitoring, retries, validation, and recovery.

Key characteristics:

- For optimal performance, [keep each copy job below 10 million files](https://learn.microsoft.com/azure/storage/common/storage-use-azcopy-optimize#reduce-the-size-of-each-job). This is a sizing recommendation, not a hard object-count limit.
- Tune concurrent requests with `AZCOPY_CONCURRENCY_VALUE` and benchmark against client resources and storage-account limits; do not assume a universal 3,000-request limit.
- Run jobs across multiple clients or VMs to reach target throughput and IOPS, preferably one AzCopy instance per client.
- Use `--overwrite=ifSourceNewer` for incremental runs and `--preserve-permissions` to carry ACLs where supported and authorized. Incremental copy does not propagate source deletions.
- Retain job plans and logs so failed transfers can be retried with [AzCopy job resume](https://learn.microsoft.com/azure/storage/common/storage-use-azcopy-configure).

Choose an AzCopy execution approach based on scale and resiliency needs. These approaches are variations of Storage - Pattern 3:

| Execution approach | Pros | Cons |
| --- | --- | --- |
| **A - Sequential copy of the entire account** | One command for initial and incremental copy; simplest to operate. | Sequential container creation; one large job can incur substantial tracking overhead. Retain job state to resume failures rather than restarting the entire copy. |
| **B - Container-by-container from a single client** | Smaller jobs; higher total scale; resume from the last successful container on failure. | More scripting to enumerate containers, partition large containers, and handle errors. |
| **C - Parallel containers across multiple clients or VMs** | All of B, plus faster copying through parallel VM instances. | Orchestration across VMs; more complex monitoring; can throttle the source or destination account under load. |

#### Azure Data Factory / Synapse pipelines

Use [Copy activity in Azure Data Factory and Azure Synapse](https://learn.microsoft.com/azure/data-factory/copy-activity-overview) for orchestrated, incremental replication to a chosen region, especially for ADLS Gen2 where object replication is not available. Pipelines support scheduling, monitoring, and data transformation, but add development and operational overhead.

Define how the pipeline detects changed data, handles deletions and failed copies, and validates the destination. The customer owns pipeline configuration, credentials, integration-runtime selection, monitoring, and recovery testing; a successful copy run is not an end-to-end disaster recovery guarantee.

#### Storage Mover

[Storage Mover](https://learn.microsoft.com/azure/storage-mover/service-overview) supports secondary-account seeding, historical data movement, periodic synchronization, planned relocation, and region expansion. Validate the supported Blob or ADLS Gen2 source-to-target combination.

Moves include only the latest version of files. The process is batch-oriented rather than continuous; use it when an RPO measured in hours or days is acceptable, not for low-RPO workloads.

### Pattern 4: Customer-managed service replication {#storage-pattern-4}

- **Deployment:** Separate regional accounts plus customer-operated replication logic, or a validated partner offering.
- **Objects:** The services explicitly supported by the implementation. For Queue and Table scenarios in customer chosen regions, implement replication using service APIs or application logic.
- **Distribution:** Capture changes through an application-owned mechanism and apply them to the destination. Define handling for updates, deletes, ordering, retries, and duplicates; do not assume a built-in change feed.
- **During an outage:** Reconcile the destination, manage producer and consumer cutover, redirect applications, and prevent conflicting writes. Test return to the original region.
- **Best for / watch for:** Requirements not met by native replication or copy tools. The customer owns infrastructure, ongoing operation, consistency, monitoring, and recovery, unless a partner contract explicitly assigns these responsibilities.

:::image type="content" source="./media/storage-customer-replication.svg" alt-text="Application writes in the primary region are captured through an application-owned change log. A customer-operated replication worker reads the log, applies changes through service APIs to a separate destination account, and records checkpoints. The customer defines ordering, deletion handling, retries, duplicate handling, and producer and consumer cutover.":::

*Storage - Pattern 4: an illustrative application-owned change-capture design, not a native Queue or Table replication feature.*

<a id="evaluate-product-specific-replication"></a>
<a id="databricks"></a>

### Pattern 5: Databricks replication and recovery {#storage-pattern-5}

Product-specific replication can preserve application metadata, consistency, and recovery semantics that generic storage replication cannot. Evaluate these options alongside Azure Storage services to reduce custom orchestration and improve end-to-end workload recovery.

For data lake workloads using Databricks, evaluate table-level cloning and managed disaster recovery alongside storage-level replication. Cloning can seed or refresh a secondary dataset, but it does not by itself recover the workspace, permissions, jobs, or application dependencies. Validate deep versus shallow clone behavior, supported table formats, destination support, and refresh procedures before treating a clone as an independent recovery copy.

- [Delta Lake Clone](https://delta.io/blog/delta-lake-clone/)
- [Clone a table on Azure Databricks](https://learn.microsoft.com/azure/databricks/tables/operations/clone)
- [Clone a managed Iceberg table](https://learn.microsoft.com/azure/databricks/iceberg/clone)
- [Incrementally clone Parquet and Apache Iceberg tables to Delta Lake](https://learn.microsoft.com/azure/databricks/ingestion/data-migration/clone-parquet)
- [Managed disaster recovery](https://learn.microsoft.com/azure/databricks/admin/managed-disaster-recovery)

<a id="evaluate-azure-storage-partners"></a>

## Azure Storage partners

When built-in replication, backup, or data-movement services cannot meet your workload requirements, use [Azure Storage solutions from Microsoft partners](https://learn.microsoft.com/azure/storage/solution-integration/) to find validated offerings that extend Azure Storage capabilities.

Evaluate partner solutions against the following criteria:

- **Workload fit:** Confirm support for the required storage services, data formats, account scale, change rate, and destination regions.
- **Recovery objectives:** Validate RPO and RTO during normal operations, regional disruption, and large-scale recovery.
- **HA and DR:** Confirm support for continuous replication, backup recovery, failover, and failback.
- **Security and compliance:** Assess encryption, customer-managed keys, access controls, isolation, residency, and auditing.
- **Operational ownership:** Define deployment, monitoring, incident, validation, failover, and support responsibilities.
- **Cost and scale:** Include licensing, storage, transfer, compute, monitoring, testing, and operations.

Before production adoption, validate the solution through workload-representative performance testing and disaster recovery exercises. Confirm that recovery procedures address application dependencies, endpoint redirection, write enablement, data consistency, and failback, not only data replication.

## Design consideration

### Endpoints and DNS during failover and failback

Plan how each application connects to storage during normal operation, failover, and failback. The endpoint behavior depends on whether recovery uses the same storage account or a separate account.

| Recovery model | Endpoint behavior | What to prepare |
| --- | --- | --- |
| **Geo-redundant account: GRS, GZRS, and read-access variants** | The account's primary service endpoint names stay the same during supported customer-managed or Microsoft-managed account failover. Azure updates DNS to route those endpoints to the new primary region. | Keep using the account's primary endpoint. Test DNS caching, retries, reconnection, and the return to the original region during failback. |
| **Secondary reads: RA-GRS or RA-GZRS** | Read access uses a separate, read-only secondary endpoint. Asynchronous replication means its data can lag behind the primary. | Decide when the application should use secondary reads and what staleness it can tolerate. Do not send writes to the secondary endpoint. |
| **Independent destination account** | The destination has its own account name and service endpoints. Replicating data does not redirect applications. | Define application configuration or DNS-based redirection, where supported. Test cutover to the destination and the reverse process during failback. |

For every model, validate private endpoints, private DNS resolution, network access, and application permissions from the recovery region. An unchanged hostname does not mean uninterrupted access. See [Storage account failover and failback](https://learn.microsoft.com/azure/storage/common/storage-disaster-recovery-guidance) and [customer-managed unplanned failover](https://learn.microsoft.com/azure/storage/common/storage-failover-customer-managed-unplanned).

### Key management and customer-managed keys

When storage uses [customer-managed keys (CMKs)](https://learn.microsoft.com/azure/storage/common/customer-managed-keys-overview), access to protected data depends on Azure Storage being able to use the configured key in Azure Key Vault or Managed HSM. Replication and backup do not automatically create an independently recoverable key-management design.

- **One geo-redundant account:** Primary and secondary replicas share the account's CMK configuration. Plan availability and recovery for the configured key store, including its replication where supported. Storage failover does not trigger key-store failover.
- **Independent accounts:** With Blob Object Replication or copy tools such as Storage Mover, each account has its own encryption configuration and can use a different key and key store. Configure the destination account's managed identity, key permissions, and key versions; copying data does not copy these settings.
- **Backup and restore:** Identify which source-account, backup-vault, and restore-target keys the selected backup service requires. Preserve required key versions and permissions for as long as recovery depends on them, and test a restore during a regional outage.

The storage account and its key vault or Managed HSM can be in different regions; destination keys are not required to be stored in the destination account's region. Choose key placement and recovery independently, subject to each service's support. Storage and key-store recovery are separate dependencies, so recovery credentials, procedures, and key-recovery material must remain accessible without first restoring the protected storage account. See the [Key Vault guidance for Azure Storage CMKs](./key-vault-across-regions.md#azure-storage-grs).

CMKs also provide control over rotation, access, and revocation for security and compliance. Enable the required soft delete and purge protection, document key lifecycle ownership, and avoid disabling or deleting keys still needed by storage or retained backups. These controls do not replace a tested key-availability and recovery plan.

### Cost management

Compare total operating and recovery cost, not just the price of storing a second copy. Include:

- **Storage and protection:** Primary and secondary capacity, versions, snapshots, backup retention, and storage operations.
- **Replication and transfer:** Geo-replication or copy charges, and any applicable cross-region network egress. Check the selected service and data path rather than assuming every transfer is billed the same way.
- **Compute and orchestration:** VMs, Functions, Data Factory pipelines, integration runtimes, monitoring, and retries.
- **Operations and recovery:** Engineering, support, failover and failback exercises, restore and rehydration charges where applicable, and partner licensing or implementation costs.

For large Blob or ADLS Gen2 datasets, estimate both initial seeding and ongoing change volume. Model normal operation, a regional outage, and failback, including the cost of rebuilding replicas. Select the least complex approach that meets the workload's required RTO, RPO, security, and compliance needs, then review actual usage and cost as the workload grows.

## Reference links

- [Azure Storage redundancy](https://learn.microsoft.com/azure/storage/common/storage-redundancy)
- [Object replication for block blobs](https://learn.microsoft.com/azure/storage/blobs/object-replication-overview)
- [Storage disaster recovery and account failover](https://learn.microsoft.com/azure/storage/common/storage-disaster-recovery-guidance)
- [AzCopy performance and job sizing](https://learn.microsoft.com/azure/storage/common/storage-use-azcopy-optimize)
- [Copy activity in Azure Data Factory and Azure Synapse](https://learn.microsoft.com/azure/data-factory/copy-activity-overview)
- [Transfer Azure Files data with AzCopy](https://learn.microsoft.com/azure/storage/common/storage-use-azcopy-files)
- [Azure Files connector for Azure Data Factory and Azure Synapse](https://learn.microsoft.com/azure/data-factory/connector-azure-file-storage)
- [Storage Mover overview](https://learn.microsoft.com/azure/storage-mover/service-overview)
- [Azure Storage partner solutions](https://learn.microsoft.com/azure/storage/solution-integration/)
- [ADLS vaulted backup support matrix](https://learn.microsoft.com/azure/backup/azure-data-lake-storage-backup-support-matrix)

## Next step

> [!div class="nextstepaction"]
> [Backup and restore across regions](./restore-across-regions.md)
