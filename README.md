# Chowda

CLAMS processing app

## Overview

### Basic Pipeline with 2 CLAMS Apps

Actors:

- **User**
- **Chowda**
  - Webapp
  - Pulbicly available on internet
- **DB**
  - Postgresql
  - VPC
  - Sperate Cluster?
- **Runner**
  - Pipeline Runner
  - In CLAMS cluster
- **CLAMS**
  - Individual CLAMS apps
  - In CLAMS cluster
  - Deployed as either:
    - Webservice
    - Kubernetes Job

### Call Sequence Diagram

- **User** starts job
- **Chowda** enters it in the **DB**
- **Runner** sees new job and starts **CLAM1** with initial MMIF
- **CLAM1** Processes data and returns MMIF to **Runner**
- **Runner** Updates **DB** and starts **CLAM2**
- **CLAM2** Processes data and returns MMIF to **Runner**
- **Runner** Updates **DB**
- **User** gets data from **Chowda**

```mermaid
sequenceDiagram
    actor User
    participant Chowda
    participant DB
    participant Runner
    participant CLAM1
    participant CLAM2

    activate User

    %% User starts job
    note left of User: Hey, Chowda! Start batch 123 on pipeline 456
    User ->> + Chowda: Start batch 123 with files [] through pipeline 456
    Chowda ->> + DB: INSERT (batch, pipeline, Initial mmif) to TABLE pipeline_runs
    DB ->> - Chowda: {pipeline_run_id, status: waiting}
    Chowda ->> - User: Pipeline run {id} is {status}
    deactivate User
    loop backgroud process
        Runner ->> DB: Check for new jobs
    end

    %% Runner
    activate Runner
    note left of Runner: Found new job!
    Runner ->> + CLAM1: Start app 1, with initial MMIF
    deactivate Runner

    %% CLAM1
    note right of CLAM1: Processing!
    loop Status check
        Runner ->> CLAM1: Status report!
        CLAM1 ->> Runner: XX %
        Runner ->> DB: UPDATE pipeline_run_id SET status CLAM1 XX %
    end
    CLAM1 ->> - Runner: Finished! -> MMIF
    activate Runner
    Runner ->> DB: UPDATE pipeline_run_id SET status 'done' + MMIF

    %% CLAM 2
    Runner ->> + CLAM2: Start app 2 with intermediate MMIF
    deactivate Runner
    note right of CLAM2: Processing!
    loop Status check
        Runner ->> CLAM2: Status report!
        CLAM2 ->> Runner: XX %
        Runner ->> DB: UPDATE pipeline_run_id SET status CLAM2 XX %
    end

    %% User update
    activate User
    note left of User: Is it done yet?
    User ->> + Chowda: Pipeline update?
    Chowda ->> + DB: WATCH pipeline_runs WHERE status=running
    DB ->> Chowda: ACTIVE_PIPELINE_RUNS
    Chowda -->> User: Websocket: Batch 123 status [CLAM1: done, CLAM2: XX %]
    note left of User: Not quite, but it should be done soon.

    %% CLAMS finished
    CLAM2 -->> - Runner: Finished! -> MMIF
    activate Runner
    Runner ->> - DB: UPDATE pipeline_run_id SET status MMIF
    DB ->> Chowda: Batch 123 update
    Chowda -->> User: WS: batch 123 Finished!
    deactivate Chowda
    deactivate DB

    note left of User: Yay! My metadata is perfect!
    deactivate User

```
