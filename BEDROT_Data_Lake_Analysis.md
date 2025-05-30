# BEDROT Data Lake - Comprehensive Analysis

*Document Date: 2025-05-30*

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
   - [Data Lake Zones](#data-lake-zones)
   - [Data Flow Visualization](#data-flow-visualization)
3. [Technical Implementation](#technical-implementation)
   - [ETL Pipeline Architecture](#etl-pipeline-architecture)
   - [Extraction Components](#extraction-components)
   - [Transformation Components](#transformation-components)
   - [Loading Components](#loading-components)
4. [Project Organization](#project-organization)
   - [Folder Structure](#folder-structure)
   - [Code Patterns](#code-patterns)
   - [Automation Strategy](#automation-strategy)
5. [Data Sources](#data-sources)
   - [DistroKid](#distrokid)
   - [TooLost](#toolost)
   - [Meta Ads](#meta-ads)
   - [TikTok](#tiktok)
   - [Linktree](#linktree)
6. [Operational Considerations](#operational-considerations)
   - [Monitoring and Logging](#monitoring-and-logging)
   - [Data Validation](#data-validation)
   - [Error Handling](#error-handling)
7. [Future Development Recommendations](#future-development-recommendations)
   - [Technical Debt](#technical-debt)
   - [Enhancement Opportunities](#enhancement-opportunities)
   - [Scaling Considerations](#scaling-considerations)
8. [Appendix](#appendix)
   - [Project Timeline](#project-timeline)
   - [Key Contributors](#key-contributors)

## Executive Summary

The BEDROT Data Lake represents a structured approach to data management for BEDROT Productions, with clearly defined zones for data processing, comprehensive automation, and robust data governance. The system ingests data from multiple sources (DistroKid, TooLost, Meta Ads, TikTok, Linktree) through web scrapers and API integrations, transforms it through a series of cleaner scripts, and provides business-ready datasets for analytics and reporting.

Key strengths of the implementation include:
- Well-defined data zones with clear responsibilities
- Automated ETL processes with scheduled execution
- Strong data lineage and auditability
- Modular code organization by data source
- Robust error handling and validation

The system shows continuous improvement, with recent updates focused on enhancing TikTok analytics extraction, refactoring Meta Ads processing, and improving the overall automation workflow.

## Architecture Overview

### Data Lake Zones

The BEDROT Data Lake follows a multi-zone architecture that enforces data governance and provides a clear path from raw data to business-ready insights:

```mermaid
graph LR
    subgraph External Sources
        DS1[DistroKid]
        DS2[TooLost]
        DS3[Meta Ads]
        DS4[TikTok]
        DS5[Linktree]
    end

    subgraph Data Lake Zones
        L[Landing Zone]
        R[Raw Zone]
        S[Staging Zone]
        C[Curated Zone]
        A[Archive Zone]
    end

    DS1 --> L
    DS2 --> L
    DS3 --> L
    DS4 --> L
    DS5 --> L
    
    L --> R
    R --> S
    S --> C
    L -.-> A
    R -.-> A
    C -.-> A

    classDef external fill:#e8f5e9,stroke:#388e3c
    classDef zones fill:#e3f2fd,stroke:#1976d2
    
    class DS1,DS2,DS3,DS4,DS5 external
    class L,R,S,C,A zones
```

Each zone has a specific purpose in the data lifecycle:

- **Landing Zone**: Initial data ingestion where external data is first collected. This zone is read-only and preserves the original format of the data. Files are often timestamped and never modified after landing.

- **Raw Zone**: Validated source-of-truth zone with immutable, append-only copies of data from the landing zone. No transformations are performed, maintaining full data lineage.

- **Staging Zone**: Where data cleaning, validation, and transformation occur. This is where most of the business logic is applied, joining data sources, and preparing for final consumption.

- **Curated Zone**: Business-ready datasets for analytics, dashboards, and ML. Contains cleaned, aggregated, and enriched data with stable schemas and documentation.

- **Archive Zone**: Long-term storage for datasets no longer actively used, ensuring historical data is preserved for compliance and future analysis.

### Data Flow Visualization

The overall data flow through the system follows a clear path with well-defined processing steps:

```mermaid
flowchart TD
    subgraph External["External Data Sources"]
        TikTok["TikTok API"]
        Spotify["Spotify API"]
        DistroKid["DistroKid"]
        Social["Social Media"]
    end

    subgraph Lake["Data Lake Zones"]
        Landing["Landing Zone"]
        Raw["Raw Zone"]
        Staging["Staging Zone"]
        Curated["Curated Zone"]
        Archive["Archive Zone"]
    end

    subgraph Scripts["ETL Scripts (src/)"]
        Extractors["Extractors"]
        Validators["Validators"]
        Cleaners["Cleaners"]
        Enrichers["Enrichers"]
    end

    subgraph Consumers["Data Consumers"]
        BI["BI Tools"]
        APIs["APIs"]
        DataScience["Data Science"]
        AI["AI/ML Models"]
    end

    subgraph Sandbox["Experimentation"]
        Jupyter["Jupyter Notebooks"]
        Exploration["Data Exploration"]
    end

    External --> |"1. Ingestion"| Landing
    Landing --> |"2. Validation"| Raw
    Raw --> |"3. Clean & Transform"| Staging
    Staging --> |"4. Enrich & Aggregate"| Curated
    
    Landing -.-> |"Retire Older Data"| Archive
    Raw -.-> |"Retire Older Data"| Archive

    Scripts --> |"Automation"| Lake
    
    Curated --> Consumers
    Raw --> Sandbox
    Sandbox --> |"Promote"| Staging

    classDef external fill:#e8f5e9,stroke:#388e3c
    classDef lake fill:#e3f2fd,stroke:#1976d2
    classDef scripts fill:#e1f5fe,stroke:#0288d1
    classDef consumers fill:#fff3e0,stroke:#f57c00
    classDef sandbox fill:#fff9c4,stroke:#fbc02d
    
    class External external
    class Lake lake
    class Scripts scripts
    class Consumers consumers
    class Sandbox sandbox
```

## Technical Implementation

### ETL Pipeline Architecture

The ETL pipeline follows a modular architecture organized by data source, with clear separation between extraction, transformation, and loading components:

```mermaid
graph TD
    subgraph Extraction
        DE1[DistroKid Extractor]
        DE2[TooLost Extractor]
        DE3[Meta Ads Extractor]
        DE4[TikTok Extractor]
        DE5[Linktree Extractor]
    end

    subgraph Validation
        DV1[Landing-to-Raw Validators]
    end

    subgraph Transformation
        DT1[Raw-to-Staging Cleaners]
        DT2[Data Normalization]
        DT3[Joining/Aggregation]
    end

    subgraph Loading
        DL1[Staging-to-Curated Promotion]
        DL2[Archiving Process]
    end

    subgraph Automation
        Cron[Cron Job Scheduler]
    end

    Extraction --> Validation
    Validation --> Transformation
    Transformation --> Loading
    Automation --> Extraction
    Automation --> Validation
    Automation --> Transformation
    Automation --> Loading

    classDef extract fill:#e1bee7,stroke:#8e24aa
    classDef validate fill:#bbdefb,stroke:#1976d2
    classDef transform fill:#c8e6c9,stroke:#388e3c
    classDef load fill:#ffccbc,stroke:#e64a19
    classDef auto fill:#d1c4e9,stroke:#512da8
    
    class DE1,DE2,DE3,DE4,DE5 extract
    class DV1 validate
    class DT1,DT2,DT3 transform
    class DL1,DL2 load
    class Cron auto
```

### Extraction Components

Extraction scripts are primarily implemented using Playwright for web scraping, with specialized modules for each data source:

```mermaid
classDiagram
    class BaseExtractor {
        +extract_data()
        +validate_credentials()
        +handle_authentication()
    }
    
    class PlaywrightExtractor {
        -browser_context
        -session_dir
        +launch_browser()
        +handle_login()
        +navigate_to_data()
        +download_data()
    }
    
    class DistroKidExtractor {
        -stream_stats_url
        -apple_music_url
        +extract_stream_stats()
        +extract_apple_music_stats()
        +extract_bank_details()
    }
    
    class TikTokExtractor {
        -analytics_url
        -account_profile
        +load_cookies()
        +navigate_to_analytics()
        +set_date_range()
        +download_csv()
    }
    
    class MetaAdsExtractor {
        -api_credentials
        +extract_campaigns()
        +extract_adsets()
        +extract_ads()
        +extract_insights()
    }
    
    BaseExtractor <|-- PlaywrightExtractor
    PlaywrightExtractor <|-- DistroKidExtractor
    PlaywrightExtractor <|-- TikTokExtractor
    BaseExtractor <|-- MetaAdsExtractor
```

### Transformation Components

The transformation pipeline follows a consistent pattern across data sources with three main stages:

```mermaid
graph LR
    subgraph Landing-to-Raw["Landing to Raw"]
        L2R1[Validation]
        L2R2[Structure Check]
        L2R3[Copy to Raw]
    end

    subgraph Raw-to-Staging["Raw to Staging"]
        R2S1[Parse & Clean]
        R2S2[Type Conversion]
        R2S3[Deduplication]
        R2S4[Missing Value Handling]
    end

    subgraph Staging-to-Curated["Staging to Curated"]
        S2C1[Business Logic]
        S2C2[Aggregation]
        S2C3[Enrichment]
        S2C4[Archiving]
    end

    Landing-to-Raw --> Raw-to-Staging
    Raw-to-Staging --> Staging-to-Curated

    classDef l2r fill:#bbdefb,stroke:#1976d2
    classDef r2s fill:#c8e6c9,stroke:#388e3c
    classDef s2c fill:#ffccbc,stroke:#e64a19
    
    class L2R1,L2R2,L2R3 l2r
    class R2S1,R2S2,R2S3,R2S4 r2s
    class S2C1,S2C2,S2C3,S2C4 s2c
```

Each data source implements these transformations with specialized cleaner scripts that follow a consistent pattern but address source-specific requirements.

## Project Organization

### Folder Structure

The project follows a well-organized folder structure that separates concerns and enforces data governance:

```mermaid
graph TD
    Root["BEDROT_DATA_LAKE/"] --> Agent[".agent/"]
    Root --> Archive["archive/"]
    Root --> Changelog["changelog.md"]
    Root --> Cronjob["cronjob/"]
    Root --> Curated["curated/"]
    Root --> DataFlow["data_lake_flow.dot"]
    Root --> Docker["docker-compose.yml"]
    Root --> Images["image.png, image.svg"]
    Root --> Knowledge["knowledge/"]
    Root --> Landing["landing/"]
    Root --> MinIO["minio/"]
    Root --> Raw["raw/"]
    Root --> Requirements["requirements.txt"]
    Root --> Sandbox["sandbox/"]
    Root --> Src["src/"]
    Root --> Staging["staging/"]
    
    Src --> SrcDK["distrokid/"]
    Src --> SrcLT["linktree/"]
    Src --> SrcMA["metaads/"]
    Src --> SrcTK["tiktok/"]
    Src --> SrcTL["toolost/"]
    
    SrcDK --> SrcDKE["extractors/"]
    SrcDK --> SrcDKC["cleaners/"]
    
    SrcMA --> SrcMAE["extractors/"]
    SrcMA --> SrcMAC["cleaners/"]
    
    Cronjob --> CronBat["run_datalake_cron.bat"]
    Cronjob --> CronNoEx["run_datalake_cron_no_extractors.bat"]
    Cronjob --> CronGen["generate_no_extractors_cron.py"]
    
    classDef zones fill:#e3f2fd,stroke:#1976d2
    classDef code fill:#e1f5fe,stroke:#0288d1
    classDef docs fill:#f3e5f5,stroke:#8e24aa
    classDef config fill:#fff3e0,stroke:#f57c00
    
    class Archive,Landing,Raw,Staging,Curated zones
    class Src,SrcDK,SrcLT,SrcMA,SrcTK,SrcTL,SrcDKE,SrcDKC,SrcMAE,SrcMAC code
    class Changelog,DataFlow,Images,Knowledge docs
    class Cronjob,CronBat,CronNoEx,CronGen,Docker,Requirements,Agent config
```

### Code Patterns

The codebase follows several consistent patterns:

```mermaid
classDiagram
    class DataProcessor {
        +process()
    }
    
    class Extractor {
        +extract()
        +validate()
    }
    
    class Cleaner {
        +load_data()
        +clean()
        +transform()
        +save()
        +archive_if_changed()
    }
    
    class Pipeline {
        +run()
        +log_progress()
        +handle_errors()
    }
    
    DataProcessor <|-- Extractor
    DataProcessor <|-- Cleaner
    Pipeline o-- Extractor
    Pipeline o-- Cleaner
```

Key patterns include:
1. **Modular Organization**: Code is organized by data source and processing stage
2. **Clear Separation of Concerns**: Extractors, validators, and cleaners have distinct responsibilities
3. **Consistent File Naming**: Files follow a predictable naming pattern like `{source}_{stage}.py`
4. **Path Abstraction**: All scripts use environment variables for paths to avoid hardcoding
5. **Idempotent Processing**: Scripts can be run multiple times without side effects
6. **Archiving Before Changes**: All curated data is archived before being replaced
7. **Hashing for Change Detection**: File hashes are used to detect changes and avoid unnecessary updates

### Automation Strategy

The automation strategy centers around Windows Task Scheduler and batch files:

```mermaid
graph TD
    Task["Windows Task Scheduler"] --> Master["run_datalake_cron.bat"]
    Task --> NoExtract["run_datalake_cron_no_extractors.bat"]
    
    Master --> Extractors["Run All Extractors"]
    Master --> Cleaners["Run All Cleaners"]
    Master --> Generator["Generate No-Extractors Version"]
    
    NoExtract --> Cleaners
    
    Generator --> NoExtract
    
    classDef scheduler fill:#d1c4e9,stroke:#512da8
    classDef batch fill:#fff3e0,stroke:#f57c00
    classDef process fill:#c8e6c9,stroke:#388e3c
    
    class Task scheduler
    class Master,NoExtract batch
    class Extractors,Cleaners,Generator process
```

The automation approach is:
1. **Centralized Maintenance**: Only the master cron job file is manually edited
2. **Automatic Generation**: Secondary variants are generated automatically
3. **Modular Processing**: The system automatically discovers and runs all extractors and cleaners
4. **Error Handling**: Any script failure stops the batch to prevent corrupted data
5. **Regular Scheduling**: Jobs run on Monday, Wednesday, and Friday

## Data Sources

### DistroKid

DistroKid data is extracted using Playwright-based web scraping that navigates to the dashboard, extracts streaming data and bank details, and processes them through the ETL pipeline:

```mermaid
graph LR
    Login[Login Script] --> Dashboard[Dashboard Navigation]
    Dashboard --> StreamStats[Stream Stats Extraction]
    Dashboard --> AppleMusic[Apple Music Stats Extraction]
    Dashboard --> BankDetails[Bank Details Download]
    
    StreamStats --> HTMLFiles[HTML Files in Landing]
    AppleMusic --> HTMLFiles
    BankDetails --> TSVFiles[TSV Files in Landing]
    
    HTMLFiles --> Validation[Landing-to-Raw Validation]
    TSVFiles --> Validation
    
    Validation --> Parsing[Raw-to-Staging Parsing & Cleaning]
    Parsing --> StagingCSV[CSVs in Staging Zone]
    
    StagingCSV --> BusinessLogic[Staging-to-Curated Business Logic]
    BusinessLogic --> CuratedCSV[CSVs in Curated Zone]
    
    classDef extract fill:#e1bee7,stroke:#8e24aa
    classDef files fill:#bbdefb,stroke:#1976d2
    classDef process fill:#c8e6c9,stroke:#388e3c
    classDef final fill:#ffccbc,stroke:#e64a19
    
    class Login,Dashboard,StreamStats,AppleMusic,BankDetails extract
    class HTMLFiles,TSVFiles files
    class Validation,Parsing,StagingCSV process
    class BusinessLogic,CuratedCSV final
```

### TikTok

TikTok analytics are extracted using account-specific Playwright automation:

```mermaid
graph TD
    TikTok[TikTok Analytics Extractor] --> Profiles[Account-Specific Browser Profiles]
    Profiles --> ZoneA0[ZONE A0 Profile]
    Profiles --> PIG1987[PIG1987 Profile]
    
    ZoneA0 --> Login1[Manual Login with Cookies]
    PIG1987 --> Login2[Manual Login with Cookies]
    
    Login1 --> Analytics1[Navigate to Analytics]
    Login2 --> Analytics2[Navigate to Analytics]
    
    Analytics1 --> DateRange1[Set Date Range to 365 Days]
    Analytics2 --> DateRange2[Set Date Range to 365 Days]
    
    DateRange1 --> Download1[Download CSV]
    DateRange2 --> Download2[Download CSV]
    
    Download1 --> Landing1[CSV in Landing Zone]
    Download2 --> Landing2[CSV in Landing Zone]
    
    classDef extractor fill:#e1bee7,stroke:#8e24aa
    classDef browser fill:#bbdefb,stroke:#1976d2
    classDef process fill:#c8e6c9,stroke:#388e3c
    classDef output fill:#ffccbc,stroke:#e64a19
    
    class TikTok,Profiles extractor
    class ZoneA0,PIG1987,Login1,Login2 browser
    class Analytics1,Analytics2,DateRange1,DateRange2,Download1,Download2 process
    class Landing1,Landing2 output
```

### Meta Ads

Meta Ads data is extracted from the Facebook Marketing API and processed through the pipeline:

```mermaid
graph TD
    Meta[Meta Ads Extractor] --> Campaigns[Extract Campaigns]
    Meta --> AdSets[Extract Ad Sets]
    Meta --> Ads[Extract Ads]
    Meta --> Insights[Extract Insights]
    
    Campaigns --> JSON1[campaigns.json in Landing]
    AdSets --> JSON2[adsets.json in Landing]
    Ads --> JSON3[ads.json in Landing]
    Insights --> JSON4[insights.json in Landing]
    
    JSON1 --> Validation[Landing-to-Raw Validation]
    JSON2 --> Validation
    JSON3 --> Validation
    JSON4 --> Validation
    
    Validation --> Raw[Validated JSONs in Raw Zone]
    
    Raw --> Cleaning[Cleaning & Transformation]
    Cleaning --> Metrics[Numeric Metrics Conversion]
    Metrics --> Deduplication[Deduplication]
    
    Deduplication --> Staging[tidy_metaads.csv in Staging]
    
    Staging --> Promotion[Staging-to-Curated Promotion]
    Promotion --> Curated[metaads_campaigns_daily.csv in Curated]
    
    classDef extract fill:#e1bee7,stroke:#8e24aa
    classDef files fill:#bbdefb,stroke:#1976d2
    classDef process fill:#c8e6c9,stroke:#388e3c
    classDef final fill:#ffccbc,stroke:#e64a19
    
    class Meta,Campaigns,AdSets,Ads,Insights extract
    class JSON1,JSON2,JSON3,JSON4,Raw files
    class Validation,Cleaning,Metrics,Deduplication,Staging process
    class Promotion,Curated final
```

## Operational Considerations

### Monitoring and Logging

The system implements comprehensive logging with:

```mermaid
graph TD
    subgraph Logging
        Console[Console Logging]
        Files[File Logging]
        Status[Status Messages]
    end
    
    subgraph Events
        Extraction[Extraction Events]
        Validation[Validation Events]
        Transformation[Transformation Events]
        Loading[Loading Events]
        Errors[Error Events]
    end
    
    Events --> Logging
    
    classDef logging fill:#bbdefb,stroke:#1976d2
    classDef events fill:#c8e6c9,stroke:#388e3c
    
    class Console,Files,Status logging
    class Extraction,Validation,Transformation,Loading,Errors events
```

### Data Validation

The data validation approach includes:

```mermaid
graph TD
    Input[Input Data] --> StructureCheck[Structure Validation]
    Input --> SchemaCheck[Schema Validation]
    Input --> ContentCheck[Content Validation]
    
    StructureCheck --> Pass[Promotion to Next Zone]
    SchemaCheck --> Pass
    ContentCheck --> Pass
    
    StructureCheck --> Fail[Rejection]
    SchemaCheck --> Fail
    ContentCheck --> Fail
    
    classDef input fill:#e1bee7,stroke:#8e24aa
    classDef validation fill:#bbdefb,stroke:#1976d2
    classDef output fill:#c8e6c9,stroke:#388e3c
    
    class Input input
    class StructureCheck,SchemaCheck,ContentCheck validation
    class Pass,Fail output
```

## Future Development Recommendations

### Technical Debt

Areas requiring attention:

```mermaid
graph TD
    subgraph Technical Debt
        TD1[Jupyter Notebooks to Scripts]
        TD2[Error Handling Standardization]
        TD3[Testing Coverage]
        TD4[Documentation Gaps]
    end
    
    classDef debt fill:#ffcdd2,stroke:#d32f2f
    class TD1,TD2,TD3,TD4 debt
```

### Enhancement Opportunities

```mermaid
graph TD
    subgraph Enhancements
        E1[Centralized Logging]
        E2[Pipeline Visualization Dashboard]
        E3[Data Quality Metrics]
        E4[Automated Testing]
        E5[Data Dictionary Maintenance]
    end
    
    classDef enhance fill:#c8e6c9,stroke:#388e3c
    class E1,E2,E3,E4,E5 enhance
```

### Scaling Considerations

```mermaid
graph TD
    subgraph Scaling
        S1[Container Orchestration]
        S2[Cloud Storage Integration]
        S3[Parallel Processing]
        S4[Data Partitioning]
        S5[Incremental Processing]
    end
    
    classDef scale fill:#bbdefb,stroke:#1976d2
    class S1,S2,S3,S4,S5 scale
```

## Appendix

### Project Timeline

Key milestones from the changelog:

```mermaid
timeline
    title BEDROT Data Lake Development Timeline
    
    section 2025 May
        22 : DistroKid Extractor : TooLost Extractor
        23 : TooLost Validation
        26 : Meta Ads Ingest : Dataset Cleaners Pipeline : Cron Automation
        27 : Meta Ads Folder Naming : Meta Ads Curated Promotion : Linktree Analytics
        28 : TikTok Extractor Rollout : TikTok PIG1987 Profile : Meta Ads Landing Refactor
        29 : Staging-to-Curated Refactor
```

### Key Contributors

The project shows evidence of collaboration across multiple roles:

```mermaid
graph TD
    subgraph Roles
        Architects[Data Architects]
        Engineers[Data Engineers]
        Analysts[Data Analysts]
        Scientists[Data Scientists]
    end
    
    subgraph Responsibilities
        Architecture[Lake Architecture]
        Extraction[Data Extraction]
        Transformation[Data Transformation]
        Loading[Data Loading]
        Analytics[Analytics & Reporting]
    end
    
    Architects --> Architecture
    Engineers --> Extraction
    Engineers --> Transformation
    Engineers --> Loading
    Analysts --> Analytics
    Scientists --> Analytics
    
    classDef roles fill:#e1bee7,stroke:#8e24aa
    classDef resp fill:#c8e6c9,stroke:#388e3c
    
    class Architects,Engineers,Analysts,Scientists roles
    class Architecture,Extraction,Transformation,Loading,Analytics resp
```

---

*This document was generated on 2025-05-30 by CASCADE for BEDROT Productions.*
