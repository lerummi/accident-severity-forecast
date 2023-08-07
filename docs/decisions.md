# Decisions for structure and tooling

## Dagster for orchestration

- Asset-based approach including partitions more suitable for the use case of yearly-partitioned dataset, that
  needs to be splitted and merged by downstream assets
- Seamless papermill integration allows to directly transfer upstream and downstream assets to and from the
  notebook

## Decomposition into scenarios using docker-compose profiles

- The complete use-case requires a total number of 13 permanently running docker containers, which requires a
  lot of system resources, especially cpu. By splitting into profiles, the number of containers can be reduced.
- Easier for the user to understand the system and the interacting components

## Minio instead of localstack

- [localstack](https://localstack.cloud/) moved S3 _Persistance_ capability to the paid version, however, since this project deals with
  different process steps running inside individual _docker-compose profiles_, persistance is required. Try to establish
  persistance using [localstack pod](https://github.com/localstack/localstack/issues/6281) was not successful
- Minio provides the same capabilities for mocking S3 like localstack, so for testing locally
