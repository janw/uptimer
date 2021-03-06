## 0.2.1 (2021-01-16)

### Refactor

- **stdout**: format as indented JSON
- **probes.http**: split off target_list logic into method
- **tests**: add fixture to override config variables
- **probes.http**: split off tls_verify logic into method
- **probes.http**: use requests error messages in event
- **events**: remove unused dummy mode

### Fix

- **probes.http**: avoid passing native re.Pattern to event
- **probes.http**: make urls argparsing more robust
- **mixins**: make distr. worker argument parsing more robust
- **events.formats**: wrong return in is_uuid on non-str formats

## 0.2.0 (2021-01-15)

### Refactor

- improve installation and quick start instructions
- **postgres**: remove separated database config params

### Feat

- **probes.http**: add support for regex matching on responses
- add database migrations mgmt and schema
- **probes.http**: add support for distributed workers

### Fix

- **probes.http**: improve url parsing

## 0.1.1 (2021-01-14)

### Fix

- **docker**: ensure images are semantically versioned

## 0.1.0 (2021-01-14)

### Fix

- **probes.http**: ensure probe_interval=-1 for one-off run works

### Feat

- add Dockerfile
- **postgres**: add postgres writer
- **kafka**: add kafka reader and writer plugins
- add application scaffolding, initial commit
