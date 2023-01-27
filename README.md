# Cassandra LWT Migration Tool

### Rationale
This tool was developed to support a migration from one datacenter to another, allowing old hardware to be 
decommissioned afterwards. The issue we ran into is that if we move too much of the topology over mid-LWT,
the new hardware with no data in it could form a quorum for that LWT and return incorrect results. Thus
the concept here is that we add a non-quorum-forming amount of hardware to our DC and use this tool to
verify that all LWTs that started before the topology change have concluded before making another
non-quorum-forming topology change. Eventually the topology will be in its fully migrated state. Then
we rebuild each new host as resources permit and eventually run a full repair to make sure everything
is complete.

As an example, consider a topology where want to get to a replication factor of

    {'class': 'NetworkTopologyStrategy', 'dc_v1': 3, 'dc_v2: 3}

In this situation, our current RF is

    {... 'dc_v1': 3}

So, first we will make a non-quorum forming change to our business-logic keyspaces:

    ALTER KEYSPACE vault_stats WITH REPLICATION = {
        'class' : 'NetworkTopologyStrategy',
        'dc_v2': 1,
        'dc_v1': 3
    };

Now we will run our tool to capture the number of open LWTs in our system.

    $ cassandra_lwt_migration_tool captureBaseline <cassandra_auth> ./cass_ips.txt ./baseline
    ...
    Any errors?: False
    Average run time: 10000ms
    Total outstanding LWTs: 100

We wait a few minutes until...


    $ cassandra_lwt_migration_tool checkCompletion <cassandra_auth> ./cass_ips.txt ./baseline
    ...
    Any errors?: False
    Average run time: 10000ms
    Total outstanding LWTs: 0

All the outstanding LWTs have concluded and we are fine to continue altering our keyspace until
we have 3 replicas in dc_v2. Now that the topology has completely finished, we can rebuild our
new cassandra nodes one by one.

    $ nodetool rebuild cassandrav2-0000
    $ nodetool rebuild cassandrav2-0001
    $ nodetool rebuild cassandrav2-0002

At this point all the data is migrated, and we can drop `dc_v1` out of our keyspace and
turn off or repurpose the old hardware.

### Installation/Setup

#### Install from pip
    pip install -i <index_url> cassandra_lwt_migration_tool
#### Install from source into a virtualenv
    ./create_venv.sh 
This should create a virtualenv and install the tool into it, in editable form. 
#### Install from source to system python
    pip install .
It is worth noting that the tool requires a relatively up-to-date version of
pip to install properly. If you are using a fresh python install, you may need to run something
along the lines of `pip install -U pip` before attempting to install to the system python. It is
highly recommended to install from pip or into a virtualenv, rather than installing directly from
source into the system `site-packages`.

### Usage

#### Command Line
This tool can be run either as a direct script installed by Pip:

        cassandra_lwt_migration_tool captureBaseline \
            --cassandra-username <username> \
            --cassandra-password <password> \
            ./cass_ips.txt \
            ./baseline

Or as an installed python module.

        python -m cassandra_lwt_migration_tool captureBaseline \
            --cassandra-username <username> \
            --cassandra-password <password> \
            ./cass_ips.txt \
            ./baseline

It supports the following run operations:
  - **captureBaseline**
   
    Captures the current set of outstanding LWTs for each node in your specified set of cassandra hosts. The
    tool will refuse to overwrite an existing baseline directory.
  - **checkCompletion**

    Checks the current set of outstanding LWTs, and saves the ones that were outstanding in the baseline set.
    The tool will save the updated set of still-outstanding LWTs to save time on repeated runs.
  - **checkBaselineCompletion**
    
    This is the same as `checkCompletion`, with the caveat that it will ignore any incremental results and
    will only check against the original baseline that was measured.
  - **checkTargetingNodes**
   
    Testing operation to ensure that all the specified cassandra nodes are reachable with the supplied credentials.

The intended flow of usage is to run `captureBaseline` and then run `checkCompletion` against the captured
baseline until the set of still-outstanding LWTs is 0. This ensures that you do not have any LWT writes that 
cross two topology change operations chronologically.

#### Specifying Cassandra Nodes
The `cass_ips.txt` file referenced above is a simple space-delimited set of hostnames and corresponding IPs.
For example, your file might look like the following:

```
cassandra-0000 192.168.100
cassandra-0001 192.168.101
cassandra-0002 192.168.102
```