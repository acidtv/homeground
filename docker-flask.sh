#!/bin/bash

set -e

#docker-compose exec app pipenv run flask $@
docker-compose exec app flask $@
